# Lab Traffic Control — Documento Tecnico

## Panoramica del progetto

Sistema per il controllo del traffico web nei laboratori di informatica scolastici. Permette al docente di decidere, in tempo reale e da remoto, quali siti web sono accessibili dagli studenti.

---

## Architettura generale

Il sistema è composto da tre componenti:

```
[Dashboard docente]  ←→  [Firebase Realtime DB]  ←→  [Agente su ogni PC]
  (Next.js/Vercel)           (canale di controllo)       (Python + mitmproxy)
```

### Componente 1 — Dashboard docente
- Applicazione web Next.js deployata su Vercel
- Autenticazione docente tramite Firebase Auth
- Permette di gestire whitelist e blacklist
- Invia i comandi a tutti i PC in tempo reale tramite Firebase

### Componente 2 — Firebase Realtime Database
- Fa da "canale di controllo" tra docente e PC
- I PC ascoltano i cambiamenti in tempo reale (Firebase listener)
- Non richiede polling, la propagazione è istantanea

### Componente 3 — Agente locale (ogni PC del laboratorio)
- Script Python installato come servizio Windows (via NSSM)
- Avvia un proxy locale HTTP/HTTPS su `127.0.0.1:8080` (mitmproxy)
- Configura il proxy di sistema nel registro Windows
- Ascolta Firebase e aggiorna le regole di filtraggio in tempo reale

---

## Meccanismo di filtraggio

### Tecnologia: proxy locale HTTP/HTTPS (mitmproxy)

Il proxy gira sul PC stesso all'indirizzo `127.0.0.1:8080`. Il browser non comunica più direttamente con internet ma passa attraverso il proxy, che decide se permettere o bloccare ogni richiesta.

```
Browser → Proxy locale (127.0.0.1:8080) → Internet
```

Per HTTPS il proxy intercetta il comando `CONNECT hostname:443` e decide in base all'hostname, **senza decifrare il traffico** (nessun certificato da installare).

### Gestione del proxy scolastico (upstream)

Se la rete scolastica ha già un proprio proxy, l'agente lo rileva automaticamente dal registro Windows all'avvio e configura mitmproxy in modalità **upstream proxy**:

```
Browser → Proxy locale → Proxy scuola → Internet
```

Per rilevare il proxy scolastico:
```powershell
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" | Select-Object ProxyServer, ProxyEnable
```

### Configurazione proxy di sistema

L'agente imposta/rimuove il proxy di sistema tramite registro Windows:
```
HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings
  ProxyEnable = 1
  ProxyServer = 127.0.0.1:8080
```

---

## Logica di filtraggio

Il sistema usa **whitelist e blacklist simultaneamente**. La blacklist ha sempre priorità sulla whitelist.

```
Arriva richiesta per dominio X:

1. X è nella BLACKLIST?  → SÌ → BLOCCA (fine)
                         → NO → continua

2. X è nella WHITELIST?  → SÌ → PERMETTI
                         → NO → BLOCCA
```

### Esempio pratico — Google Classroom + blocco YouTube

```
Whitelist: ["*.google.com", "*.googleapis.com", "*.gstatic.com"]
Blacklist: ["youtube.com", "*.youtube.com", "*.ytimg.com", "*.googlevideo.com"]

classroom.google.com  → non in blacklist → in whitelist  → ✅ PERMESSO
drive.google.com      → non in blacklist → in whitelist  → ✅ PERMESSO
youtube.com           → IN BLACKLIST                     → 🚫 BLOCCATO
```

### Supporto wildcard

La whitelist e la blacklist supportano il carattere `*` per i sottodomini:
- `*.google.com` copre `classroom.google.com`, `drive.google.com`, ecc.
- `*.youtube.com` copre `www.youtube.com`, `m.youtube.com`, ecc.

---

## Struttura Firebase Realtime Database

