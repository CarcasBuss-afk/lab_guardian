// Funzioni utility generiche

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge classi Tailwind in modo sicuro.
 * Combina clsx (condizionali) con tailwind-merge (risoluzione conflitti).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formato relativo compatto di un timestamp passato (es. "ora", "12s fa",
 * "3 min fa", "2 h fa", "1 g fa"). Usato per il "visto X fa" dei PC.
 */
export function timeAgo(timestamp: number, now: number = Date.now()): string {
  const seconds = Math.max(0, Math.round((now - timestamp) / 1000));
  if (seconds < 5) return "ora";
  if (seconds < 60) return `${seconds}s fa`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min fa`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h fa`;
  const days = Math.round(hours / 24);
  return `${days} g fa`;
}
