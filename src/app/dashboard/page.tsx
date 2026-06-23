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
  setLists,
  addPc,
  removePc,
  setPcOverride,
  setAllPcOverride,
  type LabSummary,
} from "@/lib/labs";
import type { LabConfig, PcOverride } from "@/types/lab";
import { togglePreset, type Preset } from "@/lib/presets";
import LabSelector from "@/components/dashboard/LabSelector";
import LabToggle from "@/components/dashboard/LabToggle";
import DomainListEditor from "@/components/dashboard/DomainListEditor";
import MessageEditor from "@/components/dashboard/MessageEditor";
import PresetBar from "@/components/dashboard/PresetBar";
import PcList from "@/components/dashboard/PcList";
import Toast from "@/components/layout/Toast";

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [labs, setLabs] = useState<LabSummary[]>([]);
  const [room, setRoom] = useState<string | null>(null);
  const [config, setConfig] = useState<LabConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

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
        setRoom((current) => current ?? rooms[0]?.room ?? null);
      })
      .catch((err) => setError(handleError(err)));
  }, [user]);

  // Sottoscrizione realtime alla configurazione dell'aula selezionata
  useEffect(() => {
    if (!room) {
      setConfig(null);
      return;
    }
    const unsubscribe = subscribeLab(room, (cfg) => {
      setConfig(cfg);
      // Mantiene allineato il pallino di stato dell'aula corrente nel selettore
      if (cfg) {
        setLabs((prev) =>
          prev.map((l) => (l.room === room ? { ...l, active: cfg.active } : l))
        );
      }
    });
    return unsubscribe;
  }, [room]);

  // Esegue un'azione gestendo gli errori in modo uniforme e mostrando,
  // a buon fine, una micro-conferma (toast) che la modifica è propagata.
  async function run(action: Promise<void>, confirmation = "Modifica applicata") {
    try {
      setError(null);
      await action;
      setToast(confirmation);
    } catch (err) {
      setError(handleError(err));
    }
  }

  async function handleCreate(newRoom: string) {
    await run(createLab(newRoom));
    setLabs((prev) =>
      prev.some((l) => l.room === newRoom)
        ? prev
        : [...prev, { room: newRoom, active: false }]
    );
    setRoom(newRoom);
  }

  // Attiva/disattiva una categoria: somma o rimuove i suoi domini dalle liste
  function handleTogglePreset(preset: Preset) {
    if (!room || !config) return;
    const next = togglePreset(
      preset,
      config.whitelist ?? [],
      config.blacklist ?? []
    );
    run(setLists(room, next.whitelist, next.blacklist));
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
  // Filtro attivo ma senza alcuna regola: di fatto gli studenti restano liberi
  const noRules =
    !!config?.active &&
    (config.whitelist?.length ?? 0) === 0 &&
    (config.blacklist?.length ?? 0) === 0;

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

            {noRules && (
              <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                Filtro attivo ma nessuna regola impostata: gli studenti restano
                liberi. Aggiungi una whitelist o applica un preset.
              </p>
            )}

            <PresetBar
              whitelist={config.whitelist ?? []}
              blacklist={config.blacklist ?? []}
              onToggle={handleTogglePreset}
            />

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
              onSetAllOverride={(override: PcOverride) =>
                run(setAllPcOverride(room, Object.keys(pcs), override))
              }
              onAddPc={(pcId) => run(addPc(room, pcId))}
              onRemovePc={(pcId) => run(removePc(room, pcId))}
            />
          </>
        )}
      </main>

      <Toast message={toast} onDismiss={() => setToast(null)} />
    </div>
  );
}
