"use client";

import { Sparkles, Target, BarChart3, FileText, BrainCircuit, TrendingUp, Briefcase, Search } from "lucide-react";
import { ProviderSelector } from "@/components/hub/ProviderSelector";

const QUICK_ACTIONS = [
  { id: "pipeline_status", label: "Status Pipeline", icon: BarChart3, desc: "Resumo completo das candidaturas", color: "from-blue-500/20 to-blue-600/10 border-blue-500/30" },
  { id: "analisar_ultima", label: "Analisar Vaga", icon: BrainCircuit, desc: "Análise profunda da última vaga", color: "from-accent/20 to-accent/10 border-accent/30" },
  { id: "calcular_match", label: "Calcular Match", icon: Target, desc: "Compatibilidade com seu perfil", color: "from-green-500/20 to-green-600/10 border-green-500/30" },
  { id: "abrir_browser", label: "Navegar Vagas", icon: Search, desc: "Buscar e explorar vagas", color: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/30" },
];

export function WelcomeView({ onAction, vagasRecentes, pipelineResumo }: {
  onAction: (action: string) => void;
  vagasRecentes: { titulo: string; empresa: string; score: number }[];
  pipelineResumo: { total: number; salvas: number; aplicadas: number; em_analise: number };
}) {
  return (
    <div className="p-6 space-y-6">
      <ProviderSelector />
      <div>
        <h2 className="text-lg font-semibold metallic-gradient font-heading mb-1">WorkHunter Copilot</h2>
        <p className="text-[13px] text-ink-subtle">Seu assistente inteligente de carreira. O que vamos fazer hoje?</p>
      </div>

      <div>
        <p className="text-[11px] font-semibold text-ink-subtle uppercase tracking-wider mb-3">Ações Rápidas</p>
        <div className="grid grid-cols-2 gap-3">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a.id}
              onClick={() => onAction(a.id)}
              className={`flex flex-col items-start gap-2 p-4 rounded-xl border bg-gradient-to-br ${a.color} hover:brightness-110 transition-all text-left`}
            >
              <a.icon className="w-5 h-5 text-ink" />
              <span className="text-[13px] font-medium text-ink">{a.label}</span>
              <span className="text-[11px] text-ink-muted leading-tight">{a.desc}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-2 border border-hairline rounded-xl p-4 text-center">
          <p className="text-2xl font-bold metallic-gradient tabular-nums">{pipelineResumo.total}</p>
          <p className="text-[11px] text-ink-subtle mt-1">Total Pipeline</p>
        </div>
        <div className="bg-surface-2 border border-hairline rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-accent tabular-nums">{pipelineResumo.aplicadas}</p>
          <p className="text-[11px] text-ink-subtle mt-1">Aplicadas</p>
        </div>
        <div className="bg-surface-2 border border-hairline rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-success tabular-nums">{pipelineResumo.em_analise}</p>
          <p className="text-[11px] text-ink-subtle mt-1">Em Análise</p>
        </div>
      </div>

      {vagasRecentes.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold text-ink-subtle uppercase tracking-wider mb-3">Vagas Recentes</p>
          <div className="space-y-2">
            {vagasRecentes.slice(0, 4).map((v, i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-surface-2 border border-hairline hover:bg-surface-3 transition-colors cursor-pointer"
                onClick={() => onAction(`selecionar_vaga|${i}`)}>
                <Briefcase className="w-4 h-4 text-ink-tertiary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-ink truncate">{v.titulo}</p>
                  <p className="text-[11px] text-ink-muted truncate">{v.empresa}</p>
                </div>
                <span className="text-[11px] font-semibold text-accent tabular-nums">{v.score}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
