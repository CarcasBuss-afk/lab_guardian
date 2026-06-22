"""Regole firewall di Windows per chiudere i bypass più comuni.

Il blocco di UDP/443 (QUIC / HTTP3) è essenziale: senza, i browser basati su
Chromium possono usare QUIC su UDP aggirando completamente il proxy HTTP.
"""

import subprocess

QUIC_RULE_NAME = "LabGuardian Block QUIC (UDP 443)"


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
