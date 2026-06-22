// Inizializzazione Firebase Admin SDK (solo lato server)
// Usato dalle API route della dashboard per operazioni con privilegi elevati.

import { initializeApp, getApps, getApp, cert } from "firebase-admin/app";
import { getDatabase } from "firebase-admin/database";

// La private key nelle env var ha i ritorni a capo come "\n" letterali:
// vanno riconvertiti in newline reali prima di passarla al certificato.
const privateKey = process.env.FIREBASE_ADMIN_PRIVATE_KEY?.replace(/\\n/g, "\n");

// Evita doppia inizializzazione (hot reload in sviluppo)
const adminApp =
  getApps().length === 0
    ? initializeApp({
        credential: cert({
          projectId: process.env.FIREBASE_ADMIN_PROJECT_ID,
          clientEmail: process.env.FIREBASE_ADMIN_CLIENT_EMAIL,
          privateKey,
        }),
        databaseURL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
      })
    : getApp();

// Realtime Database con privilegi admin (bypassa le regole di sicurezza)
export const adminRtdb = getDatabase(adminApp);
export default adminApp;
