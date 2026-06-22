"""Policy dei browser per chiudere ulteriori bypass.

- Chrome/Edge: disabilita QUIC (cintura di sicurezza oltre alla regola firewall)
  e forza l'uso del proxy di sistema.
- Firefox: non legge il proxy di sistema di default; con policies.json lo forziamo.
"""

import json
import os
import winreg

CHROME_POLICY = r"SOFTWARE\Policies\Google\Chrome"
EDGE_POLICY = r"SOFTWARE\Policies\Microsoft\Edge"

# Percorso standard della policy di Firefox (se installato)
FIREFOX_POLICY_DIR = r"C:\Program Files\Mozilla Firefox\distribution"
FIREFOX_POLICY_FILE = os.path.join(FIREFOX_POLICY_DIR, "policies.json")


def _set_chromium_policy(path):
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
        # Disabilita QUIC/HTTP3
        winreg.SetValueEx(key, "QuicAllowed", 0, winreg.REG_DWORD, 0)
        # Forza l'uso del proxy di sistema (ProxyMode = "system")
        winreg.SetValueEx(key, "ProxyMode", 0, winreg.REG_SZ, "system")


def _delete_chromium_policy(path):
    for name in ("QuicAllowed", "ProxyMode"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except OSError:
            pass


def apply_policies():
    """Applica le policy di Chrome, Edge e (se presente) Firefox."""
    for path in (CHROME_POLICY, EDGE_POLICY):
        try:
            _set_chromium_policy(path)
        except OSError:
            pass

    # Firefox: scriviamo policies.json solo se la cartella di installazione esiste
    if os.path.isdir(os.path.dirname(FIREFOX_POLICY_DIR)):
        try:
            os.makedirs(FIREFOX_POLICY_DIR, exist_ok=True)
            policy = {"policies": {"Proxy": {"Mode": "system"}}}
            with open(FIREFOX_POLICY_FILE, "w", encoding="utf-8") as f:
                json.dump(policy, f, indent=2)
        except OSError:
            pass


def remove_policies():
    """Rimuove le policy applicate."""
    for path in (CHROME_POLICY, EDGE_POLICY):
        _delete_chromium_policy(path)

    # Rimuove il file Firefox solo se lo abbiamo creato noi (contiene solo Proxy)
    try:
        if os.path.exists(FIREFOX_POLICY_FILE):
            with open(FIREFOX_POLICY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            policies = data.get("policies", {})
            if set(policies.keys()) <= {"Proxy"}:
                os.remove(FIREFOX_POLICY_FILE)
    except (OSError, ValueError):
        pass
