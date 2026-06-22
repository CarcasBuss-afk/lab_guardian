"""Gestione del proxy di sistema su Windows (registro).

Strategia anti-bypass:
- Il proxy viene imposto a livello MACCHINA via Group Policy (HKLM), valido per
  tutti gli utenti e non modificabile dagli studenti non-admin.
- Le impostazioni proxy originali (incluso un eventuale proxy scolastico
  "upstream") vengono salvate su file PRIMA di sovrascriverle, per poterle
  ripristinare alla disinstallazione.
"""

import json
import os
import winreg

# Impostazioni proxy per-utente (lette per rilevare l'eventuale proxy scuola)
USER_INTERNET_SETTINGS = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

# Impostazioni proxy a livello macchina (usate quando ProxySettingsPerUser = 0)
MACHINE_INTERNET_SETTINGS = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings"

# Policy che rende le impostazioni proxy valide per l'intera macchina
POLICY_INTERNET_SETTINGS = r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\Internet Settings"

# Policy che impedisce all'utente di cambiare le impostazioni proxy
POLICY_IE_PROXY = r"SOFTWARE\Policies\Microsoft\Internet Explorer\Control Panel"


def _read_value(hive, path, name):
    """Legge un valore dal registro, None se assente."""
    try:
        with winreg.OpenKey(hive, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value
    except FileNotFoundError:
        return None
    except OSError:
        return None


def get_current_user_proxy():
    """Restituisce le impostazioni proxy correnti dell'utente."""
    enable = _read_value(winreg.HKEY_CURRENT_USER, USER_INTERNET_SETTINGS, "ProxyEnable")
    server = _read_value(winreg.HKEY_CURRENT_USER, USER_INTERNET_SETTINGS, "ProxyServer")
    return {"ProxyEnable": int(enable or 0), "ProxyServer": server or ""}


def detect_school_proxy(our_address):
    """Rileva un eventuale proxy scolastico già configurato (upstream).

    Restituisce l'indirizzo (es. "proxy.scuola.it:8080") oppure None se non
    presente o se è già il nostro proxy locale.
    """
    current = get_current_user_proxy()
    server = current["ProxyServer"]
    if current["ProxyEnable"] and server and "127.0.0.1" not in server and our_address not in server:
        # Formati possibili: "host:port" oppure "http=host:port;https=host:port"
        return server
    return None


def backup_original_proxy(backup_path):
    """Salva le impostazioni proxy originali, una sola volta."""
    if os.path.exists(backup_path):
        return
    data = get_current_user_proxy()
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _set_dword(hive, path, name, value):
    with winreg.CreateKey(hive, path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)


def _set_string(hive, path, name, value):
    with winreg.CreateKey(hive, path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def enable_filter_proxy(address):
    """Imposta il nostro proxy a livello macchina e blocca la modifica utente."""
    # Impostazioni proxy valide per tutta la macchina (non per-utente)
    _set_dword(winreg.HKEY_LOCAL_MACHINE, POLICY_INTERNET_SETTINGS, "ProxySettingsPerUser", 0)

    # Proxy attivo verso il nostro listener locale
    _set_dword(winreg.HKEY_LOCAL_MACHINE, MACHINE_INTERNET_SETTINGS, "ProxyEnable", 1)
    _set_string(winreg.HKEY_LOCAL_MACHINE, MACHINE_INTERNET_SETTINGS, "ProxyServer", address)
    # Escludi gli indirizzi locali dal proxy
    _set_string(winreg.HKEY_LOCAL_MACHINE, MACHINE_INTERNET_SETTINGS, "ProxyOverride", "<local>")

    # Impedisci all'utente di cambiare le impostazioni proxy
    _set_dword(winreg.HKEY_LOCAL_MACHINE, POLICY_IE_PROXY, "Proxy", 1)


def reapply_filter_proxy(address):
    """Riapplica le chiavi proxy (loop anti-manomissione)."""
    try:
        enable_filter_proxy(address)
    except OSError:
        pass


def _delete_value(hive, path, name):
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    except OSError:
        pass


def restore_original_proxy(backup_path):
    """Ripristina le impostazioni proxy originali e rimuove le policy imposte."""
    # Rimuovi le policy di blocco
    _delete_value(winreg.HKEY_LOCAL_MACHINE, POLICY_IE_PROXY, "Proxy")
    _delete_value(winreg.HKEY_LOCAL_MACHINE, POLICY_INTERNET_SETTINGS, "ProxySettingsPerUser")
    _delete_value(winreg.HKEY_LOCAL_MACHINE, MACHINE_INTERNET_SETTINGS, "ProxyEnable")
    _delete_value(winreg.HKEY_LOCAL_MACHINE, MACHINE_INTERNET_SETTINGS, "ProxyServer")
    _delete_value(winreg.HKEY_LOCAL_MACHINE, MACHINE_INTERNET_SETTINGS, "ProxyOverride")

    # Ripristina le impostazioni utente originali, se ne avevamo un backup
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {"ProxyEnable": 0, "ProxyServer": ""}
        _set_dword(
            winreg.HKEY_CURRENT_USER, USER_INTERNET_SETTINGS, "ProxyEnable",
            int(data.get("ProxyEnable", 0)),
        )
        _set_string(
            winreg.HKEY_CURRENT_USER, USER_INTERNET_SETTINGS, "ProxyServer",
            data.get("ProxyServer", ""),
        )
