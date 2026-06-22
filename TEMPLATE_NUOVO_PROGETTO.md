# Template — Nuovo Progetto con Claude Code

> Guida operativa per partire con basi solide su ogni nuovo progetto.
> Stack: Next.js · Firebase · Vercel · Git

---

## Indice

1. [Fase 1 — Creazione progetto e repository](#fase-1--creazione-progetto-e-repository)
2. [Fase 2 — File di configurazione Claude Code](#fase-2--file-di-configurazione-claude-code)
3. [Fase 3 — Plugin e Skill](#fase-3--plugin-e-skill)
4. [Fase 4 — Struttura cartelle standard](#fase-4--struttura-cartelle-standard)
5. [Fase 5 — Configurazione Firebase](#fase-5--configurazione-firebase)
6. [Fase 6 — Configurazione Vercel](#fase-6--configurazione-vercel)
7. [Fase 7 — File base di codice](#fase-7--file-base-di-codice)
8. [Fase 8 — Primo commit e verifica](#fase-8--primo-commit-e-verifica)
9. [Appendice A — CLAUDE.md base](#appendice-a--claudemd-base)
10. [Appendice B — settings.local.json](#appendice-b--settingslocaljson)
11. [Appendice C — PROJECT_CONTEXT.md (template)](#appendice-c--project_contextmd-template)
12. [Appendice D — .gitignore](#appendice-d--gitignore)
13. [Appendice E — .env.local.example](#appendice-e--envlocalexample)
14. [Appendice F — Skill personalizzate](#appendice-f--skill-personalizzate)
15. [Appendice G — firestore.rules base](#appendice-g--firestorerules-base)
16. [Appendice H — File di codice base](#appendice-h--file-di-codice-base)
17. [Appendice I — Script utility](#appendice-i--script-utility)

---

## Fase 1 — Creazione progetto e repository

**Obiettivo**: avere repo e progetto Next.js inizializzati.

**Passi operativi**:

1. Creare il progetto Next.js:
   ```bash
   npx create-next-app@latest nome-progetto --typescript --tailwind --eslint --app --src-dir
   cd nome-progetto
   ```

2. Inizializzare il repository Git (se non già fatto da create-next-app):
   ```bash
   git init
   git remote add origin https://github.com/TUO-USER/nome-progetto.git
   ```

3. Verificare che tutto funzioni:
   ```bash
   npm run dev
   ```

**Risultato atteso**: progetto Next.js funzionante su `localhost:3000` con repo Git collegato.

---

## Fase 2 — File di configurazione Claude Code

**Obiettivo**: Claude Code è configurato e pronto a lavorare con le regole giuste.

**Passi operativi**:

1. **Creare il file `CLAUDE.md`** nella root del progetto — copiare il contenuto dall'[Appendice A](#appendice-a--claudemd-base) e personalizzare il nome del progetto.

2. **Creare la cartella `.claude/`** e il file di blocchi:
   ```bash
   mkdir -p .claude
   ```
   Creare `.claude/settings.local.json` copiando il contenuto dall'[Appendice B](#appendice-b--settingslocaljson).

3. **Creare il file `PROJECT_CONTEXT.md`** nella root — copiare dall'[Appendice C](#appendice-c--project_contextmd-template) e compilare le sezioni.

4. **Creare `.env.local.example`** — copiare dall'[Appendice E](#appendice-e--envlocalexample).

5. **Creare/aggiornare `.gitignore`** — verificare che contenga le voci dell'[Appendice D](#appendice-d--gitignore).

6. **Creare `firestore.rules`** — copiare dall'[Appendice G](#appendice-g--firestorerules-base).

**Risultato atteso**: tutti i file di configurazione sono presenti nella root del progetto.

---

## Fase 3 — Plugin e Skill

**Obiettivo**: avere i plugin essenziali installati e le skill personalizzate attive.

### 3.1 — Plugin core (installare sempre)

Questi tre plugin vanno installati su ogni progetto:

| Plugin | Tipo | Cosa fa |
|--------|------|---------|
| **frontend-design** | Skill (automatica) | Genera UI distintive e di qualità professionale, evitando l'estetica generica da AI |
| **feature-dev** | Slash command (`/feature-dev`) | Guida lo sviluppo strutturato di nuove feature con analisi, piano e implementazione |
| **code-simplifier** | Subagent (automatico) | Analizza e semplifica codice complesso, migliora leggibilità e manutenibilità |

**Comando di installazione**:
```bash
claude plugin install frontend-design
claude plugin install feature-dev
claude plugin install code-simplifier
```

> **Nota**: i plugin skill e subagent si attivano automaticamente quando servono. Il plugin `feature-dev` si attiva con il comando `/feature-dev` durante una sessione Claude Code.

### 3.2 — Skill personalizzate (opzionali ma consigliate)

Creare la cartella per le skill locali:
```bash
mkdir -p .claude/skills
```

Consultare l'[Appendice F](#appendice-f--skill-personalizzate) per il contenuto delle skill. Le skill consigliate sono:

| Skill | File | Quando si attiva |
|-------|------|-----------------|
| **firebase-deploy** | `.claude/skills/firebase-deploy.md` | Prima di ogni deploy — verifica rules, env vars, build |
| **project-setup** | `.claude/skills/project-setup.md` | Al setup iniziale — crea struttura, configura Firebase, prepara env |
| **component-create** | `.claude/skills/component-create.md` | Alla creazione di nuovi componenti — garantisce naming e struttura consistenti |

**Risultato atteso**: plugin installati, cartella skill creata con i file delle skill personalizzate.

---

## Fase 4 — Struttura cartelle standard

**Obiettivo**: avere una struttura consistente tra tutti i progetti.

Creare le cartelle base:
```bash
mkdir -p src/app/api
mkdir -p src/components/ui
mkdir -p src/components/layout
mkdir -p src/components/features
mkdir -p src/lib
mkdir -p src/hooks
mkdir -p src/styles
mkdir -p src/types
mkdir -p public/images
mkdir -p scripts
```

**Mappa delle cartelle**:

```
nome-progetto/
├── CLAUDE.md                    → Regole e workflow per Claude Code
├── PROJECT_CONTEXT.md           → Contesto specifico del progetto
├── firestore.rules              → Regole Firestore (restrittive di default)
├── .claude/
│   ├── settings.local.json      → Blocchi e permessi Claude Code
│   └── skills/                  → Skill personalizzate
│       ├── firebase-deploy.md
│       ├── project-setup.md
│       └── component-create.md
├── .env.local                   → Variabili d'ambiente (NON committare)
├── .env.local.example           → Template variabili (committare)
├── .gitignore
├── scripts/
│   └── clean.sh                 → Reset ambiente di sviluppo
├── src/
│   ├── app/                     → Pagine e route (App Router)
│   │   └── api/                 → API routes
│   ├── components/
│   │   ├── ui/                  → Componenti UI riusabili (Button, Input, Modal...)
│   │   ├── layout/              → Componenti layout (Header, Footer, Sidebar...)
│   │   └── features/            → Componenti specifici per feature
│   ├── lib/
│   │   ├── firebase.ts          → Configurazione e init Firebase
│   │   ├── errors.ts            → Gestione errori centralizzata
│   │   └── utils.ts             → Funzioni utility generiche
│   ├── hooks/                   → Custom React hooks
│   ├── styles/                  → File CSS/Tailwind globali
│   └── types/                   → TypeScript type definitions
├── public/
│   └── images/                  → Asset statici (WebP o PNG)
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

**Risultato atteso**: struttura cartelle creata e pronta all'uso.

---

## Fase 5 — Configurazione Firebase

**Obiettivo**: Firebase inizializzato e collegato al progetto.

**Passi operativi**:

1. Creare il progetto su [Firebase Console](https://console.firebase.google.com/).

2. Attivare i servizi necessari (Firestore, Auth, Storage — secondo necessità).

3. Copiare le credenziali nel file `.env.local` (usa `.env.local.example` come guida).

4. Creare il file di configurazione Firebase:
   ```bash
   # Il file src/lib/firebase.ts verrà creato da Claude Code
   # usando la skill project-setup o manualmente
   ```

5. Installare le dipendenze base:
   ```bash
   npm install firebase clsx tailwind-merge lucide-react
   ```

6. (Opzionale) Installare Firebase Admin per funzioni server-side:
   ```bash
   npm install firebase-admin
   ```

7. Verificare che `firestore.rules` sia presente con regole restrittive (vedi [Appendice G](#appendice-g--firestorerules-base)).

**Risultato atteso**: Firebase configurato, SDK installato, variabili d'ambiente impostate, regole sicure.

---

## Fase 6 — Configurazione Vercel

**Obiettivo**: deploy automatico configurato.

**Passi operativi**:

1. Collegare il repository a [Vercel](https://vercel.com/):
   - Importare il progetto da GitHub
   - Framework preset: Next.js (rilevato automaticamente)

2. Configurare le variabili d'ambiente su Vercel Dashboard:
   - Copiare tutte le variabili da `.env.local`
   - Impostare per gli ambienti appropriati (Production, Preview, Development)

3. Verificare il primo deploy automatico.

**Risultato atteso**: push su `main` → deploy automatico su Vercel.

---

## Fase 7 — File base di codice

**Obiettivo**: avere i file di codice fondamentali già pronti.

**Passi operativi**:

1. **Creare `src/lib/firebase.ts`** — inizializzazione Firebase (vedi [Appendice H.1](#h1--srclibfirebasets)).

2. **Creare `src/lib/utils.ts`** — funzione `cn()` per Tailwind (vedi [Appendice H.2](#h2--srclibhutilsts)).

3. **Creare `src/lib/errors.ts`** — gestione errori centralizzata (vedi [Appendice H.3](#h3--srchliberrorsts)).

4. **Creare `src/components/layout/ErrorBoundary.tsx`** — error boundary React (vedi [Appendice H.4](#h4--srccomponentslayouterrorboundarytsx)).

5. **Creare `scripts/clean.sh`** — script pulizia ambiente (vedi [Appendice I](#appendice-i--script-utility)).

6. Rendere lo script eseguibile:
   ```bash
   chmod +x scripts/clean.sh
   ```

**Risultato atteso**: file base di codice pronti, gestione errori attiva, script utility disponibile.

---

## Fase 8 — Primo commit e verifica

**Obiettivo**: tutto è salvato, versionato e funzionante.

**Checklist finale**:

- [ ] `npm run dev` funziona senza errori
- [ ] `CLAUDE.md` è nella root con workflow e stack compilati
- [ ] `PROJECT_CONTEXT.md` è compilato con obiettivo e contesto del progetto
- [ ] `.claude/settings.local.json` contiene la deny list completa
- [ ] `.env.local` contiene le variabili Firebase (NON committato)
- [ ] `.env.local.example` è presente (committato, senza valori reali)
- [ ] `.gitignore` include `.env.local` e `node_modules`
- [ ] `firestore.rules` è presente con regole restrittive
- [ ] Plugin core installati (frontend-design, feature-dev, code-simplifier)
- [ ] Skill personalizzate nella cartella `.claude/skills/`
- [ ] Struttura cartelle `src/` creata (incluse `api/`, `scripts/`)
- [ ] File base creati (`firebase.ts`, `utils.ts`, `errors.ts`, `ErrorBoundary.tsx`)
- [ ] Script `scripts/clean.sh` presente e eseguibile
- [ ] Firebase SDK e dipendenze base installate
- [ ] Repository collegato a Vercel

**Primo commit**:
```bash
git add .
git commit -m "scaffold: setup iniziale progetto con template Claude Code"
git push -u origin main
```

**Da questo momento sei operativo. Buon lavoro!**

---

## Appendice A — CLAUDE.md base

Copiare questo contenuto nel file `CLAUDE.md` nella root del progetto. Personalizzare il nome del progetto e i placeholder tra parentesi quadre.

```markdown
# Istruzioni per Claude Code

## Flusso di lavoro

1. **L'utente descrive** problema/idea/feature
2. **(Opzionale) Brainstorming** — se richiesto, esploriamo insieme opzioni, pro/contro, architettura. Nessun piano ancora, solo ragionamento libero. Niente codice, niente file, solo idee.
3. **Analisi** — leggo file, studio contesto, faccio domande per chiarire dubbi
4. **Piano** — presento un piano sintetico di cosa intendo fare
5. **Conferma** — aspetto approvazione esplicita ("vai", "procedi", "ok fallo", "implementa")
6. **Implementazione** — lavoro senza fermarmi. Se trovo problemi imprevisti mi fermo e avviso.
7. **Sommario** — presento un riepilogo sintetico. Dettagli solo se richiesti.
8. **Commit/push** — solo su richiesta esplicita dell'utente

**Eccezione**: correzioni banali (typo, commenti, formattazione) vanno dirette senza piano. Nel dubbio, presento comunque il piano.

## Stack tecnologico

- **Progetto**: [NOME PROGETTO]
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS
- **Database**: Firebase Firestore
- **Autenticazione**: Firebase Auth
- **Hosting**: Vercel
- **Repository**: Git + GitHub

## Branch e versioning

- **Branch di lavoro**: `main` (niente feature branch, progetto individuale)
- **Commit**: messaggi in italiano, formato `tipo: descrizione` (es. `feat: aggiunta pagina login`, `fix: corretto errore autenticazione`)
- **Push**: solo su richiesta esplicita dell'utente

## Lingua

- La lingua di default per le conversazioni è l'italiano
- I commenti nel codice devono essere in italiano

## Convenzioni di codice

- Componenti React: PascalCase (es. `UserCard.tsx`)
- Hook personalizzati: camelCase con prefisso "use" (es. `useAuth.ts`)
- Utility e lib: camelCase (es. `formatDate.ts`)
- Tipi TypeScript: PascalCase con suffisso esplicito se necessario (es. `UserType.ts`)
- CSS: Tailwind utility-first, classi custom solo se strettamente necessario
- Immagini: in `public/images/`, formato WebP o PNG, usare il componente `next/image`

## Gestione dipendenze

**Dipendenze approvate** — installabili senza chiedere conferma:
- `firebase`, `firebase-admin`
- `clsx`, `tailwind-merge`
- `lucide-react`

**Tutte le altre dipendenze**: chiedere conferma all'utente prima di installarle, spiegando perché servono e se ci sono alternative già presenti nel progetto.

## Gestione errori

- Usare le utility in `src/lib/errors.ts` per gestione errori consistente
- Wrappare le chiamate Firebase in try/catch
- Loggare errori con `console.error` in sviluppo
- Mai esporre dettagli tecnici degli errori all'utente finale

## Riferimenti

- **Contesto progetto**: consulta [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) per obiettivi, funzionalità e decisioni architetturali
- **Regole Firestore**: consulta [firestore.rules](firestore.rules) prima di modificare la sicurezza del database
```

---

## Appendice B — settings.local.json

Copiare questo contenuto in `.claude/settings.local.json`.

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Edit",
      "Write",
      "MultiEdit",
      "Bash",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(rm -rf /)",
      "Bash(rm -rf /*)",
      "Bash(sudo rm -rf *)",
      "Bash(git push --force*)",
      "Bash(git push * --force*)",
      "Bash(git push -f*)",
      "Bash(git push * -f*)",
      "Bash(> /dev/sda)",
      "Bash(mkfs *)",
      "Bash(dd if=/dev/zero *)",
      "Bash(git reset --hard*)",
      "Bash(git * reset --hard*)",
      "Bash(chmod -R 777 *)",
      "Bash(firebase projects:delete*)",
      "Bash(firebase firestore:delete*)",
      "Bash(vercel rm*)",
      "Bash(vercel remove*)",
      "Bash(DROP DATABASE*)",
      "Bash(DROP TABLE*)",
      "Bash(npx next telemetry enable*)"
    ]
  }
}
```

---

## Appendice C — PROJECT_CONTEXT.md (template)

Copiare questo contenuto in `PROJECT_CONTEXT.md` nella root e compilare i placeholder tra parentesi quadre.

```markdown
# Contesto Progetto — [NOME PROGETTO]

## Obiettivo
[Descrizione in 2-3 frasi di cosa fa il progetto e quale problema risolve]

## Utenti target
[Chi userà questa applicazione? Es: studenti, insegnanti, clienti di un e-commerce...]

## Funzionalità principali
- [Feature 1]
- [Feature 2]
- [Feature 3]

## Priorità (MVP)
[Quali funzionalità sono essenziali per la prima versione? Elencare in ordine di priorità.
Tutto il resto è "nice to have" — Claude Code non deve proporlo spontaneamente.]

## Stile e design
- **Tono**: [formale / informale / educativo / professionale]
- **Stile visivo**: [minimal / colorato / moderno / classico]
- **Colori principali**: [es. blu #3B82F6, bianco, grigio chiaro — oppure "da definire"]
- **Riferimenti**: [siti o app con uno stile simile a quello desiderato, se presenti]

## Decisioni architetturali
[Scelte importanti già prese. Es: "Autenticazione solo con Google", "Dati tutti su Firestore, niente API esterne", ecc.]

## Struttura dati (Firestore)
[Collezioni principali e relazioni. Es:]
- `users/` — profili utente
- `projects/` — progetti creati dagli utenti

## Pagine/Route principali
- `/` — Homepage
- `/dashboard` — Dashboard utente
- `/auth` — Login/Registrazione

## Endpoint API
[Elenco delle API routes man mano che vengono create. Es:]
- `GET /api/users` — lista utenti
- `POST /api/projects` — crea nuovo progetto

[Aggiornare questa sezione ogni volta che si aggiunge un endpoint.]

## Note
[Qualsiasi altra informazione utile per Claude Code]
```

---

## Appendice D — .gitignore

Verificare che il `.gitignore` contenga almeno queste voci (molte sono già presenti dal template Next.js):

```gitignore
# Dipendenze
node_modules/

# Build
.next/
out/

# Ambiente
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Sistema
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Firebase
.firebase/
firebase-debug.log
firestore-debug.log

# Vercel
.vercel/

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# TypeScript
*.tsbuildinfo
next-env.d.ts
```

---

## Appendice E — .env.local.example

Copiare in `.env.local.example`. **Non inserire valori reali in questo file** — serve solo come promemoria delle variabili necessarie.

```env
# Firebase — Client SDK
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# Firebase — Admin SDK (opzionale, solo se servono API server-side)
FIREBASE_ADMIN_PROJECT_ID=
FIREBASE_ADMIN_CLIENT_EMAIL=
FIREBASE_ADMIN_PRIVATE_KEY=
```

---

## Appendice F — Skill personalizzate

### F.1 — firebase-deploy.md

Creare il file `.claude/skills/firebase-deploy.md`:

```markdown
# Skill: Firebase Deploy Sicuro

## Quando si attiva
Prima di ogni deploy su Firebase o Vercel, o quando l'utente chiede di "deployare", "mettere in produzione", "pushare live".

## Procedura obbligatoria

### 1. Verifica Firestore Rules
- Leggere `firestore.rules`
- Controllare che NON ci siano regole `allow read, write: if true` in produzione
- Segnalare regole troppo permissive
- Se le rules sono ancora quelle di default (tutto bloccato), chiedere all'utente se è intenzionale

### 2. Verifica variabili d'ambiente
- Controllare che tutte le variabili in `.env.local.example` siano configurate su Vercel
- Verificare che `.env.local` NON sia nel repository (controllare `.gitignore`)

### 3. Verifica build
- Eseguire `npm run build` e verificare che non ci siano errori
- Controllare eventuali warning significativi

### 4. Pulizia codice
- Verificare che non ci siano `console.log` di debug nel codice di produzione
- Controllare che non ci siano TODO critici rimasti

### 5. Checklist pre-deploy
- [ ] Firestore Rules verificate e sicure
- [ ] Variabili d'ambiente configurate su Vercel
- [ ] Build senza errori
- [ ] Nessun `console.log` di debug
- [ ] File `.env.local` non committato
- [ ] Error boundary attivo nel layout

### 6. Procedi
Solo dopo aver verificato tutti i punti, procedere con il deploy.
```

### F.2 — project-setup.md

Creare il file `.claude/skills/project-setup.md`:

```markdown
# Skill: Setup Iniziale Progetto

## Quando si attiva
Quando l'utente chiede di "inizializzare il progetto", "configurare Firebase", "preparare il progetto".

## Procedura

### 1. Struttura cartelle
Creare tutte le cartelle standard:
- `src/app/api/`
- `src/components/ui/`, `src/components/layout/`, `src/components/features/`
- `src/lib/`, `src/hooks/`, `src/styles/`, `src/types/`
- `public/images/`
- `scripts/`

### 2. File Firebase (`src/lib/firebase.ts`)
Creare il file di inizializzazione Firebase con:
- Import da `firebase/app`
- Configurazione da variabili d'ambiente `NEXT_PUBLIC_FIREBASE_*`
- Export di `app`, `db` (Firestore), `auth` (se necessario)
- Controllo `getApps().length` per evitare doppia inizializzazione

### 3. File utility (`src/lib/utils.ts`)
Creare con funzioni base:
- `cn()` per merge classi Tailwind (con `clsx` e `tailwind-merge`)

### 4. File errori (`src/lib/errors.ts`)
Creare con:
- Classe `AppError` personalizzata
- Funzione `handleError()` per gestione centralizzata
- Funzione `getErrorMessage()` per messaggi user-friendly
- Mapping errori Firebase in italiano

### 5. Error Boundary (`src/components/layout/ErrorBoundary.tsx`)
Creare un error boundary React che:
- Cattura errori nel render tree
- Mostra un messaggio user-friendly in italiano
- Logga l'errore in console
- Ha pulsante "Riprova"

### 6. Layout base (`src/app/layout.tsx`)
Verificare che il layout root abbia:
- Metadata base configurata
- Font configurato
- ErrorBoundary wrappato attorno ai children

### 7. Script utility (`scripts/clean.sh`)
Creare lo script di pulizia e renderlo eseguibile con `chmod +x`.

### 8. Installazione dipendenze
```bash
npm install firebase clsx tailwind-merge lucide-react
```
```

### F.3 — component-create.md

Creare il file `.claude/skills/component-create.md`:

```markdown
# Skill: Creazione Componenti

## Quando si attiva
Quando l'utente chiede di "creare un componente", "aggiungere un componente", "fare un nuovo componente".

## Convenzioni

### Naming
- File: PascalCase (es. `UserCard.tsx`)
- Cartella di destinazione:
  - UI generico (Button, Input, Modal) → `src/components/ui/`
  - Layout (Header, Footer, Sidebar) → `src/components/layout/`
  - Specifico per feature → `src/components/features/`

### Struttura del file
```tsx
// Descrizione breve del componente in italiano

interface NomeComponenteProps {
  // Props con tipi espliciti
}

export default function NomeComponente({ ...props }: NomeComponenteProps) {
  return (
    // JSX
  );
}
```

### Regole
- Sempre TypeScript con interfaccia Props esplicita
- Sempre `export default function` (non arrow function export)
- Commenti in italiano
- Styling con Tailwind utility classes
- Immagini con il componente `next/image`, formato WebP o PNG
- Se il componente ha stato complesso, estrarre la logica in un custom hook in `src/hooks/`
- Se il componente ha più di 150 righe, valutare se spezzarlo in sotto-componenti
- Usare `handleError()` da `src/lib/errors.ts` per la gestione errori
```

---

## Appendice G — firestore.rules base

Creare il file `firestore.rules` nella root del progetto. Queste regole **bloccano tutto di default** — aprire solo le collezioni necessarie man mano che il progetto cresce.

```
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {

    // ⛔ REGOLA DI DEFAULT: tutto bloccato
    // Non rimuovere mai questa regola. Serve come rete di sicurezza.
    match /{document=**} {
      allow read, write: if false;
    }

    // ✅ Esempio: collezione "users" — ogni utente legge/scrive solo i propri dati
    // Decommentare e adattare quando serve:
    //
    // match /users/{userId} {
    //   allow read: if request.auth != null && request.auth.uid == userId;
    //   allow create: if request.auth != null && request.auth.uid == userId;
    //   allow update: if request.auth != null && request.auth.uid == userId;
    //   allow delete: if false; // gli utenti non possono cancellarsi da soli
    // }

    // ✅ Esempio: collezione pubblica in sola lettura
    // Decommentare e adattare quando serve:
    //
    // match /public/{docId} {
    //   allow read: if true;
    //   allow write: if request.auth != null && request.auth.token.admin == true;
    // }

    // ✅ Esempio: collezione con dati condivisi tra utenti autenticati
    // Decommentare e adattare quando serve:
    //
    // match /projects/{projectId} {
    //   allow read: if request.auth != null;
    //   allow create: if request.auth != null;
    //   allow update: if request.auth != null && resource.data.ownerId == request.auth.uid;
    //   allow delete: if request.auth != null && resource.data.ownerId == request.auth.uid;
    // }
  }
}
```

> **Regola d'oro**: chiudi tutto di default, apri solo quello che serve. Mai usare `allow read, write: if true` in produzione.

---

## Appendice H — File di codice base

### H.1 — `src/lib/firebase.ts`

```typescript
// Inizializzazione e configurazione Firebase

import { initializeApp, getApps, getApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Evita doppia inizializzazione in sviluppo (hot reload)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

export const db = getFirestore(app);
export const auth = getAuth(app);
export default app;
```

### H.2 — `src/lib/utils.ts`

```typescript
// Funzioni utility generiche

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge classi Tailwind in modo sicuro.
 * Combina clsx (condizionali) con tailwind-merge (risoluzione conflitti).
 *
 * Esempio: cn("px-4 py-2", isActive && "bg-blue-500", "px-6")
 * Risultato: "py-2 px-6 bg-blue-500" (px-6 sovrascrive px-4)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### H.3 — `src/lib/errors.ts`

```typescript
// Gestione errori centralizzata

/**
 * Errore personalizzato dell'applicazione.
 * Aggiunge un codice errore e un messaggio user-friendly.
 */
export class AppError extends Error {
  constructor(
    message: string,
    public code: string = "GENERIC_ERROR",
    public userMessage: string = "Si è verificato un errore. Riprova più tardi."
  ) {
    super(message);
    this.name = "AppError";
  }
}

/**
 * Gestisce un errore in modo centralizzato.
 * Logga in console e restituisce un messaggio sicuro per l'utente.
 */
export function handleError(error: unknown): string {
  // Errore personalizzato — usiamo il messaggio user-friendly
  if (error instanceof AppError) {
    console.error(`[${error.code}] ${error.message}`);
    return error.userMessage;
  }

  // Errore Firebase — mappiamo i codici più comuni
  if (error instanceof Error && "code" in error) {
    const firebaseCode = (error as { code: string }).code;
    console.error(`[Firebase: ${firebaseCode}] ${error.message}`);
    return mapFirebaseError(firebaseCode);
  }

  // Errore generico
  if (error instanceof Error) {
    console.error(`[Errore] ${error.message}`);
    return "Si è verificato un errore imprevisto.";
  }

  // Fallback per errori non standard
  console.error("[Errore sconosciuto]", error);
  return "Si è verificato un errore imprevisto.";
}

/**
 * Mappa i codici errore Firebase in messaggi comprensibili per l'utente.
 */
function mapFirebaseError(code: string): string {
  const errorMap: Record<string, string> = {
    "auth/user-not-found": "Utente non trovato.",
    "auth/wrong-password": "Password non corretta.",
    "auth/email-already-in-use": "Questa email è già registrata.",
    "auth/weak-password": "La password è troppo debole.",
    "auth/invalid-email": "Indirizzo email non valido.",
    "auth/too-many-requests": "Troppi tentativi. Riprova tra qualche minuto.",
    "permission-denied": "Non hai i permessi per questa operazione.",
    "not-found": "Risorsa non trovata.",
    "unavailable": "Servizio temporaneamente non disponibile. Riprova.",
  };

  return errorMap[code] || "Si è verificato un errore. Riprova più tardi.";
}

/**
 * Estrae il messaggio da un errore di tipo sconosciuto.
 * Utile nei blocchi catch dove error è di tipo `unknown`.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  return "Errore sconosciuto";
}
```

### H.4 — `src/components/layout/ErrorBoundary.tsx`

```tsx
"use client";

// Error boundary per catturare errori nel render tree di React

import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary] Errore catturato:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Se è stato passato un fallback personalizzato, usalo
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Fallback di default
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center">
          <h2 className="mb-2 text-xl font-semibold text-gray-800">
            Qualcosa è andato storto
          </h2>
          <p className="mb-4 text-gray-600">
            Si è verificato un errore imprevisto. Prova a ricaricare la pagina.
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
          >
            Riprova
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## Appendice I — Script utility

### `scripts/clean.sh`

Creare il file `scripts/clean.sh` e renderlo eseguibile con `chmod +x scripts/clean.sh`.

```bash
#!/bin/bash

# Script di pulizia ambiente di sviluppo
# Uso: ./scripts/clean.sh
# Rimuove cache, node_modules e reinstalla tutto da zero.
# Utile quando Next.js si inceppa o ci sono problemi con le dipendenze.

echo "🧹 Pulizia ambiente in corso..."

# Rimuove cache Next.js
if [ -d ".next" ]; then
  rm -rf .next
  echo "  ✓ Cache .next rimossa"
fi

# Rimuove node_modules
if [ -d "node_modules" ]; then
  rm -rf node_modules
  echo "  ✓ node_modules rimossi"
fi

# Reinstalla dipendenze
if [ -f "package-lock.json" ]; then
  echo "  ✓ Reinstallazione dipendenze..."
  npm install
else
  echo "  ⚠ package-lock.json non trovato, esegui npm install manualmente"
fi

echo ""
echo "✅ Pulizia completata! Avvia il progetto con: npm run dev"
```

---

> **Ultimo aggiornamento**: febbraio 2026
> **Versione template**: 2.0
