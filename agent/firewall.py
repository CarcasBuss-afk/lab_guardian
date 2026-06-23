"""Regole firewall di Windows per chiudere i bypass.

Due livelli di difesa:

1. Blocco QUIC (UDP 443): sempre attivo finché gira l'agente. Senza, i browser
   Chromium possono usare QUIC su UDP aggirando il proxy HTTP.

2. Egress-lockdown ("nega tutto, permetti il minimo"): si attiva insieme al
   blocco dell'aula e si disattiva quando il blocco viene tolto. Imposta
   l'azione predefinita in USCITA su "Blocca" e aggiunge regole di ALLOW solo
   per l'indispensabile (agente, rete locale, DNS, DHCP). Così qualunque
   programma che ignora il proxy (curl, Tor, VPN/tunnel su porte arbitrarie,
   Firefox col proxy spento...) non riesce a uscire: l'unica via verso Internet
   resta il proxy locale, che filtra per dominio.

   Nota: su Windows una regola di BLOCK esplicita ha priorità su una di ALLOW,
   quindi non si può fare "blocca tutto + permetti l'agente". La via corretta è
   cambiare l'azione predefinita in uscita (DefaultOutboundAction = Block) e
   aggiungere solo regole di ALLOW: tutto ciò che non è esplicitamente
   permesso ricade nel blocco predefinito.
"""

import logging
import subprocess

log = logging.getLogger("labguardian.firewall")

QUIC_RULE_NAME = "LabGuardian Block QUIC (UDP 443)"

# Regole di ALLOW dell'egress-lockdown
LOCKDOWN_AGENT_RULE = "LabGuardian Lockdown Allow Agent"
LOCKDOWN_LAN_RULE = "LabGuardian Lockdown Allow LAN"
LOCKDOWN_DNS_UDP_RULE = "LabGuardian Lockdown Allow DNS UDP"
LOCKDOWN_DNS_TCP_RULE = "LabGuardian Lockdown Allow DNS TCP"
LOCKDOWN_DHCP_RULE = "LabGuardian Lockdown Allow DHCP"

LOCKDOWN_RULES = (
    LOCKDOWN_AGENT_RULE,
    LOCKDOWN_LAN_RULE,
    LOCKDOWN_DNS_UDP_RULE,
    LOCKDOWN_DNS_TCP_RULE,
    LOCKDOWN_DHCP_RULE,
)

# Destinazioni sempre consentite anche a lockdown attivo: loopback, reti private
# (LAN: Veyon, stampanti, server interni, condivisioni), link-local, multicast e
# broadcast (discovery di Veyon e simili).
LOCAL_RANGES = (
    "127.0.0.0/8,"
    "10.0.0.0/8,"
    "172.16.0.0/12,"
    "192.168.0.0/16,"
    "169.254.0.0/16,"
    "224.0.0.0/4,"
    "255.255.255.255"
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


def _set_default_outbound(action):
    """Imposta l'azione predefinita in uscita per tutti i profili del firewall.

    action: "Block" oppure "Allow". Usa PowerShell perché tocca SOLO l'uscita,
    lasciando intatte le regole di ingresso (a differenza di netsh che vuole
    entrambe le direzioni).
    """
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-Command",
                f"Set-NetFirewallProfile -All -DefaultOutboundAction {action}",
            ],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except OSError:
        return False


# --- Blocco QUIC (sempre attivo finché gira l'agente) ---

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

def _remove_lockdown_rules():
    """Rimuove le regole di ALLOW del lockdown (idempotente)."""
    for name in LOCKDOWN_RULES:
        _netsh(["delete", "rule", f"name={name}"])


def enable_lockdown(agent_program):
    """Attiva il default-deny in uscita, consentendo solo l'indispensabile.

    agent_program: percorso assoluto di lab-agent.exe (può uscire liberamente
    per conto del proxy). Se None, la regola sull'agente viene saltata.
    """
    # Riparte da pulito per evitare duplicati
    _remove_lockdown_rules()

    ok = True
    # 1. L'agente (il proxy) può uscire ovunque: è lui a raggiungere i siti
    #    consentiti, l'eventuale proxy scolastico upstream e Firebase.
    if agent_program:
        ok &= _netsh([
            "add", "rule", f"name={LOCKDOWN_AGENT_RULE}",
            "dir=out", "action=allow",
            f"program={agent_program}", "enable=yes", "profile=any",
        ])
    # 2. Rete locale (Veyon, stampanti, server interni), loopback, multicast
    ok &= _netsh([
        "add", "rule", f"name={LOCKDOWN_LAN_RULE}",
        "dir=out", "action=allow",
        f"remoteip={LOCAL_RANGES}", "profile=any",
    ])
    # 3. DNS (risoluzione dei nomi per il sistema operativo)
    ok &= _netsh([
        "add", "rule", f"name={LOCKDOWN_DNS_UDP_RULE}",
        "dir=out", "action=allow",
        "protocol=UDP", "remoteport=53", "profile=any",
    ])
    ok &= _netsh([
        "add", "rule", f"name={LOCKDOWN_DNS_TCP_RULE}",
        "dir=out", "action=allow",
        "protocol=TCP", "remoteport=53", "profile=any",
    ])
    # 4. DHCP (mantenimento/rinnovo dell'indirizzo IP)
    ok &= _netsh([
        "add", "rule", f"name={LOCKDOWN_DHCP_RULE}",
        "dir=out", "action=allow",
        "protocol=UDP", "localport=68", "remoteport=67", "profile=any",
    ])
    # 5. Solo ora alziamo il muro: tutto il resto in uscita viene bloccato
    ok &= _set_default_outbound("Block")

    if ok:
        log.info("Egress-lockdown ATTIVATO (uscita predefinita: blocco)")
    else:
        log.warning("Egress-lockdown attivato con errori (alcune regole non applicate)")
    return ok


def disable_lockdown():
    """Disattiva il lockdown: ripristina l'uscita predefinita e toglie le regole."""
    # Prima riapriamo l'uscita (ripristina la connettivita'), poi puliamo
    ok = _set_default_outbound("Allow")
    _remove_lockdown_rules()
    log.info("Egress-lockdown DISATTIVATO (uscita predefinita: consenti)")
    return ok
