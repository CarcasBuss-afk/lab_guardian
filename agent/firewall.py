"""Regole firewall di Windows per chiudere i bypass.

Due livelli di difesa:

1. Blocco QUIC (UDP 443): sempre attivo finche' gira l'agente. Senza, i browser
   Chromium possono usare QUIC su UDP aggirando il proxy HTTP.

2. Egress-lockdown ("nega tutto, permetti il minimo"): si attiva insieme al
   blocco dell'aula e si disattiva quando il blocco viene tolto. Imposta
   l'azione predefinita in USCITA su "Block" e aggiunge regole di ALLOW solo
   per l'indispensabile (agente, rete locale, DNS, DHCP). Cosi' qualunque
   programma che ignora il proxy (curl, Tor, VPN/tunnel su porte arbitrarie,
   Firefox col proxy spento...) non riesce a uscire: l'unica via verso Internet
   resta il proxy locale, che filtra per dominio.

   Le regole del lockdown sono gestite via PowerShell (cmdlet NetSecurity)
   perche' gestiscono in modo affidabile i percorsi con spazi (-Program) e
   l'azione predefinita in uscita (-DefaultOutboundAction), cosa che netsh fa
   in modo fragile. CRUCIALE: la regola che autorizza l'agente DEVE agganciare
   davvero il suo processo, altrimenti l'agente perde Firebase e non puo' piu'
   togliere il blocco (il PC resta isolato).
"""

import logging
import subprocess

log = logging.getLogger("labguardian.firewall")

QUIC_RULE_NAME = "LabGuardian Block QUIC (UDP 443)"

# Prefisso comune delle regole del lockdown (per crearle/rimuoverle in blocco)
LOCKDOWN_PREFIX = "LabGuardian Lockdown"
LOCKDOWN_AGENT_RULE = "LabGuardian Lockdown Allow Agent"

# Destinazioni sempre consentite anche a lockdown attivo: loopback, reti private
# (LAN: Veyon, stampanti, server interni, condivisioni), link-local, multicast e
# broadcast (discovery di Veyon e simili).
LOCAL_RANGES = (
    "127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,"
    "169.254.0.0/16,224.0.0.0/4,255.255.255.255"
)


def _netsh(args):
    """Esegue netsh nascondendo la finestra; True se va a buon fine."""
    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "firewall", *args],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except OSError:
        return False


def _run_ps(script):
    """Esegue uno script PowerShell; ritorna (ok, output)."""
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-Command", script,
            ],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, out
    except OSError as e:
        return False, str(e)


# --- Blocco QUIC (sempre attivo finche' gira l'agente) ---

def block_quic():
    """Blocca il traffico QUIC in uscita (UDP porta 443)."""
    # Rimuove un'eventuale regola precedente per evitare duplicati
    remove_quic_block()
    return _netsh([
        "add", "rule",
        f"name={QUIC_RULE_NAME}",
        "dir=out",
        "action=block",
        "protocol=UDP",
        "remoteport=443",
    ])


def remove_quic_block():
    """Rimuove la regola firewall del QUIC."""
    return _netsh(["delete", "rule", f"name={QUIC_RULE_NAME}"])


# --- Egress-lockdown (sale/scende col blocco dell'aula) ---

def enable_lockdown(agent_program):
    """Attiva il default-deny in uscita, consentendo solo l'indispensabile.

    agent_program: percorso assoluto di lab-agent.exe. Se assente NON si attiva
    il lockdown: bloccare l'uscita senza autorizzare l'agente lo isolerebbe da
    Firebase (il PC resterebbe bloccato senza via d'uscita).

    Ritorna True solo se il muro e' stato alzato con successo.
    """
    if not agent_program:
        log.warning("Lockdown NON attivato: percorso agente sconosciuto (evito di isolare il PC)")
        return False

    # Le regole di ALLOW vengono create PRIMA, il muro si alza solo alla fine.
    # Path tra apici singoli: PowerShell li tratta come letterali (spazi ok).
    safe_path = agent_program.replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; "
        "try { "
        f"Remove-NetFirewallRule -DisplayName '{LOCKDOWN_PREFIX}*' -ErrorAction SilentlyContinue; "
        f"New-NetFirewallRule -DisplayName '{LOCKDOWN_AGENT_RULE}' -Direction Outbound "
        f"-Action Allow -Program '{safe_path}' -Profile Any | Out-Null; "
        f"New-NetFirewallRule -DisplayName '{LOCKDOWN_PREFIX} Allow LAN' -Direction Outbound "
        f"-Action Allow -RemoteAddress {LOCAL_RANGES} -Profile Any | Out-Null; "
        f"New-NetFirewallRule -DisplayName '{LOCKDOWN_PREFIX} Allow DNS UDP' -Direction Outbound "
        "-Action Allow -Protocol UDP -RemotePort 53 -Profile Any | Out-Null; "
        f"New-NetFirewallRule -DisplayName '{LOCKDOWN_PREFIX} Allow DNS TCP' -Direction Outbound "
        "-Action Allow -Protocol TCP -RemotePort 53 -Profile Any | Out-Null; "
        f"New-NetFirewallRule -DisplayName '{LOCKDOWN_PREFIX} Allow DHCP' -Direction Outbound "
        "-Action Allow -Protocol UDP -LocalPort 68 -RemotePort 67 -Profile Any | Out-Null; "
        "Set-NetFirewallProfile -All -DefaultOutboundAction Block; "
        "Write-Output 'LOCKDOWN_OK' "
        "} catch { Write-Output ('LOCKDOWN_ERR: ' + $_.Exception.Message) }"
    )
    ok, out = _run_ps(script)
    if ok and "LOCKDOWN_OK" in out:
        log.info("Egress-lockdown ATTIVATO (uscita predefinita: Block)")
        return True

    # Qualcosa e' andato storto: per sicurezza riapriamo l'uscita.
    log.warning("Egress-lockdown FALLITO (%s), ripristino l'uscita", out.strip())
    disable_lockdown()
    return False


def disable_lockdown():
    """Disattiva il lockdown: ripristina l'uscita predefinita e toglie le regole."""
    script = (
        "Set-NetFirewallProfile -All -DefaultOutboundAction Allow; "
        f"Remove-NetFirewallRule -DisplayName '{LOCKDOWN_PREFIX}*' -ErrorAction SilentlyContinue"
    )
    ok, out = _run_ps(script)
    if ok:
        log.info("Egress-lockdown DISATTIVATO (uscita predefinita: Allow)")
    else:
        log.warning("Disattivazione lockdown con errori: %s", out.strip())
    return ok
