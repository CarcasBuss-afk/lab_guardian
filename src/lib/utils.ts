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
