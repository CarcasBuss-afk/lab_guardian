// Imposta il custom claim "teacher=true" su un account docente.
// Serve perché le regole del database concedono la scrittura della configurazione
// solo agli utenti con questo claim (i docenti), distinguendoli dall'account agente.
//
// Uso (dalla root del progetto):
//   node scripts/setTeacherClaim.mjs docente@email.it
//
// Implementazione: chiama direttamente le API REST di Google Identity Toolkit
// autenticandosi con la chiave del service account. Usa solo moduli nativi di
// Node (crypto + fetch), così da NON dipendere da firebase-admin (che ha un
// conflitto jose/jwks-rsa quando si carica il modulo auth).
//
// Richiede la chiave admin (service account JSON) in locale: percorso in
// GOOGLE_APPLICATION_CREDENTIALS, altrimenti il file di default nella root.

import { readFileSync } from "node:fs";
import { createSign } from "node:crypto";

const email = process.argv[2];
if (!email) {
  console.error("Uso: node scripts/setTeacherClaim.mjs <email-docente>");
  process.exit(1);
}

const keyPath =
  process.env.GOOGLE_APPLICATION_CREDENTIALS ||
  "./lab-guardian-firebase-adminsdk-fbsvc-203d0f2496.json";

let sa;
try {
  sa = JSON.parse(readFileSync(keyPath, "utf-8"));
} catch (err) {
  console.error(`Impossibile leggere la chiave admin (${keyPath}):`, err.message);
  process.exit(1);
}

// Codifica base64url (senza padding)
function b64url(input) {
  return Buffer.from(input)
    .toString("base64")
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

// Genera un access token OAuth2 firmando un JWT con la chiave del service account
async function getAccessToken() {
  const now = Math.floor(Date.now() / 1000);
  const tokenUri = sa.token_uri || "https://oauth2.googleapis.com/token";
  const header = b64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const claims = b64url(
    JSON.stringify({
      iss: sa.client_email,
      scope: "https://www.googleapis.com/auth/identitytoolkit",
      aud: tokenUri,
      iat: now,
      exp: now + 3600,
    })
  );
  const unsigned = `${header}.${claims}`;
  const signature = createSign("RSA-SHA256")
    .update(unsigned)
    .sign(sa.private_key, "base64")
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
  const jwt = `${unsigned}.${signature}`;

  const resp = await fetch(tokenUri, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwt,
    }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(`OAuth fallito: ${JSON.stringify(data)}`);
  return data.access_token;
}

async function callIdentityToolkit(method, token, body) {
  const resp = await fetch(`https://identitytoolkit.googleapis.com/v1/${method}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(`${method} fallito: ${JSON.stringify(data)}`);
  return data;
}

try {
  const token = await getAccessToken();

  // Trova l'utente per email
  const lookup = await callIdentityToolkit("accounts:lookup", token, { email: [email] });
  const user = lookup.users && lookup.users[0];
  if (!user) {
    console.error(`Nessun utente con email ${email} (crealo prima in Authentication).`);
    process.exit(1);
  }

  // Imposta il custom claim teacher=true
  await callIdentityToolkit("accounts:update", token, {
    localId: user.localId,
    customAttributes: JSON.stringify({ teacher: true }),
  });

  console.log(`OK: claim teacher=true impostato per ${email} (uid ${user.localId}).`);
  console.log("Esci e rientra nella dashboard per aggiornare il token.");
  process.exit(0);
} catch (err) {
  console.error("Errore:", err.message);
  process.exit(1);
}
