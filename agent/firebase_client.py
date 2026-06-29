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
# Vita effettiva di un token ID Firebase (~1h)
TOKEN_LIFETIME_SECONDS = 3600
# Ricicla la connessione streaming con questo anticipo sulla scadenza del token
# con cui e' stata aperta (Firebase la chiude/rende "zombie" a token scaduto).
STREAM_RECYCLE_MARGIN = 300


class FirebaseAgent:
    def __init__(self, api_key, database_url, room, email, password, hostname,
                 on_update, heartbeat_seconds=30, reconcile_seconds=60):
        self.api_key = api_key
        self.database_url = database_url.rstrip("/")
        self.room = room
        self.email = email
        self.password = password
        self.hostname = hostname
        self.on_update = on_update
        self.heartbeat_seconds = heartbeat_seconds
        self.reconcile_seconds = reconcile_seconds

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
        # Serializza le chiamate a on_update e le modifiche a _lab: ora ci sono
        # DUE produttori (lo streaming e la riconciliazione periodica) e
        # on_update agisce sul firewall, quindi non deve mai girare in parallelo.
        self._update_lock = threading.Lock()
        # Istante dell'ultima sincronizzazione RIUSCITA (stream o riconciliazione):
        # il watchdog anti-blocco lo usa per accorgersi anche di uno stream
        # "zombie" (connesso ma che non consegna piu' eventi).
        self._last_sync = time.time()
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

    @property
    def seconds_since_sync(self):
        """Secondi trascorsi dall'ultima sincronizzazione riuscita."""
        return time.time() - self._last_sync

    def _dispatch_update(self):
        """Inoltra lo stato a on_update e marca la sincronizzazione.

        DEVE essere chiamato dentro self._update_lock (lo invocano sia lo
        streaming sia la riconciliazione)."""
        self.on_update(dict(self._lab))
        self._last_sync = time.time()

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
        """Mantiene aperto lo streaming, riconnettendo in caso di caduta.

        La connessione viene RICICLATA proattivamente prima che il token con cui
        e' stata aperta scada: Firebase chiude (o rende "zombie") lo stream a
        token scaduto, ed e' cosi' che un PC era rimasto bloccato. Riaprendo con
        un token fresco lo stream resta sempre reattivo.
        """
        backoff = 2
        while not self._stop.is_set():
            try:
                self._refresh_if_needed()
                # Scadenza di questa connessione: ricicla con margine prima che il
                # token corrente muoia (non meno di 60s per evitare loop stretti).
                token_age = time.time() - self._token_acquired_at
                deadline = time.time() + max(
                    60, TOKEN_LIFETIME_SECONDS - token_age - STREAM_RECYCLE_MARGIN
                )
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
                        # Riciclo proattivo: riapri con un token fresco prima della
                        # scadenza. Il keep-alive SSE (~30s) sveglia il loop in tempo.
                        if time.time() >= deadline:
                            log.info("Riciclo proattivo dello streaming (token in scadenza)")
                            break
                        if raw is None or raw == "":
                            continue
                        if raw.startswith("event:"):
                            event = raw[len("event:"):].strip()
                            # Token revocato o permessi persi: Firebase sta chiudendo
                            # lo stream. Riconnetti subito con un token fresco.
                            if event in ("auth_revoked", "cancel"):
                                log.info("Evento '%s' dallo streaming: riconnetto", event)
                                break
                        elif raw.startswith("data:"):
                            payload = raw[len("data:"):].strip()
                            if event in ("put", "patch") and payload and payload != "null":
                                try:
                                    msg = json.loads(payload)
                                except ValueError:
                                    continue
                                with self._update_lock:
                                    self._apply_event(event, msg.get("path", "/"), msg.get("data"))
                                    self._dispatch_update()
            except requests.RequestException as e:
                log.warning("Streaming interrotto: %s", e)
            finally:
                self._connected.clear()
            if self._stop.is_set():
                break
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)

    # --- Riconciliazione periodica (pull) ---

    def _fetch_lab(self):
        """GET singola dello stato dell'aula. Ritorna il dict (o None)."""
        self._refresh_if_needed()
        url = f"{self._lab_path()}?auth={self._id_token}"
        resp = self._session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _reconcile_loop(self):
        """Riallinea periodicamente lo stato reale con Firebase (rete di sicurezza).

        Lo streaming e' push: se perde un evento (token scaduto sulla connessione
        lunga, glitch di rete, NAT della scuola, stream "zombie") lo stato del
        firewall puo' restare divergente all'infinito. Questo loop fa una GET REST
        secca ogni 'reconcile_seconds' e la passa allo stesso on_update: cosi' un
        cambiamento perso (es. blocco rimosso) viene comunque applicato entro un
        minuto e un PC non puo' restare bloccato per sempre. La richiesta e' breve
        (si apre e chiude subito, come l'heartbeat) quindi non soffre il problema
        di scadenza token della connessione streaming.
        """
        while not self._stop.is_set():
            self._stop.wait(self.reconcile_seconds)
            if self._stop.is_set():
                break
            try:
                data = self._fetch_lab()
            except requests.RequestException as e:
                log.debug("Riconciliazione fallita: %s", e)
                continue
            if not isinstance(data, dict):
                continue
            with self._update_lock:
                # La GET ritorna lo stato AUTORITATIVO completo: sostituisce la
                # copia locale (lo streaming poi continua a fare merge da qui).
                self._lab = data
                self._dispatch_update()

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
        for target in (self._stream_loop, self._heartbeat_loop, self._reconcile_loop):
            t = threading.Thread(target=target, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()
