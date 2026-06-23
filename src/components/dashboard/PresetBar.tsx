"use client";

// Barra delle categorie: pulsanti toggle che sommano/rimuovono i loro domini
// dalle liste. Una categoria è "attiva" quando tutti i suoi domini sono presenti.

import { Sparkles } from "lucide-react";
import { PRESETS, isPresetActive, type Preset } from "@/lib/presets";
import { cn } from "@/lib/utils";

interface PresetBarProps {
  // Liste correnti, per calcolare quali categorie sono attive
  whitelist: string[];
  blacklist: string[];
  // Attiva/disattiva una categoria
  onToggle: (preset: Preset) => void;
}

export default function PresetBar({ whitelist, blacklist, onToggle }: PresetBarProps) {
  return (
    <div className="space-y-3 rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-zinc-500" />
        <h3 className="text-sm font-semibold text-zinc-900">Categorie</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => {
          const active = isPresetActive(preset, whitelist, blacklist);
          return (
            <button
              key={preset.id}
              type="button"
              onClick={() => onToggle(preset)}
              title={preset.description}
              aria-pressed={active}
              className={cn(
                "rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "border-zinc-900 bg-zinc-900 text-white hover:bg-zinc-800"
                  : "border-zinc-300 text-zinc-700 hover:border-zinc-900 hover:bg-zinc-50"
              )}
            >
              {preset.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