```json
{
  "labs": {
    "room1": {
      "active": true,
      "whitelist": [
        "*.google.com",
        "*.googleapis.com",
        "*.gstatic.com",
        "*.googleusercontent.com",
        "*.kahoot.com",
        "*.kahoot.it",
        "fonts.googleapis.com",
        "fonts.gstatic.com"
      ],
      "blacklist": [
        "youtube.com",
        "*.youtube.com",
        "youtu.be",
        "*.ytimg.com",
        "*.googlevideo.com",
        "*.tiktok.com",
        "*.instagram.com",
        "*.facebook.com"
      ],
      "message": "Oggi sono permessi solo i siti per l'esercitazione"
    }
  }
}
```

Quando `active: false` il proxy viene disabilitato e il traffico torna normale.

---

## Struttura del progetto

```
lab-traffic-control/
│
├── dashboard/                  # Next.js — dashboard docente
│   ├── app/
│   │   ├── page.tsx            # Login
│   │   ├── dashboard/
│   │   │   └── page.tsx        # Pannello principale
│   │   └── api/
│   ├── lib/
│   │   └── firebase.ts         # Config Firebase
│   └── package.json
│
├── agent/                      # Python — agente PC
│   ├── agent.py                # Entry point, servizio Windows
│   ├── proxy_filter.py         # Script mitmproxy (logica di filtraggio)
│   ├── firebase_listener.py    # Ascolta cambiamenti Firebase
│   ├── system_proxy.py         # Gestione registro Windows
│   ├── requirements.txt
│   └── install.bat             # Script installazione come servizio (NSSM)
│
└── README.md
```

---

## Stack tecnologico

| Componente | Tecnologia | Note |
|---|---|---|
| Dashboard | Next.js 14, TypeScript | Deploy su Vercel |
| Auth docente | Firebase Authentication | Email/password |
| Canale controllo | Firebase Realtime Database | Listener real-time |
| Agente PC | Python 3.11+ | |
| Proxy locale | mitmproxy 10+ | Script mode |
| Servizio Windows | NSSM (Non-Sucking Service Manager) | Free, open source |
| Browser support | Chrome, Edge automatico | Firefox: policies.json |

---

## Agente Python — dettaglio implementativo

### agent.py (entry point)
```python
import subprocess, winreg, time
import firebase_admin
from firebase_admin import credentials, db

# 1. Inizializza Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://YOUR_PROJECT.firebaseio.com'
})

# 2. Rileva proxy scolastico dal registro
def get_school_proxy():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        server, _ = winreg.QueryValueEx(key, "ProxyServer")
        enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
        if enabled and server and "127.0.0.1" not in server:
            return server
    except:
        pass
    return None

# 3. Ascolta Firebase
ref = db.reference('/labs/room1')
ref.listen(on_change)
```

### proxy_filter.py (script mitmproxy)
```python
import fnmatch
from mitmproxy import http

# Whitelist e blacklist aggiornate da Firebase listener
state = {"whitelist": [], "blacklist": [], "active": False}

def matches(domain, pattern_list):
    for pattern in pattern_list:
        if fnmatch.fnmatch(domain, pattern):
            return True
    return False

def http_connect(flow: http.HTTPFlow):
    if not state["active"]:
        return  # filtro disabilitato
    
    host = flow.request.host
    
    # Blacklist ha priorità
    if matches(host, state["blacklist"]):
        flow.response = http.Response.make(
            403, b"Sito bloccato dal docente", {"Content-Type": "text/plain"}
        )
        return
    
    # Controlla whitelist
    if not matches(host, state["whitelist"]):
        flow.response = http.Response.make(
            403, b"Sito non presente nella whitelist", {"Content-Type": "text/plain"}
        )
```

### system_proxy.py
```python
import winreg

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

def enable_proxy(address="127.0.0.1:8080"):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, address)
    winreg.CloseKey(key)

def disable_proxy():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
    winreg.CloseKey(key)
```

---

## Dashboard Next.js — funzionalità principali

### Pagina principale
- Selettore laboratorio (es. "Aula 3", "Lab A")
- Toggle ON/OFF filtraggio con feedback visivo
- Editor whitelist: aggiungi/rimuovi domini con supporto wildcard
- Editor blacklist: aggiungi/rimuovi domini con supporto wildcard
- Preset configurazioni (es. "Attiva Kahoot", "Attiva Classroom", "Solo W3Schools")
- Campo messaggio da mostrare agli studenti quando bloccati

