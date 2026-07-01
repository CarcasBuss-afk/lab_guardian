# Lab Guardian — Agente PC (manuale)

Agente da installare su ogni PC del laboratorio. Filtra il traffico web in base
alle regole decise dal docente nella dashboard, in tempo reale, tramite Firebase.

- **Architettura**: l'agente avvia un proxy locale (mitmproxy) su `127.0.0.1:8080`,
  imposta il proxy di sistema **e aggancia i browser (Chrome/Edge/Firefox) a quel
  proxy tramite policy del browser** (`ProxyMode = fixed_servers`), che ha la
  precedenza sul proxy di sistema/WPAD/PAC: così il filtro regge anche sui PC dove
  un'organizzazione (GPO/MDM) impone un proxy automatico. Filtra le richieste per
  dominio; per HTTPS decide sull'hostname del `CONNECT` **senza decifrare** il
  traffico (nessun certificato da installare).
- **Sicurezza credenziali**: l'agente NON usa la chiave admin. Si autentica come
  account "agente" a privilegi ridotti; le regole del database gli permettono di
  scrivere solo `online`/`lastSeen` del proprio PC.

---

## Indice
1. [Prerequisiti](#1-prerequisiti)
2. [Preparazione una tantum (lato docente)](#2-preparazione-una-tantum-lato-docente)
3. [Build dell'eseguibile](#3-build-delleseguibile)
4. [Contenuto della chiavetta USB](#4-contenuto-della-chiavetta-usb)
5. [Installazione su un PC](#5-installazione-su-un-pc)
6. [Disinstallazione](#6-disinstallazione)
7. [Ripristino di emergenza](#7-ripristino-di-emergenza)
8. [Risoluzione problemi](#8-risoluzione-problemi)
9. [Hardening complementare (checklist IT)](#9-hardening-complementare-checklist-it)

---

## 1. Prerequisiti

- **Sui PC del laboratorio**: Windows 10/11, privilegi di **amministratore** per
  l'installazione (gli studenti restano account **standard**), `nssm.exe`
  ([nssm.cc](https://nssm.cc/)). *Non serve Python*: l'agente è un eseguibile autonomo.
- **Sul PC del docente (per la build)**: Python 3.11+ e i pacchetti in
  `requirements.txt`.

---

## 2. Preparazione una tantum (lato docente)

Da fare **una volta sola**, nell'ordine indicato.

1. **Crea l'account agente** in Firebase → Authentication → Users → *Add user*
   (es. `agent@lab-guardian.local` + password robusta). Sarà usato da tutti i PC.

2. **Assegna il claim docente al tuo account**. Dalla root del progetto:
   ```bash
   node scripts/setTeacherClaim.mjs tua-email-docente@example.com
   ```
   Poi **esci e rientra** nella dashboard (il token va aggiornato).

3. **Pubblica le regole** del database (`database.rules.json`) in console
   (Realtime Database → Rules → incolla → Publish).
   > ⚠️ Esegui prima il punto 2: dopo aver pubblicato queste regole, solo gli
   > account con claim `teacher=true` possono modificare la configurazione. Se le
   > pubblichi prima, ti blocchi fuori dalla dashboard.

---

## 3. Build dell'eseguibile

Sul PC del docente, nella cartella `agent/`:
```bat
build.bat
```
Produce `dist\lab-agent.exe` (eseguibile autonomo, ~50–80 MB).
Rilancia `build.bat` ogni volta che modifichi i sorgenti `.py`.

Prima di copiare su USB, apri **`install.bat`** e compila una volta le costanti
in alto (`APIKEY`, `DBURL`, `AGENTEMAIL`, `AGENTPASS`) con i valori del tuo progetto.
- `APIKEY` = `NEXT_PUBLIC_FIREBASE_API_KEY` (non è un segreto).
- `AGENTEMAIL`/`AGENTPASS` = le credenziali dell'account agente del punto 2.1.

---

## 4. Contenuto della chiavetta USB

```
lab-agent.exe      (da dist\)
nssm.exe
install.bat        (con le costanti già compilate)
uninstall.bat
README.pdf         (questo manuale)
```

---

## 5. Installazione su un PC

1. Inserisci la chiavetta.
2. **Tasto destro su `install.bat` → "Esegui come amministratore"**.
3. Inserisci il **nome dell'aula** quando richiesto (es. `aula3`).
4. Attendi il messaggio "Agente installato e avviato".

L'installer copia tutto in `C:\Program Files\LabGuardian\`, crea `config.json`
(protetto da ACL), registra il servizio **LabGuardianAgent** come SYSTEM (avvio
automatico) e applica proxy, regola firewall anti‑QUIC e policy dei browser.

**Verifica**: entro ~30s il PC compare nella dashboard (pallino verde) nell'aula
scelta. Da quel momento risponde a blocco/sblocco per singolo PC e alle regole
dell'aula.

> **Antivirus**: gli eseguibili PyInstaller possono essere segnalati come falsi
> positivi. Aggiungi un'eccezione per `C:\Program Files\LabGuardian\`.

---

## 6. Disinstallazione

1. **Tasto destro su `uninstall.bat` → "Esegui come amministratore"**.

Lo script ferma il servizio, **ripristina il proxy originale** (incluso un
eventuale proxy scolastico), rimuove la regola firewall e le policy dei browser,
quindi cancella `C:\Program Files\LabGuardian\`.

### Verifica della disinstallazione

Oltre al fatto che la navigazione torna normale, apri un **Prompt dei comandi
come amministratore** e lancia questi controlli:

```cmd
sc query LabGuardianAgent
netsh advfirewall firewall show rule name="LabGuardian Block QUIC (UDP 443)"
reg query "HKLM\SOFTWARE\Policies\Google\Chrome" /v QuicAllowed
```

Risultati attesi (= tutto ripulito):
- `sc query` → errore **1060** ("Il servizio specificato non esiste").
- `netsh ...` → "**Nessuna regola corrisponde** ai criteri specificati".
- `reg query ...` → "**Impossibile trovare** il file/chiave specificato".

Verifica infine che la cartella **`C:\Program Files\LabGuardian`** non esista più.

Se uno di questi controlli non risulta pulito, vedi
[Ripristino di emergenza](#7-ripristino-di-emergenza).

---

## 7. Ripristino di emergenza

Se la disinstallazione automatica fallisce e il PC resta senza Internet (proxy
ancora impostato o firewall in lockdown), esegui questi comandi come
**amministratore** (PowerShell). Ripristinano tutto anche senza l'agente.

1. **Firewall** — riapri l'uscita e togli TUTTE le regole Lab Guardian
   (egress-lockdown + QUIC):
   ```powershell
   Set-NetFirewallProfile -All -DefaultOutboundAction Allow
   Get-NetFirewallRule -DisplayName "LabGuardian*" | Remove-NetFirewallRule -ErrorAction SilentlyContinue
   ```
2. **Proxy di sistema** — disattiva il proxy macchina e le policy:
   ```bat
   reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f
   reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /f
   reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyOverride /f
   reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxySettingsPerUser /f
   reg delete "HKLM\SOFTWARE\Policies\Microsoft\Internet Explorer\Control Panel" /v Proxy /f
   ```
   (Gli errori "valore non trovato" sono normali.)
3. **Policy browser** (facoltativo): elimina `QuicAllowed`/`ProxyMode`/`ProxyServer` in
   `HKLM\SOFTWARE\Policies\Google\Chrome` e `...\Microsoft\Edge`; elimina
   `C:\Program Files\Mozilla Firefox\distribution\policies.json` se contiene solo Proxy.
4. **Rimuovi il servizio** (se ancora presente):
   ```bat
   sc delete LabGuardianAgent
   ```
Poi riapri il browser.

---

## 8. Risoluzione problemi

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| Il PC non compare in dashboard | Credenziali agente errate o niente rete | Controlla `config.json` e `agent.log` in `C:\Program Files\LabGuardian\` |
| "Autenticazione Firebase fallita" nel log | Account agente inesistente o password errata | Verifica l'utente in Authentication |
| Le scritture del docente sono negate | Claim `teacher` mancante | Riesegui `setTeacherClaim.mjs` e rifai login |
| I siti bloccati si aprono lo stesso | QUIC attivo / browser non usa il proxy | Verifica regola firewall UDP 443; su `chrome://policy` deve risultare `ProxyMode = fixed_servers`; riavvia il browser |
| Anche i siti in whitelist non si aprono (PC gestito) | Proxy "gestito dall'organizzazione" che scavalca il nostro | Vedi la sez. 7 di `DIAGNOSTICA-SBLOCCO.txt` (policy browser `fixed_servers`) |
| Nessun sito si apre dopo l'uninstall | Proxy non ripristinato | Vedi [Ripristino di emergenza](#7-ripristino-di-emergenza) |
| L'antivirus blocca l'exe | Falso positivo PyInstaller | Aggiungi eccezione per la cartella di installazione |
| HTTPS dei siti permessi dà errore certificato | Decifratura TLS attiva per errore | Non deve accadere: l'agente fa passthrough TCP. Segnalare con il log |

Log dell'agente: `C:\Program Files\LabGuardian\agent.log`.

---

## 9. Hardening complementare (checklist IT)

L'agente copre il filtraggio web, ma alcune contromisure vanno fatte a parte
(vedi `lab-traffic-control-spec.md` per il dettaglio):

- [x] **Studenti con account non-admin** (la misura più importante).
- [x] Servizio agente come **SYSTEM** (non terminabile dagli studenti).
- [x] **QUIC bloccato** (firewall + policy) — gestito dall'agente.
- [x] **Chiusura browser + pulizia cache all'attivazione del blocco** — gestito
  dall'agente: chiude il buco dei contenuti già in cache e dei giochi PWA offline.
- [ ] **Blocco estensioni** browser (VPN) via policy.
- [ ] **USB disabilitate** (BIOS/GPO) contro i browser portatili.
- [ ] **Porte VPN** bloccate via firewall.
- [ ] Eventuale blocco dei nodi **Tor**.

> Nessun sistema è inviolabile: l'obiettivo è coprire il 95–99% dei casi con
> sforzo minimo, alzando la soglia di difficoltà.
