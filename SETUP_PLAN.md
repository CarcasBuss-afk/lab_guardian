# Piano di Setup — Nuovo Progetto

> **Questo file è per Claude Code.** Contiene le istruzioni per inizializzare un nuovo progetto partendo dal repo template.
>
> **Come usarlo**: apri Claude Code e scrivi:
> `"Segui SETUP_PLAN.md per inizializzare il progetto '[NOME]'"`
>
> Claude Code leggerà questo file ed eseguirà tutti i passi in ordine.

---

## Informazioni richieste

Prima di iniziare, Claude Code deve chiedere all'utente queste informazioni:

1. **Nome del progetto** (es. "il-mio-sito", "educode", "portale-scuola")
2. **Descrizione breve** — cosa fa il progetto in 1-2 frasi
3. **Servizi Firebase necessari** — quali tra: Firestore, Auth, Storage (default: Firestore + Auth)
4. **Serve Firebase Admin SDK?** — sì/no (default: no)

Queste informazioni verranno usate per compilare i placeholder nei file del template.

---

## Fase 1 — Configurazione Claude Code (PRIORITÀ MASSIMA)

Questa fase va eseguita **prima di qualsiasi altra operazione**. Senza questi file, Claude Code chiede permessi per ogni singolo comando e il setup diventa inutilizzabile.

### 1.1 — Creare `.claude/settings.local.json`

Se il file non esiste già, crearlo:

```bash
mkdir -p .claude
```

Creare `.claude/settings.local.json` con questo contenuto esatto:

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

### 1.2 — Creare le skill personalizzate

Se la cartella `.claude/skills/` non esiste, crearla:

```bash
mkdir -p .claude/skills
```

Verificare che esistano questi tre file. Se mancano, crearli:

**`.claude/skills/firebase-deploy.md`**:
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

**`.claude/skills/project-setup.md`**:
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
npm install firebase clsx tailwind-merge lucide-react
```

**`.claude/skills/component-create.md`**:
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
- Sempre TypeScript con interfaccia Props esplicita
- Sempre `export default function` (non arrow function export)
- Commenti in italiano
- Styling con Tailwind utility classes
- Immagini con il componente `next/image`, formato WebP o PNG
- Se il componente ha stato complesso, estrarre la logica in un custom hook in `src/hooks/`
- Se il componente ha più di 150 righe, valutare se spezzarlo in sotto-componenti
- Usare `handleError()` da `src/lib/errors.ts` per la gestione errori
```

### 1.3 — Verifica

Controllare che questi file esistano:
- [ ] `.claude/settings.local.json`
- [ ] `.claude/skills/firebase-deploy.md`
- [ ] `.claude/skills/project-setup.md`
- [ ] `.claude/skills/component-create.md`

**Solo dopo questa verifica procedere con la Fase 2.**

---

## Fase 2 — Inizializzazione Next.js

Eseguire dalla cartella corrente (il repo template clonato):

```bash
# Crea il progetto Next.js nella cartella temporanea
npx create-next-app@latest temp-next --typescript --tailwind --eslint --app --src-dir --no-git

# Sposta tutto il contenuto di temp-next nella root, senza sovrascrivere i file del template
# I file del template hanno la priorità
cp -rn temp-next/* .
cp -rn temp-next/.* . 2>/dev/null

# Rimuovi la cartella temporanea
rm -rf temp-next
```

**Verifica**: `package.json` e `tsconfig.json` devono essere presenti nella root.

---

## Fase 3 — Compilazione placeholder

Sostituire i placeholder nei file del template con le informazioni fornite dall'utente.

### 2.1 — CLAUDE.md
Aprire `CLAUDE.md` e sostituire:
- `[NOME PROGETTO]` → nome del progetto fornito dall'utente

### 2.2 — PROJECT_CONTEXT.md
Aprire `PROJECT_CONTEXT.md` e sostituire:
- `[NOME PROGETTO]` → nome del progetto
- `[Descrizione in 2-3 frasi di cosa fa il progetto e quale problema risolve]` → descrizione fornita dall'utente

Le altre sezioni (Utenti target, Funzionalità, Priorità, Stile, ecc.) vanno lasciate con i placeholder — l'utente le compilerà in seguito.

---

## Fase 4 — Struttura cartelle