### Preset consigliati da creare
```json
"presets": {
  "kahoot": {
    "whitelist": ["*.kahoot.com", "*.kahoot.it", "fonts.googleapis.com", "fonts.gstatic.com"]
  },
  "classroom": {
    "whitelist": ["*.google.com", "*.googleapis.com", "*.gstatic.com", "*.googleusercontent.com"],
    "blacklist": ["youtube.com", "*.youtube.com", "youtu.be", "*.ytimg.com", "*.googlevideo.com"]
  },
  "python_docs": {
    "whitelist": ["docs.python.org", "pypi.org", "*.python.org"]
  },
  "w3schools": {
    "whitelist": ["www.w3schools.com", "*.w3schools.com"]
  }
}
```

---

## Installazione agente sui PC

### Prerequisiti
- Python 3.11+
- NSSM scaricato in `C:\tools\nssm\`
- Firebase service account key

### install.bat
```batch
@echo off
pip install mitmproxy firebase-admin

nssm install LabTrafficAgent python "C:\lab-agent\agent.py"
nssm set LabTrafficAgent AppDirectory "C:\lab-agent"
nssm set LabTrafficAgent Start SERVICE_AUTO_START
nssm start LabTrafficAgent

echo Agente installato e avviato.
pause
```

---

## Firefox — configurazione policy

Creare il file `C:\Program Files\Mozilla Firefox\distribution\policies.json`:
```json
{
  "policies": {
    "Proxy": {
      "Mode": "system"
    }
  }
}
```
Questo forza Firefox a usare le impostazioni proxy di sistema invece delle proprie.

---

## Considerazioni di sicurezza

### Prospettiva realistica

Il sistema non mira alla sicurezza assoluta ma ad **alzare la soglia di difficoltà** abbastanza da scoraggiare la grande maggioranza degli studenti. Nessun sistema di filtraggio scolastico è inviolabile — l'obiettivo è gestire il 95-99% dei casi con il minimo sforzo di configurazione.

La distribuzione realistica in un laboratorio scolastico:
- **~80%** degli studenti segue le regole o non è motivato a aggirarle
- **~15%** prova metodi banali (proxy web, cambiare sito) — bloccati dal sistema
- **~4%** prova estensioni VPN o browser alternativi — bloccati con Chrome Policy e USB disabilitati
- **~1%** conosce strumenti avanzati (Tor, VPN desktop) — scoraggiati dalla lentezza e dalla sorveglianza fisica in aula

---

### Metodi di bypass e contromisure

#### 🟢 Facili (utenti non tecnici)

**Hotspot dal telefono**
Lo studente disconnette il PC dal Wi-Fi scolastico e usa la connessione dati del telefono. Il proxy non ha alcun controllo su un'altra rete.
Contromisura: policy scolastica sui telefoni; bloccare le schede Wi-Fi via Group Policy (`Prohibit use of Internet Connection Sharing`).

**Proxy web online** (hide.me, croxyproxy.com, ecc.)
Se raggiungibili, permettono di navigare liberamente attraverso il sito proxy.
Contromisura: aggiungerli alla blacklist. Sono migliaia, ma i più usati dai ragazzi sono pochi e noti.

**Browser portatile da USB**
Un browser portatile (es. Chrome Portable) non legge le impostazioni proxy di sistema.
Contromisura: disabilitare le porte USB dal BIOS con password, oppure via Group Policy (`Removable Disks: Deny execute access`).

---

#### 🟡 Medie (utenti tecnici)

**Modifica impostazioni proxy**
Un utente admin può semplicemente disabilitare il proxy da Impostazioni → Rete.
Contromisura: **account studenti senza diritti amministratore** — questa è la misura più importante in assoluto.

**Estensioni VPN sul browser** (Browsec, Hola, ecc.)
Tunnelano il traffico aggirando il proxy di sistema, funzionano dentro Chrome.
Contromisura: Chrome Policy per bloccare installazione estensioni non approvate:
```json
// C:\Windows\System32\GroupPolicy\Machine\Registry.pol (via gpedit.msc)
// Computer Configuration → Administrative Templates → Google → Chrome → Extensions
// "Configure extension installation blocklist" = *
// "Configure extension installation allowlist" = [lista estensioni approvate]
```

**Killare il processo agente**
Da Task Manager cercano `python.exe` o `mitmdump.exe` e lo terminano.
Contromisura: servizio installato con account SYSTEM, invisibile a utenti standard. Aggiungere un watchdog che riavvia il processo se viene terminato.

---

#### 🔴 Avanzate (utenti molto tecnici)

**VPN desktop** (ProtonVPN, Windscribe, ecc.)
Crea un tunnel cifrato prima che il traffico raggiunga il proxy. Bypassa completamente il filtraggio.
Contromisura: bloccare le porte VPN più comuni via Windows Firewall:
```powershell
New-NetFirewallRule -DisplayName "Block VPN OpenVPN" -Direction Outbound -Protocol UDP -RemotePort 1194 -Action Block
New-NetFirewallRule -DisplayName "Block VPN PPTP" -Direction Outbound -Protocol TCP -RemotePort 1723 -Action Block
New-NetFirewallRule -DisplayName "Block VPN WireGuard" -Direction Outbound -Protocol UDP -RemotePort 51820 -Action Block
```

**Tor Browser**
Instrada il traffico attraverso una catena di nodi cifrati nel mondo, ignorando il proxy di sistema. Tecnicamente efficace, ma nella pratica ha importanti limitazioni:
- È estremamente lento (tre nodi internazionali): YouTube è inutilizzabile, la navigazione normale è frustrante
- Ha un aspetto visivo riconoscibile — diverso da Chrome/Edge
- Richiede download (~80MB) o esecuzione da USB
- Se USB e diritti admin sono bloccati, è molto difficile da avviare

Contromisura opzionale: bloccare i guard node pubblici di Tor via Firewall. La lista degli IP è pubblica e aggiornabile periodicamente. Non è perfetta (esistono bridge nascosti) ma copre il 95% dei casi:
```powershell
# Script per scaricare e bloccare gli IP dei nodi Tor pubblici
$torNodes = Invoke-RestMethod "https://check.torproject.org/torbulkexitlist"
foreach ($ip in $torNodes -split "`n") {
    if ($ip -match "^\d+\.\d+\.\d+\.\d+$") {
        New-NetFirewallRule -DisplayName "Block Tor $ip" -Direction Outbound -RemoteAddress $ip -Action Block
    }
}
```

---

### Tabella priorità contromisure

| Priorità | Azione | Difficoltà | Impatto |
|---|---|---|---|
| 🔴 Critica | Account studenti senza diritti admin | Bassa | Blocca la maggior parte dei bypass |
| 🔴 Critica | Servizio agente installato come SYSTEM | Bassa | Impedisce kill del processo |
| 🟡 Alta | Chrome Policy — blocco estensioni | Bassa | Blocca VPN browser |
| 🟡 Alta | Disabilitare USB via BIOS/GPO | Bassa | Blocca browser portatili |
| 🟢 Media | Blocco porte VPN via Firewall | Media | Scoraggia VPN desktop |
| 🟢 Bassa | Blocco IP nodi Tor | Media | Scoraggia Tor (già lento di suo) |

---

## Passi di sviluppo consigliati

1. **Setup Firebase** — creare progetto, configurare Realtime DB, ottenere service account key
2. **Agente base** — `agent.py` + `proxy_filter.py` funzionante su un singolo PC
3. **Test filtraggio** — verificare whitelist/blacklist con siti reali
4. **Gestione proxy upstream** — aggiungere rilevamento e configurazione proxy scolastico
5. **Dashboard Next.js** — UI docente con Firebase integration
6. **Deploy Vercel** — dashboard online accessibile da qualsiasi device del docente
7. **Install script** — `install.bat` per deployment su tutti i PC del lab
8. **Firefox policy** — configurare policies.json
9. **Test end-to-end** — simulare una lezione completa
10. **Preset** — costruire la libreria di configurazioni predefinite

---

*Documento generato per il trasferimento del progetto a Claude Code in locale.*
