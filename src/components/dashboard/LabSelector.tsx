"use client";

// Selettore dell'aula: scelta tra le aule esistenti o creazione di una nuova.

import { useState } from "react";
import { Plus, DoorOpen } from "lucide-react";

interface LabSelectorProps {
  labs: string[];
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

  function handleCreate() {
    const room = newRoom.trim();
    if (!room) return;
    onCreate(room);
    setNewRoom("");
    setCreating(false);
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2">
        <DoorOpen className="h-5 w-5 text-zinc-500" />
        <select
          value={selected ?? ""}
          onChange={(e) => onSelect(e.target.value)}
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900"
        >
          {labs.length === 0 && <option value="">Nessuna aula</option>}
          {labs.map((room) => (
            <option key={room} value={room}>
              {room}
            </option>
          ))}
        </select>
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
