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
