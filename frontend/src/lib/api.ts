import axios from "axios";

export interface Vaga {
  id: string;
  titulo: string;
  empresa: string;
  descricao: string;
  localizacao: string | null;
  uf: string | null;
  modelo_trabalho: string | null;
  url: string;
  fonte: string;
  id_externo: string;
  salario_min: number | null;
  salario_max: number | null;
  tipo_contrato: string | null;
  data_publicacao: string | null;
  coletada_em: string;
  ativa: boolean;
  score: number;
  analise: AnaliseOffline | null;
  analise_ia: AnaliseIA | null;
  usuario_status: VagaUsuarioStatus | null;
  termo_busca: string;
}

export interface AnaliseOffline {
  fake_junior: boolean;
  fake_junior_detalhes: string[];
  nivel_estimado: string;
}

export interface AnaliseIA {
  stack_principal: string[];
  nivel: string;
  fake_junior: boolean;
  salario_estimado_min: number | null;
  salario_estimado_max: number | null;
  resumo: string;
}

export interface PerfilUsuario {
  nome: string;
  email: string;
  cargos_alvo: string[];
  area_foco: string[];
  palavras_chave_busca: string[];
  stacks_atuais: { nome: string; categoria: string }[];
  stacks_aprendendo: { nome: string; categoria: string }[];
  preferencias_localizacao: string[];
  pretensao_salarial_min: number | null;
  palavras_chave_evitar: string[];
}

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8070",
  timeout: 15000,
});

