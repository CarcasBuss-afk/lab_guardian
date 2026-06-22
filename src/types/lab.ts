// Tipi del canale di controllo (Realtime Database)

// Override del singolo PC (ha priorità sulle regole dell'aula):
// - "blocked": PC bloccato del tutto (nessun sito)
// - "free": PC libero, filtro disattivato solo per lui
// - "inherit": segue le regole dell'aula (whitelist/blacklist)
export type PcOverride = "blocked" | "free" | "inherit";

// Configurazione di un singolo PC del laboratorio
export interface PcConfig {
  // Nome host del PC (coincide con la chiave del nodo)
  hostname: string;
  // Stato di connessione riportato dall'agente
  online: boolean;
  // Timestamp (ms) dell'ultimo contatto dell'agente, se disponibile
  lastSeen?: number;
  // Stato di controllo del PC
  override: PcOverride;
}

// Configurazione di un'aula (nodo /labs/{room})
export interface LabConfig {
  // Filtro attivo per l'intera aula
  active: boolean;
  // Domini permessi (supporta wildcard, es. "*.google.com")
  whitelist: string[];
  // Domini bloccati, priorità sulla whitelist (supporta wildcard)
  blacklist: string[];
  // Messaggio mostrato agli studenti quando un sito è bloccato
  message: string;
  // PC dell'aula, indicizzati per hostname
  pcs?: Record<string, PcConfig>;
}

// Configurazione di default per una nuova aula
export const DEFAULT_LAB_CONFIG: LabConfig = {
  active: false,
  whitelist: [],
  blacklist: [],
  message: "Oggi sono permessi solo i siti per l'esercitazione.",
};
