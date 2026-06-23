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
- [ ] Modulo 1 — **tecnologia dell'overlay**: con cosa lo costruiamo (es.
      finestra WebView2 per ospitare il login Google, dato che OAuth gira meglio
      in un browser embedded) e in che linguaggio, visto che il resto
      dell'agente è in Python.
- [ ] Modulo 1 — **flusso OAuth**: come l'overlay autentica con Google
      `hd`-ristretto e come comunica l'esito al servizio (Firebase vs IPC locale).
- [ ] Modulo 1 — **mitigazioni**: quali policy/hook attivare (anti Task Manager/
      SAS, hook tastiera) e come il watchdog SYSTEM rilancia il gate.
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
- Log completo (tutti i siti per allievo) in locale è una scelta consapevole:
  più dati = più responsabilità di gestione/privacy.
