// Layer dati per il canale di controllo (Realtime Database, lato client).
// Tutte le scritture passano dalle regole di sicurezza: richiedono docente autenticato.

import {
  ref,
  onValue,
  set,
  update,
  remove,
  get,
  type Unsubscribe,
} from "firebase/database";
import { rtdb } from "@/lib/firebase";
import { DEFAULT_LAB_CONFIG } from "@/types/lab";
import type { LabConfig, PcConfig, PcOverride } from "@/types/lab";
import type { Preset } from "@/lib/presets";

// Percorso del nodo di un'aula
function labPath(room: string): string {
  return `labs/${room}`;
}

// Elenco una tantum delle aule esistenti
export async function listLabs(): Promise<string[]> {
  const snapshot = await get(ref(rtdb, "labs"));
  if (!snapshot.exists()) return [];
  return Object.keys(snapshot.val() as Record<string, unknown>);
}

// Crea un'aula con la configurazione di default (se non esiste già)
export async function createLab(room: string): Promise<void> {
  const labRef = ref(rtdb, labPath(room));
  const snapshot = await get(labRef);
  if (snapshot.exists()) return;
  await set(labRef, DEFAULT_LAB_CONFIG);
}

// Ascolta in tempo reale la configurazione di un'aula.
// Restituisce la funzione per annullare la sottoscrizione.
export function subscribeLab(
  room: string,
  callback: (config: LabConfig | null) => void
): Unsubscribe {
  const labRef = ref(rtdb, labPath(room));
  return onValue(labRef, (snapshot) => {
    callback(snapshot.exists() ? (snapshot.val() as LabConfig) : null);
  });
}

// Attiva/disattiva il filtro per l'intera aula
export async function setActive(room: string, active: boolean): Promise<void> {
  await update(ref(rtdb, labPath(room)), { active });
}

// Sovrascrive la whitelist dell'aula
export async function setWhitelist(room: string, whitelist: string[]): Promise<void> {
  await update(ref(rtdb, labPath(room)), { whitelist });
}

// Sovrascrive la blacklist dell'aula
export async function setBlacklist(room: string, blacklist: string[]): Promise<void> {
  await update(ref(rtdb, labPath(room)), { blacklist });
}

// Aggiorna il messaggio mostrato agli studenti
export async function setMessage(room: string, message: string): Promise<void> {
  await update(ref(rtdb, labPath(room)), { message });
}

// Applica un preset: sovrascrive solo le liste definite nel preset
export async function applyPreset(room: string, preset: Preset): Promise<void> {
  const updates: Partial<LabConfig> = {};
  if (preset.whitelist) updates.whitelist = preset.whitelist;
  if (preset.blacklist) updates.blacklist = preset.blacklist;
  await update(ref(rtdb, labPath(room)), updates);
}

// --- Controllo dei singoli PC ---

// Percorso del nodo di un PC
function pcPath(room: string, pcId: string): string {
  return `labs/${room}/pcs/${pcId}`;
}

// Aggiunta manuale di un PC (per test prima dell'agente): default "inherit" e offline
export async function addPc(room: string, pcId: string): Promise<void> {
  const pc: PcConfig = {
    hostname: pcId,
    online: false,
    override: "inherit",
  };
  await set(ref(rtdb, pcPath(room, pcId)), pc);
}

// Rimuove un PC dall'aula
export async function removePc(room: string, pcId: string): Promise<void> {
  await remove(ref(rtdb, pcPath(room, pcId)));
}

// Imposta lo stato di controllo di un singolo PC
export async function setPcOverride(
  room: string,
  pcId: string,
  override: PcOverride
): Promise<void> {
  await update(ref(rtdb, pcPath(room, pcId)), { override });
}
