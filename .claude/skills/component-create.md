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
