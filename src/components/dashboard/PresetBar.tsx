"use client";

// Barra dei preset: applica con un click una configurazione predefinita.

import { Sparkles } from "lucide-react";
import { PRESETS, type Preset } from "@/lib/presets";

interface PresetBarProps {
  onApply: (preset: Preset) => void;
}

export default function PresetBar({ onApply }: PresetBarProps) {
  return (
    <div className="space-y-3 rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-zinc-500" />
        <h3 className="text-sm font-semibold text-zinc-900">Preset</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            onClick={() => onApply(preset)}
            title={preset.description}
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 transition-colors hover:border-zinc-900 hover:bg-zinc-50"
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
