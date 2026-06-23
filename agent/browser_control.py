"""Chiusura dei browser e pulizia delle loro cache.

Serve a chiudere il buco dei contenuti che girano "offline" (pagine in cache e
soprattutto giochi PWA con service worker): un filtro di rete non li vede.
Quando il blocco viene attivato, l'agente chiude i browser e ne cancella
cache e service worker, così alla riapertura tutto ripassa dal filtro.

Gira come SYSTEM, quindi può terminare i processi degli utenti e accedere ai
loro profili.
"""

import glob
import logging
import os
import shutil
import subprocess
import time

log = logging.getLogger("labguardian.browser")

# Processi dei browser da terminare
BROWSER_PROCESSES = ["chrome.exe", "msedge.exe", "firefox.exe"]

# Sottocartelle di cache/offline dei browser Chromium (per profilo)
CHROMIUM_PROFILE_CACHE = [
    "Cache", "Code Cache", "GPUCache", "Service Worker",
    "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache",
]
# Cache a livello di "User Data" (non per profilo)
CHROMIUM_ROOT_CACHE = ["GrShaderCache", "ShaderCache", "GraphiteDawnCache"]


def _no_window():
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def kill_browsers():
    """Termina i browser (e i processi figli)."""
    for proc in BROWSER_PROCESSES:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc, "/T"],
                capture_output=True, creationflags=_no_window(),
            )
        except OSError:
            pass


def _rmtree(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


def _user_dirs():
    """Elenca i profili utente reali sotto C:\\Users."""
    users_root = os.path.join(os.environ.get("SystemDrive", "C:") + "\\", "Users")
    skip = {"public", "default", "default user", "all users"}
    dirs = []
    try:
        for name in os.listdir(users_root):
            if name.lower() in skip:
                continue
            path = os.path.join(users_root, name)
            if os.path.isdir(path):
                dirs.append(path)
    except OSError:
        pass
    return dirs


def _clear_chromium(user_data):
    """Cancella cache e service worker di un browser Chromium (Chrome/Edge)."""
    if not os.path.isdir(user_data):
        return
    for d in CHROMIUM_ROOT_CACHE:
        _rmtree(os.path.join(user_data, d))
    try:
        for entry in os.listdir(user_data):
            if entry == "Default" or entry.startswith("Profile"):
                profile = os.path.join(user_data, entry)
                if os.path.isdir(profile):
                    for d in CHROMIUM_PROFILE_CACHE:
                        _rmtree(os.path.join(profile, d))
    except OSError:
        pass


def _clear_firefox(user):
    """Cancella cache e storage offline (service worker) di Firefox."""
    local = os.path.join(user, "AppData", "Local", "Mozilla", "Firefox", "Profiles")
    roaming = os.path.join(user, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    for prof in glob.glob(os.path.join(local, "*")):
        _rmtree(os.path.join(prof, "cache2"))
        _rmtree(os.path.join(prof, "startupCache"))
    for prof in glob.glob(os.path.join(roaming, "*")):
        _rmtree(os.path.join(prof, "storage"))


def clear_caches():
    """Pulisce le cache dei browser per tutti i profili utente."""
    for user in _user_dirs():
        _clear_chromium(os.path.join(user, "AppData", "Local", "Google", "Chrome", "User Data"))
        _clear_chromium(os.path.join(user, "AppData", "Local", "Microsoft", "Edge", "User Data"))
        _clear_firefox(user)


def enforce_clean():
    """Chiude i browser e ne pulisce le cache (eseguire in un thread a parte)."""
    log.info("Blocco attivato: chiusura browser")
    kill_browsers()
    # Attende il rilascio dei file prima di cancellare
    time.sleep(2)
    log.info("Pulizia cache/service worker dei browser")
    clear_caches()
    log.info("Pulizia browser completata")
