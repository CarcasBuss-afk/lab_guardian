"""Addon mitmproxy: logica di filtraggio per dominio.

HTTPS: la decisione avviene sull'hostname del CONNECT, SENZA decifrare il
traffico (nessun certificato da installare). Il TLS viene fatto passare come
tunnel TCP grezzo.

Priorità delle decisioni:
1. Override del singolo PC:  "blocked" -> blocca tutto;  "free" -> permetti tutto;
   "inherit" -> applica le regole dell'aula.
2. Fail-open: solo se non è mai arrivata una configurazione (PC mai impostato).
3. Regole aula: se il filtro è spento -> permetti; altrimenti
   blacklist (priorità) -> blocca;  whitelist -> permetti;  resto -> blocca.
"""

import fnmatch
import threading

from mitmproxy import http


class FilterState:
    """Stato condiviso tra il client Firebase e l'addon (thread-safe)."""

    def __init__(self, hostname):
        self.hostname = hostname
        self._lock = threading.Lock()
        self.active = False
        self.whitelist = []
        self.blacklist = []
        self.override = "inherit"
        self.message = "Sito bloccato dal docente."
        self.has_config = False  # almeno una config ricevuta

    def update_from_lab(self, lab):
        """Aggiorna lo stato dalla configurazione dell'aula ricevuta da Firebase."""
        with self._lock:
            self.active = bool(lab.get("active", False))
            self.whitelist = list(lab.get("whitelist", []) or [])
            self.blacklist = list(lab.get("blacklist", []) or [])
            self.message = lab.get("message") or self.message
            pcs = lab.get("pcs", {}) or {}
            pc = pcs.get(self.hostname, {})
            self.override = pc.get("override", "inherit")
            self.has_config = True

    def snapshot(self):
        with self._lock:
            return {
                "active": self.active,
                "whitelist": list(self.whitelist),
                "blacklist": list(self.blacklist),
                "override": self.override,
                "message": self.message,
                "has_config": self.has_config,
            }


def _matches(host, patterns):
    """True se host corrisponde a uno dei pattern (supporta wildcard *)."""
    host = host.lower()
    return any(fnmatch.fnmatch(host, p.lower()) for p in patterns)


def is_allowed(host, snap):
    """Applica la logica di filtraggio a un hostname."""
    # 1. Override del singolo PC
    if snap["override"] == "free":
        return True
    if snap["override"] == "blocked":
        return False

    # 2. Fail-open: solo se non è mai arrivata una configurazione (PC mai impostato)
    if not snap["has_config"]:
        return True

    # 3. Regole dell'aula (override "inherit")
    if not snap["active"]:
        return True
    if _matches(host, snap["blacklist"]):
        return False
    if _matches(host, snap["whitelist"]):
        return True
    return False


class LabFilter:
    def __init__(self, state):
        self.state = state

    def http_connect(self, flow: http.HTTPFlow):
        """Filtra le richieste HTTPS sull'hostname del CONNECT (prima del TLS).
        Se il sito è bloccato, rifiuta il tunnel con un 403."""
        snap = self.state.snapshot()
        if not is_allowed(flow.request.host, snap):
            flow.response = http.Response.make(
                403, snap["message"].encode("utf-8"),
                {"Content-Type": "text/plain; charset=utf-8"},
            )

    def tls_clienthello(self, data):
        """Le connessioni HTTPS che superano il CONNECT sono consentite: le
        lasciamo passare SENZA decifrarle (nessun certificato da installare).
        Così il browser dialoga direttamente col certificato vero del sito."""
        data.ignore_connection = True

    def request(self, flow: http.HTTPFlow):
        """Filtra le richieste HTTP in chiaro."""
        snap = self.state.snapshot()
        if not is_allowed(flow.request.pretty_host, snap):
            flow.response = http.Response.make(
                403, snap["message"].encode("utf-8"),
                {"Content-Type": "text/plain; charset=utf-8"},
            )
