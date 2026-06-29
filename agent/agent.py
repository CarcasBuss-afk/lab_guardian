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
import browser_control
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
    try:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    except OSError:
        # Se il log e' inaccessibile (file bloccato da un processo in chiusura o
        # permessi) NON dobbiamo bloccare l'avvio: e' fondamentale soprattutto
        # per --cleanup, che deve poter ripristinare il sistema comunque.
        handler = logging.NullHandler()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler],
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


def reapply_proxy_loop(address, stop_event):
    """Riapplica le impostazioni proxy per neutralizzare le manomissioni."""
    while not stop_event.is_set():
        system_proxy.reapply_filter_proxy(address)
        stop_event.wait(10)


def lockdown_watchdog(fb, watcher, stop_event, grace_seconds=150):
    """Rete di sicurezza anti-blocco.

    Se il muro del firewall e' alzato ma l'agente non riesce a sincronizzarsi
    con Firebase (ne' via streaming ne' via riconciliazione) per piu' di
    'grace_seconds', sta "volando alla cieca": abbassa il muro, cosi' un PC non
    puo' mai restare bloccato in modo irreversibile. Il filtraggio per dominio
    resta comunque garantito dal proxy locale (modalita' degradata, finche' non
    si riattiva esplicitamente il blocco).

    Si basa sull'ULTIMA sincronizzazione riuscita (non sul semplice "sono
    connesso"): cosi' intercetta anche lo stream "zombie" — connesso ma che non
    consegna piu' eventi — che e' proprio il caso che aveva tenuto un PC bloccato
    a token scaduto. Finche' la riconciliazione periodica funziona,
    'seconds_since_sync' resta basso e il muro legittimamente attivo non viene
    mai abbassato per errore.
    """
    while not stop_event.is_set():
        stop_event.wait(15)
        if stop_event.is_set():
            break
        if watcher.lockdown_raised and fb.seconds_since_sync >= grace_seconds:
            log.warning(
                "Nessuna sincronizzazione da >%ds con lockdown attivo: abbasso il "
                "muro (filtra solo il proxy finche' non si riattiva il blocco)",
                grace_seconds,
            )
            firewall.disable_lockdown()
            watcher.lockdown_raised = False
            # Evita la ri-attivazione automatica (e quindi l'oscillazione):
            # servira' una nuova transizione esplicita off->on per riprovare.
            watcher._prev_restrictive = True


class ConfigWatcher:
    """Aggiorna lo stato e reagisce alle transizioni del blocco.

    Quando il PC passa a "restrittivo" (filtro aula attivo o PC su "Bloccato"):
    - alza l'egress-lockdown del firewall (default-deny in uscita);
    - alla transizione non-bloccato -> bloccato chiude i browser e pulisce la
      cache (NON sulle modifiche di whitelist/blacklist, e non al primo avvio).

    Quando torna "non restrittivo" abbassa il lockdown e il PC torna normale.
    """

    def __init__(self, state, enforce_enabled, agent_program=None):
        self.state = state
        self.enforce_enabled = enforce_enabled
        self.agent_program = agent_program
        self._prev_restrictive = None
        # True quando il muro del firewall e' effettivamente alzato (serve al
        # watchdog anti-blocco per sapere quando intervenire).
        self.lockdown_raised = False

    @staticmethod
    def _is_restrictive(snap):
        # Il PC filtra/blocca davvero quando:
        if snap["override"] == "blocked":
            return True
        if snap["override"] == "free":
            return False
        return snap["active"]  # override "inherit": dipende dal filtro aula

    def on_update(self, lab):
        self.state.update_from_lab(lab)
        restrictive = self._is_restrictive(self.state.snapshot())

        # Reagisce solo quando lo stato restrittivo cambia (incluso il primo
        # update all'avvio, dove _prev_restrictive vale None).
        if self.enforce_enabled and restrictive != self._prev_restrictive:
            if restrictive:
                self.lockdown_raised = firewall.enable_lockdown(self.agent_program)
                # Chiusura browser + pulizia cache solo su ATTIVAZIONE reale
                # (non al primo avvio del servizio col blocco gia' attivo).
                if self._prev_restrictive is False:
                    log.info("Blocco attivato: avvio chiusura browser e pulizia cache")
                    threading.Thread(target=browser_control.enforce_clean, daemon=True).start()
            else:
                firewall.disable_lockdown()
                self.lockdown_raised = False

        self._prev_restrictive = restrictive


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

    # Ogni ripristino in modo indipendente: se uno fallisce, gli altri devono
    # comunque eseguire (es. il proxy deve tornare normale anche se il firewall
    # da' errore, e viceversa).
    steps = (
        ("ripristino proxy", lambda: system_proxy.restore_original_proxy(BACKUP_PATH)),
        ("rimozione regola QUIC", firewall.remove_quic_block),
        ("disattivazione lockdown", firewall.disable_lockdown),
        ("rimozione policy browser", browser_policy.remove_policies),
    )
    for desc, fn in steps:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - il cleanup deve proseguire
            log.warning("Cleanup: %s fallito: %s", desc, e)
    log.info("Cleanup completato")


