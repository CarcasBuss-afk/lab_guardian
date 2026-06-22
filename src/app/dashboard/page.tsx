"use client";

// Pannello di controllo del docente. Protetto: richiede autenticazione.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, LogOut } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { handleError } from "@/lib/errors";
import {
  listLabs,
  createLab,
  subscribeLab,
  setActive,
  setWhitelist,
  setBlacklist,
  setMessage,
  applyPreset,
  addPc,
  removePc,
  setPcOverride,
} from "@/lib/labs";
import type { LabConfig, PcOverride } from "@/types/lab";
import type { Preset } from "@/lib/presets";
import LabSelector from "@/components/dashboard/LabSelector";
import LabToggle from "@/components/dashboard/LabToggle";
import DomainListEditor from "@/components/dashboard/DomainListEditor";
import MessageEditor from "@/components/dashboard/MessageEditor";
import PresetBar from "@/components/dashboard/PresetBar";
import PcList from "@/components/dashboard/PcList";

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [labs, setLabs] = useState<string[]>([]);
  const [room, setRoom] = useState<string | null>(null);
  const [config, setConfig] = useState<LabConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Protezione rotta: se non autenticato torna al login
  useEffect(() => {
    if (!loading && !user) {
      router.replace("/");
    }
  }, [user, loading, router]);

  // Carica l'elenco delle aule una volta autenticato
  useEffect(() => {
    if (!user) return;
    listLabs()
      .then((rooms) => {
        setLabs(rooms);
        setRoom((current) => current ?? rooms[0] ?? null);
      })
      .catch((err) => setError(handleError(err)));
  }, [user]);

  // Sottoscrizione realtime alla configurazione dell'aula selezionata
  useEffect(() => {
    if (!room) {
      setConfig(null);
      return;
    }
    const unsubscribe = subscribeLab(room, setConfig);
    return unsubscribe;
  }, [room]);

  // Esegue un'azione gestendo gli errori in modo uniforme
  async function run(action: Promise<void>) {
    try {
      setError(null);
      await action;
    } catch (err) {
      setError(handleError(err));
    }
  }

  async function handleCreate(newRoom: string) {
    await run(createLab(newRoom));
    setLabs((prev) => (prev.includes(newRoom) ? prev : [...prev, newRoom]));
    setRoom(newRoom);
  }

  function handleLogout() {
    logout().catch((err) => setError(handleError(err)));
  }

  // Stato di caricamento iniziale / redirect
  if (loading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-50">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </div>
    );
  }

  const pcs = config?.pcs ?? {};

  return (
    <div className="flex flex-1 flex-col bg-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-4">
        <h1 className="text-lg font-semibold tracking-tight text-zinc-900">
          Lab Guardian
        </h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-zinc-500">{user.email}</span>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:border-zinc-900 hover:bg-zinc-50"
          >
            <LogOut className="h-4 w-4" />
            Esci
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 space-y-5 px-6 py-8">
        <LabSelector
          labs={labs}
          selected={room}
          onSelect={setRoom}
          onCreate={handleCreate}
        />

        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}

        {!room ? (
          <p className="rounded-xl border border-dashed border-zinc-300 p-8 text-center text-sm text-zinc-500">
            Crea o seleziona un&apos;aula per iniziare.
          </p>
        ) : config === null ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
          </div>
        ) : (
          <>
            <LabToggle
              active={config.active}
              onToggle={(active) => run(setActive(room, active))}
            />

            <PresetBar onApply={(preset: Preset) => run(applyPreset(room, preset))} />

            <DomainListEditor
              title="Whitelist (siti permessi)"
              domains={config.whitelist ?? []}
              onChange={(domains) => run(setWhitelist(room, domains))}
              variant="allow"
            />

            <DomainListEditor
              title="Blacklist (siti bloccati — priorità sulla whitelist)"
              domains={config.blacklist ?? []}
              onChange={(domains) => run(setBlacklist(room, domains))}
              variant="deny"
            />

            <MessageEditor
              message={config.message ?? ""}
              onSave={(message) => run(setMessage(room, message))}
            />

            <PcList
              pcs={pcs}
              onSetOverride={(pcId, override: PcOverride) =>
                run(setPcOverride(room, pcId, override))
              }
              onAddPc={(pcId) => run(addPc(room, pcId))}
              onRemovePc={(pcId) => run(removePc(room, pcId))}
            />
          </>
        )}
      </main>
    </div>
  );
}
