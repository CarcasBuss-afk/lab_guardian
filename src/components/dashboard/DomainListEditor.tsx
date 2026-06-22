"use client";

// Editor riusabile per una lista di domini (whitelist o blacklist).
// Supporta wildcard (es. "*.google.com"). Le modifiche sono notificate al parent.

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DomainListEditorProps {
  title: string;
  // Domini correnti
  domains: string[];
  // Chiamato con la nuova lista a ogni modifica
  onChange: (domains: string[]) => void;
  // Variante cromatica: verde per la whitelist, rossa per la blacklist
  variant: "allow" | "deny";
}

export default function DomainListEditor({
  title,
  domains,
  onChange,
  variant,
}: DomainListEditorProps) {
  const [value, setValue] = useState("");

  function addDomain() {
    const domain = value.trim().toLowerCase();
    if (!domain || domains.includes(domain)) {
      setValue("");
      return;
    }
    onChange([...domains, domain]);
    setValue("");
  }

  function removeDomain(domain: string) {
    onChange(domains.filter((d) => d !== domain));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      addDomain();
    }
  }

  const accent =
    variant === "allow"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : "bg-red-50 text-red-700 border-red-200";

  return (
    <div className="space-y-3 rounded-xl border border-zinc-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-zinc-900">{title}</h3>

      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="es. *.google.com"
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900"
        />
        <button
          type="button"
          onClick={addDomain}
          className="flex items-center gap-1 rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
        >
          <Plus className="h-4 w-4" />
          Aggiungi
        </button>
      </div>

      {domains.length === 0 ? (
        <p className="text-sm text-zinc-400">Nessun dominio.</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {domains.map((domain) => (
            <li
              key={domain}
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm",
                accent
              )}
            >
              <span className="font-mono">{domain}</span>
              <button
                type="button"
                onClick={() => removeDomain(domain)}
                aria-label={`Rimuovi ${domain}`}
                className="rounded-full p-0.5 hover:bg-black/5"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
