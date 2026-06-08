"use client";

import { useEffect, useState } from "react";
import { getProvider, setProvider, getGpuStatus, gpuLoad, gpuUnload } from "@/lib/api";
import { Cpu, Loader2, Zap, PowerOff } from "lucide-react";

export function ProviderSelector() {
  const [info, setInfo] = useState<{ current: string; available: string[]; models: Record<string, string> } | null>(null);
  const [switching, setSwitching] = useState(false);
  const [gpu, setGpu] = useState<{ loaded: boolean; model: string; vram_bytes: number } | null>(null);
  const [gpuBusy, setGpuBusy] = useState(false);

  const fetchGpu = async () => {
    try {
      const s = await getGpuStatus();
      setGpu(s);
    } catch {
      setGpu(null);
    }
  };

  useEffect(() => {
    getProvider().then(setInfo).catch(() => {});
    fetchGpu();
    const interval = setInterval(fetchGpu, 8000);
    return () => clearInterval(interval);
  }, []);

  if (!info) return null;

  const handleSwitch = async (provider: string) => {
    if (provider === info.current || switching) return;
    setSwitching(true);
    try {
      const updated = await setProvider(provider);
      setInfo(updated);
    } catch {
    } finally {
      setSwitching(false);
    }
  };

  const handleLoad = async () => {
    setGpuBusy(true);
    try {
      await gpuLoad();
      await fetchGpu();
    } catch {
    } finally {
      setGpuBusy(false);
    }
  };

  const handleUnload = async () => {
    setGpuBusy(true);
    try {
      await gpuUnload();
      setGpu({ loaded: false, model: gpu?.model || "", vram_bytes: 0 });
    } catch {
    } finally {
      setGpuBusy(false);
    }
  };

  const formatVRAM = (bytes: number) => {
    const gb = bytes / 1024 / 1024 / 1024;
    return `${gb.toFixed(1)}GB`;
  };

  return (
    <div className="bg-surface-2 border border-hairline rounded-xl p-4 space-y-3">
      <p className="text-[11px] font-semibold text-ink-subtle uppercase tracking-wider">
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

      <div className="border-t border-hairline pt-3">
        <div className="flex items-center justify-between mb-2">
          <p className="text-[11px] font-semibold text-ink-subtle uppercase tracking-wider flex items-center gap-1.5">
            <Cpu className="w-3 h-3" />
            GPU
          </p>
          {gpu && (
            <span className={`flex items-center gap-1 text-[11px] ${gpu.loaded ? "text-success" : "text-ink-tertiary"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${gpu.loaded ? "bg-success" : "bg-ink-tertiary"}`} />
              {gpu.loaded ? `${formatVRAM(gpu.vram_bytes)} / 16GB` : "disponivel"}
            </span>
          )}
        </div>

        {gpu === null && (
          <p className="text-[11px] text-ink-tertiary">Ollama indisponivel</p>
        )}

        {gpu && (
          <div className="w-full bg-surface-3 rounded-full h-1.5 mb-2.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                gpu.loaded ? "bg-success" : "bg-ink-tertiary/30"
              }`}
              style={{ width: gpu.loaded ? `${Math.min((gpu.vram_bytes / (16 * 1024 * 1024 * 1024)) * 100, 100)}%` : "0%" }}
            />
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={handleLoad}
            disabled={gpuBusy || gpu === null}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium bg-accent/10 text-accent border border-accent/30 hover:bg-accent/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {gpuBusy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
            Carregar
          </button>
          <button
            onClick={handleUnload}
            disabled={gpuBusy || gpu === null || !gpu.loaded}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium bg-warning/10 text-warning border border-warning/30 hover:bg-warning/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {gpuBusy ? <Loader2 className="w-3 h-3 animate-spin" /> : <PowerOff className="w-3 h-3" />}
            Liberar
          </button>
        </div>
      </div>
    </div>
  );
}
