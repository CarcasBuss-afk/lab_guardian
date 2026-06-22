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
