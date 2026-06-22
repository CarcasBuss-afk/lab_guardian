"""Lab Guardian - Agente PC.

Supervisore eseguito come servizio Windows (SYSTEM). Configura il proxy di
sistema, le regole firewall e le policy dei browser, poi avvia il proxy di
filtraggio (mitmproxy in-process) e si sincronizza con Firebase.

Uso:
    lab-agent.exe              avvia l'agente (modalità servizio)
    lab-agent.exe --cleanup    ripristina lo stato originale (disinstallazione)
"""

import asyncio
import json
import logging
import os
import socket
import sys
import threading
import time

import system_proxy
import firewall
import browser_policy
from firebase_client import FirebaseAgent
from proxy_filter import FilterState, LabFilter

log = logging.getLogger("labguardian")


def app_dir():
    """Cartella dell'eseguibile (o dello script in sviluppo)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = app_dir()
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
BACKUP_PATH = os.path.join(BASE_DIR, "proxy_backup.json")
LOG_PATH = os.path.join(BASE_DIR, "agent.log")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8")],
    )


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_upstream(server):
    """Estrae host:port da una stringa proxy di Windows."""
    if not server:
        return None
    # Formato "http=host:port;https=host:port" oppure "host:port"
    if "=" in server:
        parts = dict(p.split("=", 1) for p in server.split(";") if "=" in p)
        server = parts.get("https") or parts.get("http") or ""
    server = server.strip()
    return server or None


def network_probe_loop(state, stop_event):
    """Verifica periodicamente la connettività generale (per il fail-open)."""
    while not stop_event.is_set():
        ok = False
        try:
            with socket.create_connection(("1.1.1.1", 53), timeout=3):
                ok = True
        except OSError:
            ok = False
        state.set_network_ok(ok)
        stop_event.wait(15)


def reapply_proxy_loop(address, stop_event):
    """Riapplica le impostazioni proxy per neutralizzare le manomissioni."""
    while not stop_event.is_set():
        system_proxy.reapply_filter_proxy(address)
        stop_event.wait(10)


async def run_proxy(state, listen_port, upstream):
    """Avvia mitmproxy in-process con l'addon di filtraggio."""
    from mitmproxy.options import Options
    from mitmproxy.tools.dump import DumpMaster

    opts = Options(listen_host="127.0.0.1", listen_port=listen_port)
    master = DumpMaster(opts, with_termlog=False, with_dumper=False)
    if upstream:
        master.options.update(mode=[f"upstream:http://{upstream}"])
    else:
        master.options.update(mode=["regular"])
    master.addons.add(LabFilter(state))
    log.info("Proxy in ascolto su 127.0.0.1:%s (upstream=%s)", listen_port, upstream)
    await master.run()


def cleanup(config):
    """Ripristina lo stato originale del sistema (disinstallazione)."""
    log.info("Avvio cleanup")
    # Segna il PC offline su Firebase (best effort)
    try:
        agent = FirebaseAgent(
            config["apiKey"], config["databaseURL"], config["room"],
            config["agentEmail"], config["agentPassword"],
            socket.gethostname(), on_update=lambda _: None,
        )
        agent.authenticate()
        agent.set_offline()
    except Exception as e:  # noqa: BLE001 - best effort
        log.warning("Impossibile segnare offline: %s", e)

    system_proxy.restore_original_proxy(BACKUP_PATH)
    firewall.remove_quic_block()
    browser_policy.remove_policies()
    log.info("Cleanup completato")


def run():
    config = load_config()
    hostname = socket.gethostname()
    address = config.get("proxyAddress", "127.0.0.1:8080")
    listen_port = int(address.split(":")[-1])

    # 1. Rileva e salva il proxy esistente (eventuale proxy scolastico upstream)
    system_proxy.backup_original_proxy(BACKUP_PATH)
    upstream = normalize_upstream(system_proxy.detect_school_proxy(address))
    if upstream:
        log.info("Rilevato proxy scolastico upstream: %s", upstream)

    # 2. Applica proxy di sistema, firewall (QUIC) e policy browser
    system_proxy.enable_filter_proxy(address)
    firewall.block_quic()
    browser_policy.apply_policies()

    # 3. Stato condiviso e sincronizzazione con Firebase
    state = FilterState(hostname)
    fb = FirebaseAgent(
        config["apiKey"], config["databaseURL"], config["room"],
        config["agentEmail"], config["agentPassword"], hostname,
        on_update=state.update_from_lab,
        heartbeat_seconds=config.get("heartbeatSeconds", 30),
    )
    try:
        fb.authenticate()
    except Exception as e:  # noqa: BLE001
        log.error("Autenticazione Firebase fallita: %s", e)
    fb.start()

    # 4. Thread di supporto: probe di rete e riapplicazione proxy
    stop_event = threading.Event()
    threading.Thread(target=network_probe_loop, args=(state, stop_event), daemon=True).start()
    threading.Thread(target=reapply_proxy_loop, args=(address, stop_event), daemon=True).start()

    # 5. Proxy di filtraggio (blocca finché il servizio è attivo)
    try:
        asyncio.run(run_proxy(state, listen_port, upstream))
    finally:
        stop_event.set()
        fb.stop()


def main():
    setup_logging()
    try:
        config = load_config()
    except (OSError, ValueError) as e:
        log.error("Config non leggibile (%s): %s", CONFIG_PATH, e)
        return 1

    if "--cleanup" in sys.argv:
        cleanup(config)
        return 0

    # Riavvio automatico in caso di errore non gestito (watchdog interno;
    # NSSM riavvia comunque il processo se termina del tutto).
    while True:
        try:
            run()
            break
        except Exception as e:  # noqa: BLE001
            log.exception("Errore non gestito, riavvio tra 5s: %s", e)
            time.sleep(5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
