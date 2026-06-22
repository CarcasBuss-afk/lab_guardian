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
    id: "classroom",
    label: "Google Classroom",
    description: "Servizi Google, con YouTube bloccato.",
    whitelist: ["*.google.com", "*.googleapis.com", "*.gstatic.com", "*.googleusercontent.com"],
    blacklist: ["youtube.com", "*.youtube.com", "youtu.be", "*.ytimg.com", "*.googlevideo.com"],
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
