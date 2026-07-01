"""Policy dei browser per chiudere ulteriori bypass.

- Chrome/Edge: disabilita QUIC (cintura di sicurezza oltre alla regola firewall)
  e forza il NOSTRO proxy locale a livello di browser (ProxyMode "fixed_servers").
  La policy del browser ha la precedenza sul proxy di sistema, WPAD/PAC inclusi:
  indispensabile sui PC dove un'organizzazione (GPO/MDM) impone un proxy
  automatico che scavalcherebbe il nostro proxy di sistema.
- Firefox: non legge il proxy di sistema di default; con policies.json forziamo
  lo stesso proxy locale in modalita' manuale.
"""

import json
import os
import winreg

CHROME_POLICY = r"SOFTWARE\Policies\Google\Chrome"
EDGE_POLICY = r"SOFTWARE\Policies\Microsoft\Edge"

# Percorso standard della policy di Firefox (se installato)
FIREFOX_POLICY_DIR = r"C:\Program Files\Mozilla Firefox\distribution"
FIREFOX_POLICY_FILE = os.path.join(FIREFOX_POLICY_DIR, "policies.json")


def _set_chromium_policy(path, proxy_address):
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
        # Disabilita QUIC/HTTP3
        winreg.SetValueEx(key, "QuicAllowed", 0, winreg.REG_DWORD, 0)
        # Forza il NOSTRO proxy locale (ProxyMode = "fixed_servers"): a livello
        # di browser ha la precedenza sul proxy di sistema/WPAD/PAC dell'org.
        winreg.SetValueEx(key, "ProxyMode", 0, winreg.REG_SZ, "fixed_servers")
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_address)


def _delete_chromium_policy(path):
    for name in ("QuicAllowed", "ProxyMode", "ProxyServer"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except OSError:
            pass


def apply_policies(proxy_address):
    """Applica le policy di Chrome, Edge e (se presente) Firefox.

    proxy_address: indirizzo del proxy locale di filtraggio (es. "127.0.0.1:8080").
    """
    for path in (CHROME_POLICY, EDGE_POLICY):
        try:
            _set_chromium_policy(path, proxy_address)
        except OSError:
            pass

    # Firefox: scriviamo policies.json solo se la cartella di installazione esiste
    if os.path.isdir(os.path.dirname(FIREFOX_POLICY_DIR)):
        try:
            os.makedirs(FIREFOX_POLICY_DIR, exist_ok=True)
            # Modalita' manuale sullo stesso proxy locale (UseHTTPProxyForAll:
            # instrada anche HTTPS sul proxy HTTP). Locked: l'utente non lo cambia.
            policy = {"policies": {"Proxy": {
                "Mode": "manual",
                "HTTPProxy": proxy_address,
                "UseHTTPProxyForAllProtocols": True,
                "Locked": True,
            }}}
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
