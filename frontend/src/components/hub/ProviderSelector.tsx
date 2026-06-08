"use client";

import { useEffect, useState } from "react";
import { getProvider, setProvider } from "@/lib/api";

export function ProviderSelector() {
  const [info, setInfo] = useState<{ current: string; available: string[]; models: Record<string, string> } | null>(null);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    getProvider().then(setInfo).catch(() => {});
  }, []);

  if (!info) return null;

  const handleSwitch = async (provider: string) => {
    if (provider === info.current || switching) return;
    setSwitching(true);
    try {
      const updated = await setProvider(provider);
      setInfo(updated);
    } catch {
      // silently fail
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="bg-surface-2 border border-hairline rounded-xl p-4">
      <p className="text-[11px] font-semibold text-ink-subtle uppercase tracking-wider mb-3">
        Provedor AI
      </p>
      <div className="space-y-2">
        {info.available.map((p) => (
          <button
            key={p}
            onClick={() => handleSwitch(p)}
            disabled={switching}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all text-[13px] ${
              info.current === p
                ? "bg-accent/10 text-accent border border-accent/30"
                : "text-ink-muted hover:bg-surface-3 border border-transparent"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${info.current === p ? "bg-accent" : "bg-ink-tertiary"}`} />
            <div className="flex-1 min-w-0">
              <p className="font-medium capitalize">{p === "lm_studio" ? "LM Studio" : p}</p>
              <p className="text-[11px] text-ink-tertiary truncate">{info.models[p]}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