export interface VagaListaResponse {
  data: Vaga[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface VagaUsuarioStatus {
  favoritada: boolean;
  aplicada: boolean;
  salva: boolean;
  analisada: boolean;
  ignorada: boolean;
  arquivada: boolean;
}

export async function listarVagas(params?: {
  fonte?: string;
  ativa?: boolean;
  score_min?: number;
  order_by?: string;
  limit?: number;
  offset?: number;
}): Promise<Vaga[]> {
  const { data } = await api.get<VagaListaResponse>("/api/v1/vagas/", { params });
  return data.data;
}

export interface Categoria {
  id: string;
  label: string;
  keywords_include: string[];
  keywords_exclude: string[];
  score_bonus: number;
  cor: string;
  ativa: boolean;
  ordem: number;
}

export async function listarCategorias(): Promise<Categoria[]> {
  const { data } = await api.get<Categoria[]>("/api/v1/categorias/");
  return data;
}

export async function listarVagasPaginado(params?: {
  page?: number;
  limit?: number;
  fonte?: string;
  ativa?: boolean;
  score_min?: number;
  score_max?: number;
  busca?: string;
  status?: string;
  modelo_trabalho?: string;
  uf?: string[];
  categoria?: string;
  search_term?: string;
  order_by?: string;
  order_dir?: string;
}): Promise<VagaListaResponse> {
  const { data } = await api.get<VagaListaResponse>("/api/v1/vagas/", { params });
  return data;
}

export async function listarLocais(): Promise<{
  ufs: string[];
  modelos_trabalho: string[];
  possui_remoto: boolean;
}> {
  const { data } = await api.get("/api/v1/vagas/locais");
  return data;
}

export async function favoritarVaga(vagaId: string): Promise<{ favoritada: boolean }> {
  const { data } = await api.post(`/api/v1/vagas-usuarios/favoritar/${vagaId}`);
  return data;
}

export async function obterStatusVaga(vagaId: string): Promise<VagaUsuarioStatus & { id: string; notas: string; updated_at: string }> {
  const { data } = await api.get(`/api/v1/vagas-usuarios/status/${vagaId}`);
  return data;
}

export async function bulkStatusVaga(vagaIds: string[]): Promise<Record<string, VagaUsuarioStatus>> {
  const { data } = await api.post("/api/v1/vagas-usuarios/bulk-status", { vaga_ids: vagaIds });
  return data;
}

export async function atualizarVagaUsuario(vagaId: string, body: Partial<{ notas: string; ignorada: boolean; arquivada: boolean; salva: boolean }>): Promise<{ ok: boolean }> {
  const { data } = await api.patch(`/api/v1/vagas-usuarios/${vagaId}`, body);
  return data;
}

export async function obterVaga(id: string): Promise<Vaga> {
  const { data } = await api.get<Vaga>(`/api/v1/vagas/${id}`);
  return data;
}

export async function coletarAgora(termos?: string[]): Promise<{
  total_brutas: number;
  novas_inseridas: number;
  filtradas_irrelevantes: number;
}> {
  const body = termos ? { termos } : undefined;
  const { data } = await api.post("/api/v1/sistema/coletar-agora", body);
  return data;
}

export async function limparVagasIrrelevantes(): Promise<{
  total_antes: number;
  removidas: number;
  total_depois: number;
  protegidas_pipeline: number;
}> {
  const { data } = await api.post("/api/v1/sistema/limpar-vagas");
  return data;
}

export async function analisarVagaIA(id: string): Promise<{ analise_ia: AnaliseIA | null }> {
  const { data } = await api.post(`/api/v1/analise/vagas/${id}/analisar-ia`);
  return data;
}

export async function obterAnalise(id: string): Promise<{
  analise_offline: AnaliseOffline;
  analise_ia: AnaliseIA | null;
  score: number;
}> {
  const { data } = await api.get(`/api/v1/analise/vagas/${id}/analise`);
  return data;
}

export async function obterPerfil(): Promise<PerfilUsuario | null> {
  const { data } = await api.get("/api/v1/perfil/");
  return data;
}

export async function salvarPerfil(perfil: PerfilUsuario): Promise<PerfilUsuario> {
  const { data } = await api.put("/api/v1/perfil/", perfil);
  return data;
}

export interface Candidatura {
  id: string;
  vaga_id: string;
  vaga_titulo: string;
  empresa: string;
  status: string;
  score_no_momento: number;
  curriculo_gerado: boolean;
  curriculo_path: string | null;
  observacoes: string | null;
  criada_em: string;
  atualizada_em: string;
}

export interface CandidaturaStats {
  salva: number;
  candidatada: number;
  entrevista: number;
  rejeitada: number;
  aprovada: number;
}

export async function listarCandidaturas(status?: string): Promise<Candidatura[]> {
  const params = status ? { status } : {};
  const { data } = await api.get<Candidatura[]>("/api/v1/candidaturas/", { params });
  return data;
}

export async function candidatarVaga(vagaId: string, observacoes?: string): Promise<Candidatura> {
  const params: Record<string, string> = {};
  if (observacoes) params.observacoes = observacoes;
  const { data } = await api.post<Candidatura>(`/api/v1/candidaturas/${vagaId}`, null, { params });
  return data;
}

export async function atualizarStatusCandidatura(candidaturaId: string, status: string): Promise<Candidatura> {
  const { data } = await api.patch<Candidatura>(`/api/v1/candidaturas/${candidaturaId}/status`, null, { params: { status } });
  return data;
}

export async function estatisticasCandidaturas(): Promise<CandidaturaStats> {
  const { data } = await api.get<CandidaturaStats>("/api/v1/candidaturas/estatisticas");
  return data;
}

export async function seedPerfil(): Promise<{ message: string }> {
  const { data } = await api.post("/api/v1/seed/perfil");
  return data;
}

export interface StackCount {
  stack: string;
  count: number;
}

export interface SalarioPorStack {
  stack: string;
  count: number;
  salario_medio_min: number;
  salario_medio_max: number;
}

export interface FonteCount {
  fonte: string;
  count: number;
}

export interface SenioridadeCount {
  nivel: string;
  count: number;
}

export interface TimelinePoint {
  data: string;
  count: number;
}

export interface AlertaVaga {
  id: string;
  titulo: string;
  empresa: string;
  score: number;
  url: string;
}

export interface Overview {
  total_vagas: number;
  fake_junior_count: number;
  score_medio: number;
  alertas: AlertaVaga[];
}

export async function getStacksMaisPedidas(limit = 15): Promise<StackCount[]> {
  const { data } = await api.get<StackCount[]>("/api/v1/analytics/stacks", { params: { limit } });
  return data;
}

export async function getMediaSalarial(limit = 15): Promise<SalarioPorStack[]> {
  const { data } = await api.get<SalarioPorStack[]>("/api/v1/analytics/salarios", { params: { limit } });
  return data;
}

export async function getVagasPorFonte(): Promise<FonteCount[]> {
  const { data } = await api.get<FonteCount[]>("/api/v1/analytics/fontes");
  return data;
}

export async function getVagasPorSenioridade(): Promise<SenioridadeCount[]> {
  const { data } = await api.get<SenioridadeCount[]>("/api/v1/analytics/senioridade");
  return data;
}

export interface ChatAnalytics {
  total_sessoes: number;
  total_mensagens: number;
  sessoes_hoje: number;
  media_mensagens_por_sessao: number;
  tools_executadas: Record<string, number>;
  tools_resultados: Record<string, number>;
  atividade_diaria: { data: string; mensagens: number }[];
}

export async function getChatAnalytics(): Promise<ChatAnalytics> {
  const { data } = await api.get<ChatAnalytics>("/api/v1/analytics/chat");
  return data;
}

export async function getTimeline(dias = 30): Promise<TimelinePoint[]> {
  const { data } = await api.get<TimelinePoint[]>("/api/v1/analytics/timeline", { params: { dias } });
  return data;
}

export interface FonteScore {
  fonte: string;
  count: number;
  score_medio: number;
  score_max: number;
}

export interface SkillCount {
  skill: string;
  count: number;
}

export async function getScorePorFonte(): Promise<FonteScore[]> {
  const { data } = await api.get<FonteScore[]>("/api/v1/analytics/fontes-score");
  return data;
}

export async function getSkillsPopulares(limit = 15): Promise<SkillCount[]> {
  const { data } = await api.get<SkillCount[]>("/api/v1/analytics/skills", { params: { limit } });
  return data;
}

export async function getOverview(): Promise<Overview> {
  const { data } = await api.get<Overview>("/api/v1/analytics/overview");
  return data;
}

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get("/api/v1/sistema/health");
  return data;
}

/* ══════════════════════════════════════════════════════════════
   CURRÍCULO / RESUME
   ══════════════════════════════════════════════════════════════ */

import type { Curriculo } from "@/types/curriculo";

export interface CurriculoContatos {
  email?: string;
  telefone?: string;
  linkedin?: string;
}

export interface OtimizacaoResultado {
  resumo_otimizado: string;
  stacks_priorizadas: string[];
  experiencias_otimizadas: { empresa: string; cargo: string; descricao_otimizada: string }[];
  projetos_destacados: string[];
  mudancas_feitas: string[];
  nota_honestidade: string;
  vaga_titulo?: string;
  vaga_empresa?: string;
}

export interface EmailOutreachResultado {
  email_encontrado_na_vaga: string | null;
  email_gerado_por_ia: {
    assunto: string;
    corpo: string;
    nota_plataforma: string;
  } | null;
  repo_url: string;
}

export async function uploadCurriculo(file: File): Promise<Curriculo> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<{ data: Curriculo }>("/api/v1/curriculo/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  });
  return data.data;
}

export async function obterCurriculo(): Promise<Curriculo | null> {
  const { data } = await api.get<{ data: Curriculo }>("/api/v1/curriculo/");
  return data.data;
}

export async function otimizarCurriculo(
  vagaId: string,
  instrucoes?: string
): Promise<OtimizacaoResultado> {
  const params: Record<string, string> = {};
  if (instrucoes) params.instrucoes = instrucoes;
  const { data } = await api.post(`/api/v1/curriculo/otimizar/${vagaId}`, null, {
    params,
    timeout: 120000,
  });
  return data;
}

export async function obterOtimizacao(vagaId: string): Promise<OtimizacaoResultado> {
  const { data } = await api.get(`/api/v1/curriculo/otimizar/${vagaId}`);
  return data;
}

export async function gerarEmailOutreach(vagaId: string): Promise<EmailOutreachResultado> {
  const { data } = await api.post(`/api/v1/curriculo/email/${vagaId}`, null, {
    timeout: 120000,
  });
  return data;
}

export async function obterEmailOutreach(vagaId: string): Promise<EmailOutreachResultado> {
  const { data } = await api.get(`/api/v1/curriculo/email/${vagaId}`);
  return data;
}

export interface PipelineItem {
  id: string;
  vaga_id: string;
  vaga_titulo: string;
  empresa: string;
  fonte: string;
  score: number;
  url: string;
  etapa: string;
  curriculo_gerado: boolean;
  curriculo_path: string | null;
  curriculo_versao_id: string | null;
  aplicada_em: string | null;
  notas: string;
  proxima_acao: string | null;
  proxima_data: string | null;
  created_at: string;
  updated_at: string;
  historico: { etapa: string; data: string; observacao: string | null }[];
}

export interface PipelineStats {
  salva: number;
  aplicada: number;
  em_analise: number;
  entrevista_rh: number;
  entrevista_tecnica: number;
  teste_tecnico: number;
  contratado: number;
  rejeitado: number;
  total: number;
  taxa_conversao: number;
  taxa_rejeicao: number;
}

export async function criarPipeline(vagaId: string, etapa?: string, curriculoVersaoId?: string): Promise<PipelineItem> {
  const params: Record<string, string> = {};
  if (etapa) params.etapa = etapa;
  if (curriculoVersaoId) params.curriculo_versao_id = curriculoVersaoId;
  const { data } = await api.post(`/api/v1/pipeline/${vagaId}`, null, { params });
  return data;
}

export async function listarPipeline(etapa?: string): Promise<PipelineItem[]> {
  const params = etapa ? { etapa } : {};
  const { data } = await api.get<PipelineItem[]>("/api/v1/pipeline/", { params });
  return data;
}

export async function avancarEtapaPipeline(pipelineId: string, etapa: string, observacao?: string): Promise<PipelineItem> {
  const params: Record<string, string> = { etapa };
  if (observacao) params.observacao = observacao;
  const { data } = await api.patch(`/api/v1/pipeline/${pipelineId}/etapa`, null, { params });
  return data;
}

export async function atualizarPipeline(pipelineId: string, body: Partial<{ notas: string; proxima_acao: string; proxima_data: string }>): Promise<PipelineItem> {
  const { data } = await api.patch(`/api/v1/pipeline/${pipelineId}`, body);
  return data;
}

export async function deletarPipeline(pipelineId: string): Promise<{ ok: boolean }> {
  const { data } = await api.delete(`/api/v1/pipeline/${pipelineId}`);
  return data;
}

export async function pipelineEstatisticas(): Promise<PipelineStats> {
  const { data } = await api.get<PipelineStats>("/api/v1/pipeline/estatisticas");
  return data;
}

export async function listarPipelinePorCurriculo(curriculoId: string): Promise<PipelineItem[]> {
  const { data } = await api.get<PipelineItem[]>(`/api/v1/pipeline/curriculo/${curriculoId}`);
  return data;
}

export interface EventoCalendario {
  id: string;
  pipeline_id: string | null;
  vaga_id: string;
  empresa: string;
  titulo: string;
  tipo: string;
  data_inicio: string;
  data_fim: string | null;
  descricao: string;
  local: string;
  url: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export async function listarEventos(params?: { de?: string; ate?: string; pipeline_id?: string }): Promise<EventoCalendario[]> {
  const { data } = await api.get<EventoCalendario[]>("/api/v1/eventos/", { params });
  return data;
}

export async function criarEvento(body: {
  vaga_id: string;
  empresa: string;
  titulo: string;
  tipo: string;
  data_inicio: string;
  data_fim?: string;
  descricao?: string;
  local?: string;
  url?: string;
}): Promise<EventoCalendario> {
  const { data } = await api.post<EventoCalendario>("/api/v1/eventos/", body);
  return data;
}

export async function atualizarEvento(eventoId: string, body: Partial<{ data_inicio: string; data_fim: string; descricao: string; local: string; status: string; tipo: string }>): Promise<EventoCalendario> {
  const { data } = await api.patch<EventoCalendario>(`/api/v1/eventos/${eventoId}`, body);
  return data;
}

export async function deletarEvento(eventoId: string): Promise<void> {
  await api.delete(`/api/v1/eventos/${eventoId}`);
}

export async function cleanupEventosOrfaos(): Promise<{ removidos: number }> {
  const { data } = await api.post<{ removidos: number }>("/api/v1/eventos/cleanup-orphans");
  return data;
}

export async function syncPipelineEventos(): Promise<EventoCalendario[]> {
  const { data } = await api.post<EventoCalendario[]>("/api/v1/eventos/sync-pipeline");
  return data;
}

/* ══════════════════════════════════════════════════════════════
   AI PROVIDER
   ══════════════════════════════════════════════════════════════ */

export interface ProviderInfo {
  current: string;
  available: string[];
  models: Record<string, string>;
}

export async function getProvider(): Promise<ProviderInfo> {
  const { data } = await api.get<ProviderInfo>("/api/v1/ai/provider");
  return data;
}

export async function setProvider(provider: string): Promise<ProviderInfo> {
  const { data } = await api.post<ProviderInfo>("/api/v1/ai/provider", { provider });
  return data;
}

/* ══════════════════════════════════════════════════════════════
   CHAT IA
   ══════════════════════════════════════════════════════════════ */

export interface ChatSession {
  id: string;
  titulo: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  sessao_id: string;
  papel: "user" | "assistant" | "system";
  conteudo: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export async function criarSessaoChat(titulo?: string): Promise<ChatSession> {
  const { data } = await api.post<ChatSession>("/api/v1/ai/chat/sessions", {
    titulo: titulo || "Nova conversa",
  });
  return data;
}

export async function listarSessoesChat(): Promise<ChatSession[]> {
  const { data } = await api.get<ChatSession[]>("/api/v1/ai/chat/sessions");
  return data;
}

export async function deletarSessaoChat(sessaoId: string): Promise<void> {
  await api.delete(`/api/v1/ai/chat/sessions/${sessaoId}`);
}

export async function atualizarSessaoChat(sessaoId: string, titulo: string): Promise<ChatSession> {
  const { data } = await api.patch<ChatSession>(`/api/v1/ai/chat/sessions/${sessaoId}`, { titulo });
  return data;
}

export async function listarMensagensChat(sessaoId: string): Promise<ChatMessage[]> {
  const { data } = await api.get<ChatMessage[]>(`/api/v1/ai/chat/sessions/${sessaoId}/messages`);
  return data;
}

export async function enviarMensagemChat(
  sessaoId: string,
  mensagem: string,
  onToken: (token: string) => void,
  onDone?: () => void,
  onError?: (error: string) => void,
  onToolStart?: (tool: string, params: string) => void,
  onToolResult?: (result: Record<string, unknown>) => void,
  vagaId?: string,
  onReasoning?: (token: string) => void,
): Promise<void> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8070";
  const url = `${baseUrl}/api/v1/ai/chat/sessions/${sessaoId}/send`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensagem, vaga_id: vagaId }),
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => "Erro desconhecido");
    onError?.(errText);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError?.("Stream não disponível");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";
  let completed = false;

  const handleData = (data: Record<string, unknown>, event: string) => {
    if (event === "tool_start") {
      onToolStart?.(data.tool as string, (data.params as string) || "");
    } else if (event === "tool_result") {
      onToolResult?.(data);
    } else if (event === "done") {
      completed = true;
      onDone?.();
    } else if (event === "error") {
      completed = true;
      onError?.((data.error as string) || "Erro desconhecido");
    } else {
      if (data.type === "reasoning") {
        onReasoning?.(data.token as string);
      } else if (data.token) {
        onToken(data.token as string);
      }
      if (data.event === "tool_start") {
        onToolStart?.(data.tool as string, (data.params as string) || "");
      }
      if (data.event === "tool_result") {
        onToolResult?.(data);
      }
      if (data.event === "done" || data.done) {
        completed = true;
        onDone?.();
      }
      if (data.error) {
        completed = true;
        onError?.((data.error as string) || "Erro desconhecido");
      }
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith("event: ")) {
          currentEvent = trimmed.slice(7).trim();
        } else if (trimmed.startsWith("data: ")) {
          const dataStr = trimmed.slice(6).trim();
          try {
            const data = JSON.parse(dataStr);
            handleData(data, currentEvent);
          } catch {
            // ignorar JSON malformado
          }
          currentEvent = "";
        }
      }
    }

    // Process remaining buffer after stream ends
    if (buffer.trim()) {
      const trimmedBuffer = buffer.trim();
      if (trimmedBuffer.startsWith("data: ")) {
        try {
          const data = JSON.parse(trimmedBuffer.slice(6).trim());
          handleData(data, currentEvent);
        } catch {
          // skip
        }
      }
    }

    // Garantir que onDone seja chamado mesmo sem evento explícito
    if (!completed) {
      completed = true;
      onDone?.();
    }
  } catch (err) {
    if (!completed) {
      completed = true;
      onError?.(String(err));
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   AI TOOLS - RESULTADOS PERSISTIDOS
   ══════════════════════════════════════════════════════════════ */

export interface MatchResult {
  id: string;
  vaga_id: string;
  score_geral: number;
  score_tecnico: number;
  score_experiencia: number;
  score_soft_skills: number;
  skills_match: { skill: string; nivel_vaga: string; nivel_usuario: string }[];
  missing_skills: string[];
  gaps: { area: string; descricao: string; impacto: string }[];
  chance_entrevista: string;
  created_at: string;
}

export interface VagaAnalysisResult {
  id: string;
  vaga_id: string;
  stack_principal: string[];
  nivel: string;
  salario_estimado_min: number | null;
  salario_estimado_max: number | null;
  resumo: string;
  requisitos_obrigatorios: { descricao: string; tipo: string }[];
  requisitos_desejaveis: { descricao: string; tipo: string }[];
  soft_skills: string[];
  palavras_chave_ats: string[];
  created_at: string;
}



export interface CurriculoVersao {
  id: string;
  vaga_id: string | null;
  versao: number;
  conteudo_original: Record<string, unknown>;
  conteudo_otimizado: Record<string, unknown>;
  changes_log: { tipo: string; descricao: string }[];
  created_at: string;
}

export async function obterMatchResultado(vagaId: string): Promise<MatchResult | null> {
  try {
    const { data } = await api.get<MatchResult | null>(`/api/v1/analise/match/${vagaId}`);
    return data;
  } catch {
    return null;
  }
}

export async function obterAnaliseVaga(vagaId: string): Promise<VagaAnalysisResult | null> {
  try {
    const { data } = await api.get<VagaAnalysisResult | null>(`/api/v1/analise/vaga/${vagaId}`);
    return data;
  } catch {
    return null;
  }
}

export interface AnaliseCompleta {
  vaga: Vaga;
  analise: VagaAnalysisResult | null;
  match: {
    score: number | null;
    detalhes: {
      score_tecnico: number;
      score_experiencia: number;
      score_soft_skills: number;
      skills_match: { skill: string; nivel_vaga: string; nivel_usuario: string }[];
      missing_skills: string[];
      gaps: { area: string; descricao: string; impacto: string }[];
      chance_entrevista: string;
    } | null;
    analisado_em: string | null;
  } | null;
  status: {
    salva: boolean;
    aplicada: boolean;
    favoritada: boolean;
    analisada: boolean;
  } | null;
  pipeline: string | null;
}

export async function obterAnaliseCompleta(vagaId: string): Promise<AnaliseCompleta | null> {
  try {
    const { data } = await api.get<AnaliseCompleta>(`/api/v1/analise/completa/${vagaId}`);
    return data;
  } catch {
    return null;
  }
}

export async function obterMatchesBulk(vagaIds: string[]): Promise<Record<string, { score: number | null; analisado: boolean }>> {
  try {
    const { data } = await api.post<Record<string, { score: number | null; analisado: boolean }>>("/api/v1/analise/match/bulk", { vaga_ids: vagaIds });
    return data;
  } catch {
    return {};
  }
}

export async function atualizarCurriculo(versaoId: string, dados: Record<string, unknown>): Promise<{ success: boolean; data: Curriculo }> {
  const { data } = await api.put(`/api/v1/curriculo/${versaoId}`, dados);
  return data;
}

export async function deletarVersaoCurriculo(versaoId: string): Promise<{ success: boolean }> {
  const { data } = await api.delete(`/api/v1/curriculo/versoes/${versaoId}`);
  return data;
}

export async function duplicarVersaoCurriculo(versaoId: string): Promise<{ success: boolean; data: Curriculo }> {
  const { data } = await api.post(`/api/v1/curriculo/versoes/${versaoId}/duplicar`);
  return data;
}

export async function renomearVersaoCurriculo(versaoId: string, nome: string): Promise<{ success: boolean; data: Curriculo }> {
  const { data } = await api.put(`/api/v1/curriculo/versoes/${versaoId}/renomear`, { nome });
  return data;
}

export async function setPadraoCurriculo(versaoId: string): Promise<{ success: boolean; data: Curriculo }> {
  const { data } = await api.post(`/api/v1/curriculo/versoes/${versaoId}/set-padrao`);
  return data;
}

/* ══════════════════════════════════════════════════════════════
   EMAIL (IMAP/SMTP)
   ══════════════════════════════════════════════════════════════ */

export interface EmailConfig {
  configured: boolean;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  email_user: string;
  email_from: string;
  check_interval_minutes: number;
}

export interface EmailRecebido {
  id: string;
  assunto: string;
  de: string;
  de_email: string;
  data_recebida: string | null;
  corpo_preview: string;
  tipo: string;
  vaga_id: string | null;
  vaga_titulo: string | null;
  pipeline_id: string | null;
  created_at: string;
  lida: boolean;
}

export async function obterConfigEmail(): Promise<EmailConfig> {
  const { data } = await api.get<EmailConfig>("/api/v1/notifications/email");
  return data;
}

export async function testarConexaoEmail(): Promise<{
  ok: boolean;
  conexao_imap: boolean;
  emails_encontrados: number;
  ultimos: { assunto: string; de: string; data: string }[];
}> {
  const { data } = await api.post("/api/v1/notifications/email/testar");
  return data;
}

export async function sincronizarEmail(): Promise<{
  ok: boolean;
  importados: number;
  emails: EmailRecebido[];
}> {
  const { data } = await api.post("/api/v1/notifications/email/sync");
  return data;
}

export async function listarEmailsRecebidos(params?: {
  tipo?: string;
  lida?: boolean;
  limit?: number;
}): Promise<EmailRecebido[]> {
  const { data } = await api.get<EmailRecebido[]>("/api/v1/notifications/email/mensagens", { params });
  return data;
}

export async function marcarEmailLido(emailId: string): Promise<{ ok: boolean }> {
  const { data } = await api.patch(`/api/v1/notifications/email/${emailId}/ler`);
  return data;
}
