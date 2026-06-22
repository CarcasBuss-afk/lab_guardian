"use client";

// Toggle ON/OFF del filtro per l'intera aula, con feedback visivo.

import { ShieldCheck, ShieldOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface LabToggleProps {
  active: boolean;
  onToggle: (active: boolean) => void;
}

export default function LabToggle({ active, onToggle }: LabToggleProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between rounded-xl border p-5 transition-colors",
        active ? "border-emerald-200 bg-emerald-50" : "border-zinc-200 bg-white"
      )}
    >
      <div className="flex items-center gap-3">
        {active ? (
          <ShieldCheck className="h-6 w-6 text-emerald-600" />
        ) : (
          <ShieldOff className="h-6 w-6 text-zinc-400" />
        )}
        <div>
          <p className="text-sm font-semibold text-zinc-900">
            Filtro {active ? "attivo" : "disattivato"}
          </p>
          <p className="text-sm text-zinc-500">
            {active
              ? "Le regole dell'aula sono applicate sui PC."
              : "Gli studenti navigano senza restrizioni."}
          </p>
        </div>
      </div>

      <button
        type="button"
        role="switch"
        aria-checked={active}
        onClick={() => onToggle(!active)}
        className={cn(
          "relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors",
          active ? "bg-emerald-600" : "bg-zinc-300"
        )}
      >
        <span
          className={cn(
            "inline-block h-5 w-5 transform rounded-full bg-white transition-transform",
            active ? "translate-x-6" : "translate-x-1"
          )}
        />
      </button>
    </div>
  );
}
