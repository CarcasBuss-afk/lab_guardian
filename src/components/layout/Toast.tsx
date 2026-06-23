"use client";

// Toast leggero in basso a destra, senza dipendenze esterne.
// Si auto-nasconde dopo `duration` ms; il parent ne controlla la visibilità.

import { useEffect } from "react";
import { Check } from "lucide-react";

interface ToastProps {
  // Messaggio da mostrare; null/"" nasconde il toast
  message: string | null;
  // Richiesta di chiusura (timeout scaduto)
  onDismiss: () => void;
  // Durata in ms prima dell'auto-dismiss
  duration?: number;
}

export default function Toast({ message, onDismiss, duration = 1500 }: ToastProps) {
  useEffect(() => {
    if (!message) return;
    const id = window.setTimeout(onDismiss, duration);
    return () => window.clearTimeout(id);
  }, [message, duration, onDismiss]);

  if (!message) return null;

  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white shadow-lg">
      <Check className="h-4 w-4 text-emerald-400" />
      {message}
    </div>
  );
}
