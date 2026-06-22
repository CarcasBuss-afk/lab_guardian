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
