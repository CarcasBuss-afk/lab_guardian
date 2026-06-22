"use client";

// Lista dei PC dell'aula con controllo per singolo PC (3 stati) e stato online/offline.

import { useState } from "react";
import { Plus, Trash2, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PcConfig, PcOverride } from "@/types/lab";

interface PcListProps {
  pcs: Record<string, PcConfig>;
  onSetOverride: (pcId: string, override: PcOverride) => void;
  onAddPc: (pcId: string) => void;
  onRemovePc: (pcId: string) => void;
}

// Opzioni dei tre stati di controllo del PC
const OVERRIDE_OPTIONS: { value: PcOverride; label: string; active: string }[] = [
  { value: "inherit", label: "Segue aula", active: "bg-zinc-900 text-white" },
  { value: "free", label: "Libero", active: "bg-emerald-600 text-white" },
  { value: "blocked", label: "Bloccato", active: "bg-red-600 text-white" },
];

export default function PcList({
  pcs,
  onSetOverride,
  onAddPc,
  onRemovePc,
}: PcListProps) {
  const [newPc, setNewPc] = useState("");

  function handleAdd() {
    const pcId = newPc.trim();
    if (!pcId) return;
    onAddPc(pcId);
    setNewPc("");
  }

  const entries = Object.entries(pcs);

  return (
    <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Monitor className="h-4 w-4 text-zinc-500" />
        <h3 className="text-sm font-semibold text-zinc-900">PC dell'aula</h3>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={newPc}
          onChange={(e) => setNewPc(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="Hostname PC (es. PC-01)"
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="flex items-center gap-1 rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
        >
          <Plus className="h-4 w-4" />
          Aggiungi
        </button>
      </div>

      {entries.length === 0 ? (
        <p className="text-sm text-zinc-400">
          Nessun PC. Aggiungine uno a mano o attendi che l&apos;agente si registri.
        </p>
      ) : (
        <ul className="space-y-2">
          {entries.map(([pcId, pc]) => (
            <li
              key={pcId}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-zinc-200 px-3 py-2.5"
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "h-2.5 w-2.5 rounded-full",
                    pc.online ? "bg-emerald-500" : "bg-zinc-300"
                  )}
                  title={pc.online ? "Online" : "Offline"}
                />
                <span className="font-mono text-sm text-zinc-900">{pc.hostname}</span>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex overflow-hidden rounded-lg border border-zinc-300">
                  {OVERRIDE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => onSetOverride(pcId, opt.value)}
                      className={cn(
                        "px-3 py-1.5 text-xs font-medium transition-colors",
                        pc.override === opt.value
                          ? opt.active
                          : "bg-white text-zinc-600 hover:bg-zinc-50"
                      )}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => onRemovePc(pcId)}
                  aria-label={`Rimuovi ${pc.hostname}`}
                  className="rounded-lg p-1.5 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
