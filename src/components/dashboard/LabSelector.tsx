"use client";

// Selettore dell'aula: dropdown con stato del filtro per ciascuna aula
// (pallino verde = attivo) e creazione di una nuova aula.

import { useEffect, useRef, useState } from "react";
import { Plus, DoorOpen, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LabSummary } from "@/lib/labs";

interface LabSelectorProps {
  labs: LabSummary[];
  selected: string | null;
  onSelect: (room: string) => void;
  onCreate: (room: string) => void;
}

export default function LabSelector({
  labs,
  selected,
  onSelect,
  onCreate,
}: LabSelectorProps) {
  const [creating, setCreating] = useState(false);
  const [newRoom, setNewRoom] = useState("");
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Chiude il dropdown al click fuori
  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  function handleCreate() {
    const room = newRoom.trim();
    if (!room) return;
    onCreate(room);
    setNewRoom("");
    setCreating(false);
  }

  const selectedLab = labs.find((l) => l.room === selected);

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2">
        <DoorOpen className="h-5 w-5 text-zinc-500" />
        <div ref={dropdownRef} className="relative">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-haspopup="listbox"
            aria-expanded={open}
            className="flex min-w-[10rem] items-center justify-between gap-2 rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none transition-colors hover:border-zinc-400 focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900"
          >
            <span className="flex items-center gap-2">
              {selectedLab && (
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    selectedLab.active ? "bg-emerald-500" : "bg-zinc-300"
                  )}
                />
              )}
              {selected ?? "Nessuna aula"}
            </span>
            <ChevronDown className="h-4 w-4 text-zinc-400" />
          </button>

          {open && labs.length > 0 && (
            <ul
              role="listbox"
              className="absolute z-10 mt-1 max-h-64 w-full min-w-[12rem] overflow-auto rounded-lg border border-zinc-200 bg-white py-1 shadow-lg"
            >
              {labs.map((lab) => (
                <li key={lab.room} role="option" aria-selected={lab.room === selected}>
                  <button
                    type="button"
                    onClick={() => {
                      onSelect(lab.room);
                      setOpen(false);
                    }}
                    className={cn(
                      "flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors hover:bg-zinc-50",
                      lab.room === selected ? "font-medium text-zinc-900" : "text-zinc-700"
                    )}
                  >
                    <span
                      className={cn(
                        "h-2 w-2 shrink-0 rounded-full",
                        lab.active ? "bg-emerald-500" : "bg-zinc-300"
                      )}
                      title={lab.active ? "Filtro attivo" : "Filtro disattivato"}
                    />
                    {lab.room}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {creating ? (
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newRoom}
            onChange={(e) => setNewRoom(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            placeholder="Nome aula (es. aula3)"
            autoFocus
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900"
          />
          <button
            type="button"
            onClick={handleCreate}
            className="rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
          >
            Crea
          </button>
          <button
            type="button"
            onClick={() => setCreating(false)}
            className="text-sm text-zinc-500 hover:text-zinc-900"
          >
            Annulla
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="flex items-center gap-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 transition-colors hover:border-zinc-900 hover:bg-zinc-50"
        >
          <Plus className="h-4 w-4" />
          Nuova aula
        </button>
      )}
    </div>
  );
}