Creare le cartelle che Next.js non crea di default:

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
```

La cartella `scripts/` e `.claude/skills/` sono già state create nella Fase 1.

**Verifica**: tutte le cartelle nella mappa del progetto devono esistere.

---

## Fase 5 — Installazione dipendenze

### 4.1 — Dipendenze base (sempre)
```bash
npm install firebase clsx tailwind-merge lucide-react
```

### 4.2 — Firebase Admin (solo se richiesto dall'utente)
```bash
npm install firebase-admin
```

**Non installare altre dipendenze** senza conferma esplicita dell'utente.

---

## Fase 6 — Creazione file di codice base

Creare i seguenti file con il contenuto specificato. I commenti devono essere in italiano.

### 5.1 — `src/lib/firebase.ts`

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

> **Nota**: se l'utente NON ha richiesto Firebase Auth, rimuovere le righe relative a `getAuth` e `auth`.
> Se l'utente ha richiesto Firebase Storage, aggiungere `import { getStorage } from "firebase/storage"` e `export const storage = getStorage(app)`.

### 5.2 — `src/lib/utils.ts`

```typescript
// Funzioni utility generiche

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge classi Tailwind in modo sicuro.
 * Combina clsx (condizionali) con tailwind-merge (risoluzione conflitti).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 5.3 — `src/lib/errors.ts`

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
  if (error instanceof AppError) {
    console.error(`[${error.code}] ${error.message}`);
    return error.userMessage;
  }

  if (error instanceof Error && "code" in error) {
    const firebaseCode = (error as { code: string }).code;
    console.error(`[Firebase: ${firebaseCode}] ${error.message}`);
    return mapFirebaseError(firebaseCode);
  }

  if (error instanceof Error) {
    console.error(`[Errore] ${error.message}`);
    return "Si è verificato un errore imprevisto.";
  }

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

### 5.4 — `src/components/layout/ErrorBoundary.tsx`

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
      if (this.props.fallback) {
        return this.props.fallback;
      }

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

## Fase 7 — Configurazione layout con ErrorBoundary

Modificare il file `src/app/layout.tsx` generato da Next.js per wrappare i children con l'ErrorBoundary:

- Aggiungere l'import: `import ErrorBoundary from "@/components/layout/ErrorBoundary";`
- Wrappare `{children}` con `<ErrorBoundary>{children}</ErrorBoundary>`
- Aggiornare i metadata con il nome del progetto fornito dall'utente

---

## Fase 8 — Permessi script

```bash
chmod +x scripts/clean.sh
```

---

## Fase 9 — Verifica finale

Eseguire questi controlli prima di dichiarare il setup completato:

```bash
# Verifica che il progetto compili
npm run build
```

Se la build ha errori, correggerli prima di procedere.

**Checklist** — verificare che tutti questi file/cartelle esistano:

- [ ] `CLAUDE.md` — con nome progetto compilato
- [ ] `PROJECT_CONTEXT.md` — con nome e descrizione compilati
- [ ] `.claude/settings.local.json` — deny list presente
- [ ] `.claude/skills/firebase-deploy.md`
- [ ] `.claude/skills/project-setup.md`
- [ ] `.claude/skills/component-create.md`
- [ ] `.env.local.example`
- [ ] `.gitignore`
- [ ] `firestore.rules`
- [ ] `scripts/clean.sh` — eseguibile
- [ ] `src/lib/firebase.ts`
- [ ] `src/lib/utils.ts`
- [ ] `src/lib/errors.ts`
- [ ] `src/components/layout/ErrorBoundary.tsx`
- [ ] `src/app/layout.tsx` — con ErrorBoundary wrappato
- [ ] Tutte le cartelle standard create
- [ ] `npm run build` senza errori

---

## Fase 10 — Pulizia e sommario

1. **Rimuovere questo file** (`SETUP_PLAN.md`) dal progetto — ha esaurito il suo scopo:
   ```bash
   rm SETUP_PLAN.md
   ```

2. **Rimuovere `TEMPLATE_NUOVO_PROGETTO.md`** se presente — è la guida di riferimento, non serve nel progetto finale:
   ```bash
   rm -f TEMPLATE_NUOVO_PROGETTO.md
   ```

3. **Presentare il sommario** all'utente con:
   - Conferma che il setup è completato
   - Elenco dei file creati
   - Prossimi passi consigliati:
     - Compilare le sezioni rimanenti di `PROJECT_CONTEXT.md`
     - Creare il progetto Firebase e inserire le credenziali in `.env.local`
     - Collegare il repository a Vercel
     - Installare i plugin Claude Code: `claude plugin install frontend-design feature-dev code-simplifier`
   - Ricordare che il primo commit va fatto con: `git add . && git commit -m "scaffold: setup iniziale progetto [NOME]"`

---

## Note per Claude Code

- **Lingua**: tutte le comunicazioni con l'utente devono essere in italiano
- **Commenti nel codice**: in italiano
- **Non chiedere conferma** per ogni singolo passo — esegui tutto in sequenza. Fermati solo se c'è un errore o se serve un'informazione che non hai
- **Non installare dipendenze extra** oltre a quelle specificate (firebase, clsx, tailwind-merge, lucide-react + opzionalmente firebase-admin)
- **Se qualcosa fallisce**: fermati, spiega l'errore, proponi una soluzione e aspetta conferma
