# Lab Guardian v2 — Gestione sessioni allievi (documento di progettazione)

> Documento di lavoro: raccoglie idee, decisioni e questioni aperte per
> l'estensione di Lab Guardian. **Non è ancora un piano implementativo.**
> Si aggiorna man mano che prendiamo decisioni in fase di brainstorming.

---

## 1. Obiettivo

Estendere Lab Guardian da semplice filtro web a **sistema di gestione delle
sessioni d'aula con identità**. I PC del laboratorio hanno un account Windows
generico e condiviso (nessun account per singolo allievo). Vogliamo che, **solo
quando il docente lo attiva**:

1. all'avvio il PC sia bloccato finché l'allievo non si autentica con il proprio
   **account Google scolastico**;
2. durante la sessione si monitorino **login/logout, file creati e siti
   visitati** (con attenzione ai contenuti pericolosi per minori);
3. a fine giornata (o su comando) **tutti i file prodotti sul PC vengano
   cancellati**, riportando il PC a uno stato pulito.

### Cosa riusiamo dall'attuale Lab Guardian
- **Proxy locale (mitmproxy)** → vede già ogni hostname: base per il log siti.
- **Sincronizzazione Firebase RTDB** → canale di attivazione lato docente.
- **Servizio Windows come SYSTEM** → non terminabile dagli allievi, parte
  all'avvio prima del login.
- **ACL sulla cartella d'installazione** → modello per la cartella di log protetta.
- **Policy browser / firewall / chiusura browser** → già in essere.

---

## 2. Vincolo trasversale: privacy (minori)

Stiamo monitorando **minori** (navigazione, file, orari). Questo è un vincolo di
**design**, non un dettaglio legale a posteriori:

