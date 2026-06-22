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
