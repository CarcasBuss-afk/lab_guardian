// Preset di configurazione predefiniti per la dashboard docente.
// Applicare un preset sovrascrive whitelist e/o blacklist dell'aula.

export interface Preset {
  // Identificativo univoco del preset
  id: string;
  // Etichetta mostrata nella UI
  label: string;
  // Breve descrizione dell'uso
  description: string;
  // Domini da impostare in whitelist (se presente)
  whitelist?: string[];
  // Domini da impostare in blacklist (se presente)
  blacklist?: string[];
}

export const PRESETS: Preset[] = [
  {
    id: "kahoot",
    label: "Kahoot",
    description: "Solo Kahoot e font necessari.",
    whitelist: ["*.kahoot.com", "*.kahoot.it", "fonts.googleapis.com", "fonts.gstatic.com"],
  },
  {
    id: "google_scolastico",
    label: "Solo Google Scolastico",
    description: "Tutti gli strumenti Google (Classroom, Drive, Gmail, Documenti…); bloccati YouTube e Google Sites.",
    whitelist: [
      "google.com",
      "*.google.com",
      // Domini Google regionali italiani (es. accounts.google.it nel login)
      "google.it",
      "*.google.it",
      "*.googleapis.com",
      "*.gstatic.com",
      // Dominio "nudo": *.gstatic.com NON copre l'apex, da cui Classroom
      // serve alcune immagini/asset (es. banner del corso → riquadro bianco).
      "gstatic.com",
      "*.googleusercontent.com",
      "*.ggpht.com",
      "*.gvt1.com",
      "*.gvt2.com",
    ],
    blacklist: [
      // YouTube (non sta sotto *.google.com, ma lo blocchiamo esplicitamente)
      "youtube.com",
      "*.youtube.com",
      "youtu.be",
      "*.ytimg.com",
      "*.googlevideo.com",
      // Google Sites: ricade sotto *.google.com, la blacklist ha priorità e lo blocca
      "sites.google.com",
    ],
  },
  {
    id: "python_docs",
    label: "Documentazione Python",
    description: "Solo documentazione e pacchetti Python.",
    whitelist: ["docs.python.org", "pypi.org", "*.python.org"],
  },
  {
    id: "w3schools",
    label: "W3Schools",
    description: "Solo W3Schools.",
    whitelist: ["www.w3schools.com", "*.w3schools.com"],
  },
];

// Verifica se un preset è "attivo": tutti i suoi domini sono già nelle liste.
// Un preset senza domini non è mai considerato attivo.
export function isPresetActive(
  preset: Preset,
  whitelist: string[],
  blacklist: string[]
): boolean {
  const w = preset.whitelist ?? [];
  const b = preset.blacklist ?? [];
  if (w.length === 0 && b.length === 0) return false;
  return w.every((d) => whitelist.includes(d)) && b.every((d) => blacklist.includes(d));
}

// Attiva/disattiva un preset sulle liste correnti e restituisce le nuove liste.
// - Se non attivo: aggiunge i suoi domini (dedup, preservando l'ordine esistente).
// - Se attivo: rimuove i suoi domini, ma conserva quelli ancora richiesti da
//   altre categorie rimaste attive (gestione delle sovrapposizioni).
export function togglePreset(
  preset: Preset,
  whitelist: string[],
  blacklist: string[]
): { whitelist: string[]; blacklist: string[] } {
  if (isPresetActive(preset, whitelist, blacklist)) {
    // Domini da preservare perché condivisi con altre categorie attive
    const stillActive = PRESETS.filter(
      (p) => p.id !== preset.id && isPresetActive(p, whitelist, blacklist)
    );
    const keepW = new Set(stillActive.flatMap((p) => p.whitelist ?? []));
    const keepB = new Set(stillActive.flatMap((p) => p.blacklist ?? []));
    const removeW = new Set((preset.whitelist ?? []).filter((d) => !keepW.has(d)));
    const removeB = new Set((preset.blacklist ?? []).filter((d) => !keepB.has(d)));
    return {
      whitelist: whitelist.filter((d) => !removeW.has(d)),
      blacklist: blacklist.filter((d) => !removeB.has(d)),
    };
  }
  const addW = (preset.whitelist ?? []).filter((d) => !whitelist.includes(d));
  const addB = (preset.blacklist ?? []).filter((d) => !blacklist.includes(d));
  return {
    whitelist: [...whitelist, ...addW],
    blacklist: [...blacklist, ...addB],
  };
}