- richiede base giuridica lato istituto (informativa famiglie, regolamento
  d'istituto, eventuale confronto con DPO/Garante);
- **minimizzazione** dei dati raccolti;
- **retention breve** e accesso ristretto al solo docente;
- **trasparenza**: il gate di login dichiara che la sessione è monitorata.

Scelta coerente già presa: **nessun log nel cloud** (vedi §4, Modulo 4). I dati
restano locali sul PC, in cartella protetta. → da gestire comunque retention e
accesso fisico.

---

## 3. Decisioni prese (brainstorming)

| # | Tema | Decisione |
|---|------|-----------|
| D1 | Account Windows | **Nessun account per allievo.** Resta l'utente Windows generico condiviso, con autologon. |
| D2 | Identità allievo | **Google OAuth ristretto al dominio Workspace** della scuola (parametro `hd`). |
| D3 | Reset file | **Ripristino a stato pulito** dell'intero profilo utente generico (baseline + cancellazione del delta), **non** cancellazione selettiva per allievo. |
| D4 | Trigger reset | **Comando del docente**, con esecuzione anche **all'avvio**: se il PC era spento, alla prima accensione esegue la pulizia pendente *prima* di rendere usabile il PC. |
| D5 | Log attività | **Tutti i file e tutti i siti**, salvati in **cartella locale protetta da ACL** (invisibile agli allievi). **Niente Firestore / niente cloud.** |
| D6 | Persistenza log | Il log **non** viene cancellato dal reset di fine giornata: è la traccia, deve sopravvivere. |
| D7 | Vista docente | **Solo live** (chi è loggato, dove, alert siti a rischio in tempo reale). Nessun report storico nel cloud. |
| D8 | Workspace | Confermato uso di Google Workspace con dominio scolastico. In **test** si usa un Firebase/Google Cloud personale; `hd` reale = dominio scuola in produzione. |
| D9 | Architettura processi | **Estendere lab-guardian in monorepo modulare**, NON creare un servizio separato. Un solo **servizio SYSTEM** (enforcer: proxy/filtro, firewall, log siti, watcher file, reset al boot, stato sessione) + una **nuova app UI nella sessione utente** (solo il gate di login). Vincolo decisivo: l'isolamento della **Sessione 0** impedisce a un servizio di mostrare UI → l'app gate è comunque un secondo processo, qualunque scelta. Il servizio sorveglia/rilancia il gate. Comunicazione servizio↔gate: Firebase per stato (login richiesto / chi è loggato) + IPC locale (es. named pipe) per scambi a bassa latenza (dettaglio da definire). |
| D10 | Tecnica del gate | **Overlay** (app fullscreen topmost nella sessione utente), NON kiosk nativo (Shell Launcher v2) né Credential Provider. Motivi: il kiosk nativo richiede edizione Enterprise/Education, **scontra con l'attivazione dinamica** dal docente (config statica dell'OS), alza il **rischio bricking** (shell che crasha = schermo nero) e complica install/dominio — tutto contro i nostri pilastri ("non bloccare mai il PC", attivazione dinamica, install USB semplice). L'overlay gira su qualsiasi edizione, è nativamente dinamico (Firebase) e a basso rischio bricking; in cambio è più debole contro chi è determinato (limiti noti nel Modulo 1). |
| D11 | Sblocco offline | **Password docente locale di emergenza.** Una **sola** password (livello aula) impostata dalla dashboard, distribuita ai PC quando sono online e memorizzata localmente come **hash salato con KDF lento** (PBKDF2/scrypt/argon2) nella cartella ACL. Verificata **offline dal servizio SYSTEM** (l'overlay passa la password digitata via IPC; il segreto non vive mai nel processo utente). Effetti: abbassa **solo il gate** (il filtro web resta attivo), vale **solo per la sessione corrente** (non permanente), la sessione risulta **"non identificata"** nel log ed è sempre loggata; **lockout** dopo N tentativi contro il brute-force. Razionale: è la via di recupero indipendente dalla rete che permette di scegliere fail-closed offline **senza brickare** il PC. |
| D12 | Tecnologia overlay | **App Python fullscreen topmost** (no WebView2). Riusa toolchain/PyInstaller dell'agente. Possibile perché il login NON sta più dentro l'overlay (vedi D13) → niente browser embedded da gestire, quindi la robustezza di un nativo .NET non serve. L'overlay è solo chrome: messaggio, pulsante "Accedi", avviso sessione monitorata, stato, voce discreta "Sblocco docente" (D11). |
| D13 | Flusso OAuth | **System browser + redirect su loopback + PKCE** (RFC 8252). Il **webview embedded è scartato**: Google lo blocca dal 2023 con `disallowed_useragent`, **incluso WebView2**. L'overlay apre il browser di sistema in **modalità app/kiosk** (`--app=URL`, niente barra/schede) sull'URL Google con `hd=dominio`; un listener locale su `127.0.0.1` cattura il code → ID token. Durante il gate il firewall **whitelista solo i domini auth Google + loopback**. La **validazione del JWT** (firma via JWKS Google, `aud`, `exp`, `email_verified`, claim `hd`) la fa il **servizio SYSTEM**, non l'overlay: l'overlay (manomettibile) passa il JWT grezzo via IPC, così un allievo non può falsificare "sono loggato". |
| D14 | Default offline del gate | **Fidarsi dell'ultimo stato noto (cache).** Offline: cache=ON → fail-closed + sblocco con password D11; cache=OFF o nessuna cache (primo avvio, feature opt-in) → PC aperto. Scartato il fail-closed totale offline (chiederebbe la password a ogni avvio offline anche quando la feature non è in uso). Residuo accettato: docente attiva il gate mentre il PC è spento *e* il PC riparte offline → in quel caso il PC è comunque senza internet, il file-watcher logga lo stesso in locale, e il gate compare appena si riconnette. |
| D15 | Mitigazioni gate | Difesa **primaria = watchdog SYSTEM** che rilancia l'overlay nella sessione utente (`CreateProcessAsUser`) entro ~1-2s se ucciso/non in foreground (residuo: finestra di pochi secondi, accettato). Overlay **fullscreen multi-monitor, topmost, senza barra/controlli, con re-assert periodico del foreground**. Policy a supporto: `DisableTaskMgr`, `NoWinKeys`, `HideFastUserSwitching`. **Niente hook tastiera** (fragile, scarso ritorno: ci si affida a `NoWinKeys` + topmost). Premessa che riduce la superficie: logoff/riavvio/"disconnetti" da SAS **non** sono vie di fuga (autologon + gate-al-login li fanno rientrare nel gate); il SAS resta non intercettabile ma innocuo. |

---

## 4. Architettura per moduli

### Modulo 1 — Gate di login (identità)

Modello: l'utente Windows generico fa **autologon**, subito dopo si presenta un
blocco a tutto schermo che richiede il login Google (dominio `hd` ristretto).
Solo dopo l'autenticazione il PC diventa usabile. Attivabile/disattivabile dal
docente via Firebase (come l'attuale blocco).

**Tecnica scelta: overlay** (vedi D10). App fullscreen topmost nella sessione
utente, mostrata/nascosta dinamicamente in base al flag Firebase. Gira su
qualsiasi edizione Windows, basso rischio bricking, coerente con la filosofia
"alziamo l'asticella ~95%".

**Implementazione e login (D12, D13).** L'overlay è un'**app Python fullscreen**
(no WebView2): solo chrome (messaggio, "Accedi", avviso monitoraggio, stato,
"Sblocco docente"). Il login **non** sta nell'overlay — Google blocca i webview
embedded — ma nel **browser di sistema in modalità app** (`--app=URL`), via
OAuth loopback + PKCE; durante il gate il firewall whitelista solo i domini auth
Google + loopback, quindi quella finestra è murata e si chiude da sola dopo il
redirect. Il **servizio SYSTEM** valida il JWT (firma, `aud`, `exp`, claim `hd`)
ricevuto dall'overlay via IPC, così l'esito non è falsificabile dall'allievo.

> **Validato (Spike A)** — `agent/spike_oauth.py` ha dimostrato end-to-end il
> flusso (loopback + PKCE + scambio code) e la validazione del JWT via JWKS, con
> un account Workspace reale (`hd=ciacdidattica.it`).
>
> **Validato (Spike B1)** — `agent/spike_overlay.py`: overlay senza bordi che
> copre **tutti i monitor** (desktop virtuale), re-assert periodico del topmost,
> login integrato (riusa Spike A) con pulsante **Annulla/reset** per non restare
> mai bloccati. Nodo noto rinviato a B2: z-order overlay vs finestra browser
> (l'overlay non-topmost, se cliccato, copre il browser → per ora recuperabile
> con Annulla; soluzione pulita quando il gate sara' lanciato dal servizio).
>
> **Da fare (Spike B2)** — parte dipendente dall'ambiente: servizio SYSTEM che
> lancia l'overlay nella sessione utente (`CreateProcessAsUser`) + watchdog, da
> provare sul PC di laboratorio.

**Limiti noti dell'overlay (da mitigare):**
- vive sopra il desktop, non lo sostituisce → un utente standard può tentare di
  chiuderlo. Mitigazione: Task Manager disabilitato via policy + **watchdog
  SYSTEM** che rilancia il gate (resta una finestra di pochi secondi);
- **Ctrl+Alt+Canc (SAS) non intercettabile**: apre sempre la schermata sicura
  di Windows; si limita via policy (no Task Manager / cambio utente / logoff) ma
  non si elimina;
- Win+Tab / Alt+Tab / Win+D intercettabili con hook tastiera a basso livello ma
  fragili;
- crash overlay / modalità provvisoria = potenziali buchi;
- non protegge da boot USB / altro OS (già accettato nel threat model).

**Scartate** (vedi D10): *Shell Launcher v2* (edizione Enterprise/Education,
scontro con attivazione dinamica, rischio schermo-nero) e *Credential Provider*
(troppo complesso). Analisi completa nella cronologia delle decisioni.

**Dipendenze dalla rete e sblocco offline.** Il gate dipende da **due** canali
cloud, entrambi indisponibili offline: *Firebase* (sa se il gate è attivo / se
il docente l'ha tolto) e *Google* (OAuth + validazione del JWT, che scarica le
chiavi pubbliche). Senza rete l'identità è impossibile → tensione tra "tenere
bloccato" (rischio brick) e "aprire" (gate aggirabile staccando la LAN). La
risolve la **password docente di emergenza (D11)**: via di recupero indipendente
dalla rete che consente fail-closed senza brick. Casi critici coperti: Google
giù (Firebase ok), avvio offline con gate attivo, docente che ha disattivato ma
il PC offline non lo sa, rete che cade durante l'OAuth. *Resta da decidere il
comportamento di default quando il PC è offline e non sa lo stato del gate.*

### Modulo 2 — Monitoraggio sessione
- **login/logout** → eventi con timestamp + macchina + email allievo.
- **file creati** → filesystem watcher sul profilo utente generico. La stessa
  lista alimenta sia il log sia (indirettamente) la verifica del reset.
- Destinazione: **cartella locale protetta** (D5). Stato live minimale su
  Firebase per la vista docente (D7).

### Modulo 3 — Reset di fine giornata
- Modello **baseline + delta sull'intero profilo** `C:\Users\<generico>\` (D3).
  Razionale: un utente standard può scrivere **solo** nel proprio profilo + aree
  temp → scansionando tutto il profilo si coprono anche le "cartelle nascoste".
- **Baseline**: foto dei file presenti al momento della configurazione; il reset
  cancella ciò che non era nel baseline (+ pulizia Temp/cache browser).
- **Trigger** (D4): comando docente → **flag persistente su Firebase**. Il
  servizio SYSTEM, all'avvio, se trova il flag pendente esegue la pulizia
  *prima* di rendere usabile il PC, poi azzera il flag. → copre il caso "PC
  spento, pulizia al primo avvio".
- **Attenzione**: file in uso/lockati se l'autologon è già avvenuto → eseguire
  la pulizia il più presto possibile dal servizio SYSTEM. *Dettaglio da
  approfondire.*
- **Esclusione**: la cartella di log (D6) e i file/cartelle di sistema non vanno
  toccati.
- *Opzione futura*: ripristino a livello disco (tipo Deep Freeze) per coprire
  anche fuori dal profilo. Fuori scope per ora.

### Modulo 4 — Navigazione e contenuti a rischio
- Il proxy **già vede ogni hostname** → log dei siti per sessione (D5: tutti).
- **Categorizzazione** "pericoloso per minori" (adulti, gioco d'azzardo,
  autolesionismo, droghe, violenza…): serve una fonte di categorie (blocklist/
  feed open vs servizio di categorizzazione). *Build vs integrazione: da
  decidere.*
- **Alert live** al docente in dashboard quando si tocca una categoria sensibile
  (D7). Storico solo nel log locale.

---

## 5. Note su backend / dati

- **Live** (chi è loggato, dove, alert correnti) → **Firebase RTDB**, come ora.
- **Storico** (sessioni, file, siti) → **cartella locale protetta sul PC**, non
  cloud (D5). Niente Firestore.
- Il docente consulta lo storico sul PC (o raccolta via USB) — modalità di
  consultazione **da definire**.

---

## 6. Questioni aperte

- [x] Modulo 1: tecnica del gate → **overlay** (vedi D10).
- [x] Modulo 1 — **tecnologia dell'overlay** → app Python fullscreen (D12).
- [x] Modulo 1 — **flusso OAuth** → system browser + loopback PKCE, validazione
      JWT lato servizio (D13).
- [x] Modulo 1 — **sblocco offline** → password docente di emergenza (D11).
- [x] Modulo 1 — **mitigazioni** → watchdog SYSTEM + policy, no hook tastiera (D15).
- [x] Modulo 1 — **policy di default offline** → fidarsi della cache (D14).
- [ ] Modulo 3: gestione file lockati durante la pulizia (timing rispetto
      all'autologon).
- [ ] Modulo 4: fonte di categorizzazione dei contenuti a rischio (open feed vs
      servizio).
- [ ] Formato e modalità di consultazione del log locale da parte del docente.
- [ ] Retention dei log locali (durata, rotazione).
- [ ] Base giuridica / informativa privacy lato istituto (in parallelo).
- [ ] OAuth: configurazione client Google Cloud (test su progetto personale,
      produzione su dominio scolastico).

---

## 7. Limiti noti (consapevoli)
- Nessuna delle misure è inviolabile: come per il filtro web, l'obiettivo è
  coprire il 95–99% dei casi alzando la soglia di difficoltà.
- Boot da USB / altro OS resta fuori portata (solo BIOS lo chiude — rischio già
  accettato).
- **Modalità provvisoria** (safe mode): il servizio potrebbe non partire →
  desktop senza gate. Accettato come limite noto (richiede interrompere il boot,
  livello "avanzato", coerente col boot-USB). Eventuale hardening futuro:
  registrare il servizio per l'avvio anche in safe mode.
- Log completo (tutti i siti per allievo) in locale è una scelta consapevole:
  più dati = più responsabilità di gestione/privacy.
- **Teardown dei blocchi allo spegnimento**: valutato e **scartato**. Inaffidabile
  (spegnimento brutale/crash = non gira; finestra di shutdown limitata), ridondante
  con watchdog 90s + password D11, e aprirebbe una finestra di bypass all'avvio.
  Il "PC spento non resta incastrato" è già garantito alla riaccensione.

---

## 8. Portabilità / migrazione (personale → Workspace scolastico)

**Stato attuale**: si sviluppa sul progetto Firebase/Google Cloud **personale**
(`lab-guardian`), in attesa della liberazione del progetto scolastico (cancellazione
vecchi progetti, ~30 giorni). La migrazione futura al Workspace della scuola deve
restare **meccanica**.

### Regola di design (vincolante)
**Mai valori Google hardcoded nel codice.** Project id, Web API key, database URL,
account agente, **client OAuth** e soprattutto il **dominio `hd`** stanno solo in
file di config/env. Migrare = cambiare il file di config, non il codice.

### Checklist di migrazione (da eseguire quando il progetto scolastico è pronto)
1. **Firebase**: nuovo progetto → abilitare Realtime Database + caricare
   `database.rules.json`, abilitare Auth.
2. **Account/credenziali**: ricreare account **agente** (email/password), account
   **docente** + custom claim (`scripts/setTeacherClaim.mjs`), generare nuova
   **chiave Admin SDK**, prendere la nuova **Web API key**.
3. **OAuth**: nuova schermata di consenso + nuovo **client "App desktop"**
   (come quello creato in test). Su Workspace, se il progetto è creato *dentro*
   l'organizzazione, la consent screen può essere **Interna** → niente utenti di
   test, niente verifica Google, `hd` naturale.
4. **Dati RTDB** (aule, preset, PC): pochi → rifare a mano o export/import.
5. **Agenti sui PC**: rigenerare `config.json` e reinstallare/aggiornare (USB).
   Più tardi si migra, più PC ci sono da toccare.
6. **Config del gate**: aggiornare client OAuth + impostare `hd` = dominio scuola
   (**valore reale noto: `ciacdidattica.it`** — verificato via Spike A nel claim
   `hd` di un account Workspace della scuola).

### Punto Workspace da verificare con l'admin del dominio
⚠️ Le scuole spesso **limitano le app OAuth di terze parti**: l'admin del Workspace
potrebbe dover **autorizzare / marcare come "attendibile"** il nostro client OAuth,
altrimenti il login allievi viene bloccato a livello di organizzazione. Da chiarire
con chi gestisce il dominio **prima** del go-live.