def run(apply_system=True):
    config = load_config()
    hostname = socket.gethostname()
    address = config.get("proxyAddress", "127.0.0.1:8080")
    listen_port = int(address.split(":")[-1])

    upstream = None
    if apply_system:
        # 1. Rileva e salva il proxy esistente (eventuale proxy scolastico upstream)
        system_proxy.backup_original_proxy(BACKUP_PATH)
        upstream = normalize_upstream(system_proxy.detect_school_proxy(address))
        if upstream:
            log.info("Rilevato proxy scolastico upstream: %s", upstream)

        # 2. Applica proxy di sistema, firewall (QUIC) e policy browser
        system_proxy.enable_filter_proxy(address)
        firewall.block_quic()
        browser_policy.apply_policies()
    else:
        # Modalità test: nessuna modifica al sistema. Imposta il proxy del
        # browser a mano su 127.0.0.1:8080 per provare il filtraggio.
        log.info("MODALITA' TEST: nessuna modifica al sistema")

    # 3. Stato condiviso e sincronizzazione con Firebase.
    #    Il watcher chiude i browser quando il blocco viene attivato (solo in
    #    installazione reale, mai in modalità --test).
    state = FilterState(hostname)
    # Percorso dell'eseguibile dell'agente: serve al firewall per consentirgli
    # l'uscita anche a lockdown attivo (solo se "congelato" con PyInstaller).
    agent_program = sys.executable if getattr(sys, "frozen", False) else None
    watcher = ConfigWatcher(state, enforce_enabled=apply_system, agent_program=agent_program)
    fb = FirebaseAgent(
        config["apiKey"], config["databaseURL"], config["room"],
        config["agentEmail"], config["agentPassword"], hostname,
        on_update=watcher.on_update,
        heartbeat_seconds=config.get("heartbeatSeconds", 30),
        reconcile_seconds=config.get("reconcileSeconds", 60),
    )
    try:
        fb.authenticate()
    except Exception as e:  # noqa: BLE001
        log.error("Autenticazione Firebase fallita: %s", e)
    fb.start()

    # 4. Thread di supporto: riapplicazione proxy (anti-manomissione) e
    #    watchdog anti-blocco (riapre l'uscita se l'agente resta isolato).
    stop_event = threading.Event()
    if apply_system:
        threading.Thread(target=reapply_proxy_loop, args=(address, stop_event), daemon=True).start()
        threading.Thread(target=lockdown_watchdog, args=(fb, watcher, stop_event), daemon=True).start()

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

    # Modalità test: avvia solo proxy + Firebase, senza toccare il sistema
    apply_system = "--test" not in sys.argv

    # Riavvio automatico in caso di errore non gestito (watchdog interno;
    # NSSM riavvia comunque il processo se termina del tutto).
    while True:
        try:
            run(apply_system=apply_system)
            break
        except Exception as e:  # noqa: BLE001
            log.exception("Errore non gestito, riavvio tra 5s: %s", e)
            time.sleep(5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
