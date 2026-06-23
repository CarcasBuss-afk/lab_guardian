"""Client Firebase a privilegi ridotti (Strada 2).

Non usa l'Admin SDK (nessuna chiave admin sui PC). L'agente si autentica come
account "agente" tramite l'API REST di Firebase Auth e:
- ascolta in tempo reale la configurazione dell'aula via REST streaming (SSE);
- invia un heartbeat periodico sul proprio nodo PC (online/lastSeen/hostname).

Le regole del Realtime Database garantiscono che, anche con queste credenziali,
si possano scrivere solo i campi online/lastSeen/hostname del proprio PC.
"""

import json
import logging
import threading
import time

import requests

log = logging.getLogger("labguardian.firebase")

# Endpoint REST di Firebase Auth
SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

# I token ID scadono dopo ~1h: li rinnoviamo con margine
TOKEN_TTL_SECONDS = 3000


class FirebaseAgent:
    def __init__(self, api_key, database_url, room, email, password, hostname,
                 on_update, heartbeat_seconds=30):
        self.api_key = api_key
        self.database_url = database_url.rstrip("/")
        self.room = room
        self.email = email
        self.password = password
        self.hostname = hostname
        self.on_update = on_update
        self.heartbeat_seconds = heartbeat_seconds

        # Sessione che IGNORA il proxy di sistema/registro: l'agente deve
        # parlare con Firebase direttamente, mai attraverso il proxy locale.
        self._session = requests.Session()
        self._session.trust_env = False

        self._id_token = None
        self._refresh_token = None
        self._token_acquired_at = 0
        self._lab = {}  # ultima configurazione nota dell'aula
        self._stop = threading.Event()
        self._connected = threading.Event()  # streaming attivo
        self._threads = []

    # --- Autenticazione ---

    def authenticate(self):
        """Login come account agente. Solleva eccezione in caso di errore."""
        resp = self._session.post(
            f"{SIGN_IN_URL}?key={self.api_key}",
            json={"email": self.email, "password": self.password, "returnSecureToken": True},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self._id_token = data["idToken"]
        self._refresh_token = data["refreshToken"]
        self._token_acquired_at = time.time()
        log.info("Autenticazione agente riuscita")

    def _refresh_if_needed(self):
        if time.time() - self._token_acquired_at < TOKEN_TTL_SECONDS:
            return
        try:
            resp = self._session.post(
                f"{REFRESH_URL}?key={self.api_key}",
                data={"grant_type": "refresh_token", "refresh_token": self._refresh_token},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            self._id_token = data["id_token"]
            self._refresh_token = data["refresh_token"]
            self._token_acquired_at = time.time()
            log.info("Token rinnovato")
        except requests.RequestException as e:
            log.warning("Rinnovo token fallito: %s", e)

    # --- Stato ---

    @property
    def connected(self):
        return self._connected.is_set()

    def _lab_path(self):
        return f"{self.database_url}/labs/{self.room}.json"

    def _pc_path(self):
        return f"{self.database_url}/labs/{self.room}/pcs/{self.hostname}.json"

    # --- Streaming della configurazione (SSE) ---

    def _set_node(self, path, data):
        """PUT: sostituisce il nodo in path con data (None = elimina)."""
        if path in ("", "/"):
            self._lab = data if isinstance(data, dict) else {}
            return
        keys = [k for k in path.split("/") if k]
        node = self._lab
        for key in keys[:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = {}
                node[key] = child
            node = child
        last = keys[-1]
        if data is None:
            node.pop(last, None)
        else:
            node[last] = data

    def _apply_event(self, event, path, data):
        """Applica un evento SSE alla copia locale della configurazione.

        - put:   sostituisce il nodo in path con data.
        - patch: unisce i figli di data nel nodo in path, lasciando intatti gli
                 altri campi (es. 'patch / {active:true}' NON cancella whitelist).
        """
        if event == "patch" and isinstance(data, dict):
            base = "" if path == "/" else path.rstrip("/")
            for key, value in data.items():
                self._set_node(f"{base}/{key}", value)
        else:
            self._set_node(path, data)

    def _stream_loop(self):
        """Mantiene aperto lo streaming, riconnettendo in caso di caduta."""
        backoff = 2
        while not self._stop.is_set():
            try:
                self._refresh_if_needed()
                # Accept-Encoding identity + no-cache: niente compressione/buffer
                # intermedi, così gli eventi SSE arrivano subito.
                headers = {
                    "Accept": "text/event-stream",
                    "Accept-Encoding": "identity",
                    "Cache-Control": "no-cache",
                }
                url = f"{self._lab_path()}?auth={self._id_token}"
                with self._session.get(url, headers=headers, stream=True, timeout=(15, 75)) as resp:
                    resp.raise_for_status()
                    self._connected.set()
                    backoff = 2
                    log.info("Streaming configurazione attivo")
                    event = None
                    # chunk_size=1: nessun buffering lato requests, propagazione immediata
                    for raw in resp.iter_lines(decode_unicode=True, chunk_size=1):
                        if self._stop.is_set():
                            break
                        if raw is None or raw == "":
                            continue
                        if raw.startswith("event:"):
                            event = raw[len("event:"):].strip()
                        elif raw.startswith("data:"):
                            payload = raw[len("data:"):].strip()
                            if event in ("put", "patch") and payload and payload != "null":
                                try:
                                    msg = json.loads(payload)
                                    self._apply_event(event, msg.get("path", "/"), msg.get("data"))
                                    self.on_update(dict(self._lab))
                                except ValueError:
                                    pass
            except requests.RequestException as e:
                log.warning("Streaming interrotto: %s", e)
            finally:
                self._connected.clear()
            if self._stop.is_set():
                break
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)

    # --- Heartbeat ---

    def _heartbeat_loop(self):
        while not self._stop.is_set():
            try:
                self._refresh_if_needed()
                payload = {
                    "hostname": self.hostname,
                    "online": True,
                    # Timestamp lato server di Firebase
                    "lastSeen": {".sv": "timestamp"},
                }
                self._session.patch(
                    f"{self._pc_path()}?auth={self._id_token}",
                    json=payload,
                    timeout=15,
                )
            except requests.RequestException as e:
                log.debug("Heartbeat fallito: %s", e)
            self._stop.wait(self.heartbeat_seconds)

    def set_offline(self):
        """Segna il PC come offline (usato alla disinstallazione)."""
        try:
            self._refresh_if_needed()
            self._session.patch(
                f"{self._pc_path()}?auth={self._id_token}",
                json={"online": False},
                timeout=15,
            )
        except requests.RequestException:
            pass

    # --- Ciclo di vita ---

    def start(self):
        for target in (self._stream_loop, self._heartbeat_loop):
            t = threading.Thread(target=target, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()
