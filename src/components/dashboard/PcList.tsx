"use client";

// Lista dei PC dell'aula con controllo per singolo PC (3 stati), stato
// online/offline live, riepilogo e azioni rapide su tutti i PC.

import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, Monitor, Lock, Unlock, DoorOpen } from "lucide-react";
import { cn, timeAgo } from "@/lib/utils";
import type { PcConfig, PcOverride } from "@/types/lab";

interface PcListProps {
  pcs: Record<string, PcConfig>;
  onSetOverride: (pcId: string, override: PcOverride) => void;
  onSetAllOverride: (override: PcOverride) => void;
  onAddPc: (pcId: string) => void;
  onRemovePc: (pcId: string) => void;
}

// Un PC è considerato online se ha inviato un heartbeat di recente.
// L'agente non può segnalare la disconnessione (REST senza onDisconnect),
// quindi lo stato si deduce dalla freschezza di lastSeen.
const ONLINE_THRESHOLD_MS = 90_000;

// Frequenza del tick che fa "scadere" lo stato online senza nuovi eventi.
const TICK_MS = 15_000;

function isOnline(pc: PcConfig, now: number): boolean {
  if (pc.lastSeen) return now - pc.lastSeen < ONLINE_THRESHOLD_MS;
  return pc.online;
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
  onSetAllOverride,
  onAddPc,
  onRemovePc,
}: PcListProps) {
  const [newPc, setNewPc] = useState("");
  // Tick periodico: cambia ogni TICK_MS per forzare il ricalcolo dello stato
  // online e del "visto X fa" anche senza nuovi eventi realtime.
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), TICK_MS);
    return () => window.clearInterval(id);
  }, []);

  function handleAdd() {
    const pcId = newPc.trim();
    if (!pcId) return;
    onAddPc(pcId);
    setNewPc("");
  }

  const entries = Object.entries(pcs);

  // Conteggi per il riepilogo a colpo d'occhio
  const summary = useMemo(() => {
    let online = 0;
    let blocked = 0;
    let free = 0;
    let inherit = 0;
    for (const [, pc] of entries) {
      if (isOnline(pc, now)) online += 1;
      if (pc.override === "blocked") blocked += 1;
      else if (pc.override === "free") free += 1;
      else inherit += 1;
    }
    return { online, blocked, free, inherit };
  }, [entries, now]);

  function handleBlockAll() {
    if (entries.length === 0) return;
    if (
      window.confirm(
        `Bloccare tutti i ${entries.length} PC dell'aula? Nessuno potrà navigare.`
      )
    ) {
      onSetAllOverride("blocked");
    }
  }

  return (
    <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Monitor className="h-4 w-4 text-zinc-500" />
          <h3 className="text-sm font-semibold text-zinc-900">PC dell&apos;aula</h3>
        </div>

        {entries.length > 0 && (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              {summary.online} online
            </span>
            <span className="text-red-600">{summary.blocked} bloccati</span>
            <span className="text-emerald-600">{summary.free} liberi</span>
            <span>{summary.inherit} seguono aula</span>
          </div>
        )}
      </div>

      {/* Azioni rapide su tutti i PC */}
      {entries.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleBlockAll}
            className="flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-100"
          >
            <Lock className="h-3.5 w-3.5" />
            Blocca tutti
          </button>
          <button
            type="button"
            onClick={() => onSetAllOverride("free")}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-100"
          >
            <Unlock className="h-3.5 w-3.5" />
            Libera tutti
          </button>
          <button
            type="button"
            onClick={() => onSetAllOverride("inherit")}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            <DoorOpen className="h-3.5 w-3.5" />
            Tutti seguono l&apos;aula
          </button>
        </div>
      )}

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
          {entries.map(([pcId, pc]) => {
            const online = isOnline(pc, now);
            return (
              <li
                key={pcId}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-zinc-200 px-3 py-2.5"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "h-2.5 w-2.5 rounded-full",
                      online ? "bg-emerald-500" : "bg-zinc-300"
                    )}
                    title={online ? "Online" : "Offline"}
                  />
                  <span className="font-mono text-sm text-zinc-900">{pc.hostname}</span>
                  {!online && pc.lastSeen && (
                    <span className="text-xs text-zinc-400">
                      visto {timeAgo(pc.lastSeen, now)}
                    </span>
                  )}
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
            );
          })}
        </ul>
      )}
    </div>
  );
}
