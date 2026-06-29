"""Spike A - flusso di login Google per il gate allievi (riutilizzabile).

Flusso OAuth 2.0 Authorization Code + PKCE per app native (RFC 8252):
- apre il browser di sistema sulla pagina di login Google;
- cattura il 'code' su un redirect loopback 127.0.0.1;
- scambia il code per i token;
- valida l'ID token (firma via JWKS, aud, iss, exp) e ritorna i claim.

NON e' codice di produzione: serve a validare il meccanismo. La funzione
`login()` e' riusata dallo Spike B1 (overlay).

Uso CLI:
    python agent/spike_oauth.py

Prerequisiti:
    - agent/oauth_client.json (client OAuth tipo "App desktop")
    - l'account di login aggiunto come "utente di test" nella consent screen
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_PATH = os.path.join(HERE, "oauth_client.json")

SCOPES = "openid email profile"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
VALID_ISS = ("https://accounts.google.com", "accounts.google.com")

# Dominio Workspace da imporre (claim hd). Vuoto in test (anche un account
# Workspace passa). In produzione: "ciacdidattica.it" -> login fuori dominio rifiutati.
HD_DOMAIN = ""


def b64url_decode(data):
    """Decodifica base64url aggiungendo il padding mancante."""
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def load_client():
    """Carica il client OAuth dal JSON di Google (chiave 'installed' per desktop)."""
    with open(CLIENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("installed") or data.get("web") or data


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Cattura il redirect del browser sul loopback."""

    result = {}
    done = threading.Event()

    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        # Ignora richieste spurie (es. /favicon.ico)
        if "code" not in params and "error" not in params:
            self.send_response(404)
            self.end_headers()
            return
        CallbackHandler.result = {k: v[0] for k, v in params.items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<html><body style='font-family:sans-serif;text-align:center;margin-top:3em'>"
            "<h2>Login completato</h2>"
            "<p>Puoi chiudere questa scheda e tornare all'app.</p>"
            "</body></html>".encode("utf-8")
        )
        CallbackHandler.done.set()

    def log_message(self, *args):
        pass  # silenzia i log del server


def verify_id_token(id_token, client_id):
    """Valida firma (JWKS Google) e claim dell'ID token. Ritorna i claim.

    Solleva RuntimeError se la validazione fallisce.
    """
    try:
        header_b64, payload_b64, sig_b64 = id_token.split(".")
    except ValueError:
        raise RuntimeError("JWT malformato")
    header = json.loads(b64url_decode(header_b64))
    payload = json.loads(b64url_decode(payload_b64))

    # Trova la chiave pubblica Google corrispondente al 'kid' dell'header
    jwks = requests.get(JWKS_URL, timeout=15).json()
    key = next((k for k in jwks["keys"] if k["kid"] == header.get("kid")), None)
    if key is None:
        raise RuntimeError("kid del token non trovato tra le chiavi Google")

    n = int.from_bytes(b64url_decode(key["n"]), "big")
    e = int.from_bytes(b64url_decode(key["e"]), "big")
    public_key = rsa.RSAPublicNumbers(e, n).public_key()

    # Verifica firma RS256 su "header.payload"
    signing_input = f"{header_b64}.{payload_b64}".encode()
    try:
        public_key.verify(
            b64url_decode(sig_b64), signing_input, padding.PKCS1v15(), hashes.SHA256()
        )
    except InvalidSignature:
        raise RuntimeError("firma del token NON valida")

    # Verifica claim
    now = time.time()
    if payload.get("iss") not in VALID_ISS:
        raise RuntimeError(f"issuer non valido: {payload.get('iss')}")
    if payload.get("aud") != client_id:
        raise RuntimeError("audience non corrisponde al client")
    if payload.get("exp", 0) < now:
        raise RuntimeError("token scaduto")

    return payload


def login(hd_domain=HD_DOMAIN, status=print, cancel_event=None):
    """Esegue il login Google e ritorna i claim validati.

    `status` e' una callback per i messaggi di avanzamento (default: print).
    `cancel_event` (threading.Event) permette di annullare l'attesa del login.
    Solleva RuntimeError in caso di errore o annullamento.
    """
    if not os.path.exists(CLIENT_PATH):
        raise RuntimeError(f"manca {CLIENT_PATH}")
    client = load_client()
    client_id = client["client_id"]
    client_secret = client.get("client_secret")
    auth_uri = client.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
    token_uri = client.get("token_uri", "https://oauth2.googleapis.com/token")

    # 1. PKCE: verifier casuale + challenge = base64url(sha256(verifier))
    code_verifier = b64url_encode(secrets.token_bytes(64))
    code_challenge = b64url_encode(hashlib.sha256(code_verifier.encode()).digest())
    state = secrets.token_urlsafe(16)

    # 2. Server loopback su porta effimera scelta dall'OS (stato handler azzerato)
    CallbackHandler.result = {}
    CallbackHandler.done = threading.Event()
    server = http.server.HTTPServer(("127.0.0.1", 0), CallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}/"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # 3. URL di autorizzazione e apertura del browser di sistema
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "prompt": "select_account",
    }
    if hd_domain:
        params["hd"] = hd_domain
    auth_url = auth_uri + "?" + urllib.parse.urlencode(params)

    status("Apro il browser per il login...")
    webbrowser.open(auth_url)

    try:
        # 4. Attendi il redirect (max 180s), controllando l'eventuale annullamento
        deadline = time.time() + 180
        while not CallbackHandler.done.wait(timeout=0.3):
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("login annullato")
            if time.time() > deadline:
                raise RuntimeError("timeout: nessuna risposta dal login")
        result = CallbackHandler.result
        if "error" in result:
            raise RuntimeError(result.get("error_description") or result["error"])
        if result.get("state") != state:
            raise RuntimeError("'state' non corrispondente (possibile CSRF)")
        code = result["code"]

        # 5. Scambio code -> token (con il code_verifier PKCE)
        status("Verifica delle credenziali...")
        token_resp = requests.post(
            token_uri,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=15,
        )
    finally:
        server.shutdown()

    if not token_resp.ok:
        raise RuntimeError(f"scambio token fallito ({token_resp.status_code})")
    id_token = token_resp.json().get("id_token")
    if not id_token:
        raise RuntimeError("nessun id_token nella risposta")

    # 6. Validazione dell'ID token (come fara' il servizio SYSTEM in produzione)
    claims = verify_id_token(id_token, client_id)
    if hd_domain and claims.get("hd") != hd_domain:
        raise RuntimeError(f"dominio non autorizzato: {claims.get('hd') or '(assente)'}")
    return claims


def main():
    try:
        claims = login(status=print)
    except RuntimeError as e:
        print("ERRORE:", e)
        return 1

    print("\n=== LOGIN VALIDATO ===")
    print("email          :", claims.get("email"))
    print("email_verified :", claims.get("email_verified"))
    print("hd (dominio)   :", claims.get("hd", "(assente - account non Workspace)"))
    print("sub (id utente):", claims.get("sub"))
    print("name           :", claims.get("name"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
