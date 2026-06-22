# Contesto Progetto — lab-guardian

## Obiettivo
Sistema di controllo del traffico web nei laboratori di informatica scolastici (Lab Traffic Control). Permette al docente di decidere, in tempo reale e da remoto, quali siti web sono accessibili dagli studenti. Dettaglio tecnico completo in [lab-traffic-control-spec.md](lab-traffic-control-spec.md).

## Utenti target
- **Docente**: gestisce le regole di accesso delle aule dalla dashboard web.
- **Studenti**: usano i PC del laboratorio; il traffico è filtrato dall'agente locale.

## Funzionalità principali
- Dashboard docente con login (Firebase Auth).
- Gestione per aula: attiva/disattiva filtro, whitelist e blacklist con wildcard, messaggio agli studenti, preset rapidi.
- **Controllo per singolo PC**: ogni PC può essere `blocked` (bloccato), `free` (libero) o `inherit` (segue le regole dell'aula). L'override del PC ha priorità sulle regole dell'aula.
- Propagazione in tempo reale via Realtime Database verso gli agenti.

## Architettura
```
[Dashboard docente]  ←→  [Firebase Realtime DB]  ←→  [Agente su ogni PC]
  (Next.js/Vercel)         (canale di controllo)      (Python + mitmproxy)
```
- **Database**: Realtime Database (non Firestore) — gli agenti usano listener realtime.
- **Auth**: Firebase Auth email/password. I docenti vengono creati a mano in console.
- **Agente**: usa l'Admin SDK e bypassa le regole del DB. Da realizzare in `agent/`.

## Struttura dati (Realtime Database)
```
/labs/{room}/
  active: boolean            # filtro attivo per l'intera aula
  whitelist: string[]        # domini permessi (wildcard: *.dominio.com)
  blacklist: string[]        # domini bloccati, priorità sulla whitelist
  message: string            # messaggio agli studenti quando un sito è bloccato
  pcs/{hostname}/
    hostname: string
    online: boolean          # mantenuto dall'agente
    lastSeen: number         # timestamp ultimo contatto (opz.)
    override: "blocked" | "free" | "inherit"
```

## Pagine/Route principali
- `/` — Login docente
- `/dashboard` — Pannello di controllo (selettore aula, toggle, liste, messaggio, preset, PC)

## Stato di avanzamento
- [x] Setup Firebase (Realtime DB + Auth + Admin SDK) verificato.
- [x] Dashboard docente (login + pannello aula + controllo per singolo PC).
- [ ] Agente Python (`agent/`).
- [ ] Deploy su Vercel.

## Note
- I segreti (`.env.local`, service account key) non vanno mai committati né deployati (vedi `.vercelignore`).
- Logica di filtraggio: blacklist ha priorità sulla whitelist; override del PC ha priorità sulle regole dell'aula.
