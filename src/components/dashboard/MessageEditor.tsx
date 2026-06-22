"use client";

// Editor del messaggio mostrato agli studenti quando un sito è bloccato.

import { useEffect, useState } from "react";
import { Save, Check } from "lucide-react";

interface MessageEditorProps {
  message: string;
  onSave: (message: string) => void;
}

export default function MessageEditor({ message, onSave }: MessageEditorProps) {
  const [value, setValue] = useState(message);
  const [saved, setSaved] = useState(false);

  // Allinea il campo quando il messaggio cambia da remoto
  useEffect(() => {
    setValue(message);
  }, [message]);

  function handleSave() {
    onSave(value.trim());
    setSaved(true);
    // Nasconde la conferma dopo poco (timeout solo per UI, lato client)
    window.setTimeout(() => setSaved(false), 2000);
  }

  const dirty = value.trim() !== message;

  return (
    <div className="space-y-3 rounded-xl border border-zinc-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-zinc-900">Messaggio agli studenti</h3>
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={2}
        placeholder="Messaggio mostrato quando un sito è bloccato"
        className="w-full resize-none rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900"
      />
      <button
        type="button"
        onClick={handleSave}
        disabled={!dirty}
        className="flex items-center gap-2 rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50"
      >
        {saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
        {saved ? "Salvato" : "Salva messaggio"}
      </button>
    </div>
  );
}
