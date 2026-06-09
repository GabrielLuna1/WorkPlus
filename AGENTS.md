# WorkHunter — Contexto para Agentes

## Stack
- **Backend**: FastAPI + MongoDB 7 + Python 3.11 (porta 8070)
- **Frontend**: Next.js 15 + Tailwind CSS v3 + TypeScript (porta 3000)
- **Design**: Dark theme, metallic-gold accent, Poppins headings

## Estrutura de Dados

### Collections
- `vagas` — Vagas brutas coletadas dos integradores
- `vagas_usuarios` — Interação do usuário com cada vaga
- `pipeline` — Candidaturas em andamento (8 etapas)
- `eventos` — Eventos de calendário
- `chat_sessoes` — Sessões de conversa
- `chat_mensagens` — Mensagens de cada sessão
- `vaga_analysis` — Resultados de analyze_vaga
- `match_results` — Resultados de calcular_match
- `curriculo_versoes` — Versões de currículo otimizadas
### Relação entre collections
```
vagas_usuarios.vaga_id → vagas._id (M:1)
pipeline.vaga_id → vagas._id (M:1)
eventos.pipeline_id → pipeline._id (1:1 opcional)
```

## Endpoints

### Chat IA (`/api/v1/ai/chat/`)
- `POST /sessions` — Criar sessão
- `GET /sessions` — Listar
- `PATCH /sessions/{id}` — Renomear
- `DELETE /sessions/{id}` — Deletar + mensagens
- `GET /sessions/{id}/messages` — Histórico
- `POST /sessions/{id}/send` — Enviar + SSE streaming (eventos: token, tool_start, tool_result, done, error)

### AI Analysis (`/api/v1/analise/`)
- `GET /match/{vaga_id}` — Match result persistido
- `GET /vaga/{vaga_id}` — Análise persistida
- `POST /match/bulk` — Bulk match scores (body: { vaga_ids: string[] })
- `GET /completa/{vaga_id}` — Vaga + analysis + match + status + pipeline

### Analytics (`/api/v1/analytics/`)
- `GET /stacks` — Stacks mais pedidas
- `GET /salarios` — Média salarial por stack
- `GET /fontes` — Vagas por fonte
- `GET /senioridade` — Vagas por senioridade
- `GET /timeline` — Vagas por dia (30d)
- `GET /overview` — Overview (total, fake jr, score médio, alertas)
- `GET /chat` — Chat analytics (sessões, mensagens, tools)
- `GET /fontes-score` — Score médio por fonte (score_medio, score_max)
- `GET /skills` — Skills mais populares

### Vagas (`/api/v1/vagas/`)
- `GET /` — Lista paginada com busca, ordenação, filtros
- `GET /{id}` — Vaga individual com usuario_status

### Pipeline (`/api/v1/pipeline/`)
- `POST /{vaga_id}` — Criar entrada (default: "salva")
- `GET /` — Listar (filtro opcional por etapa)
- `PATCH /{id}/etapa` — Avançar etapa
- `PATCH /{id}` — Atualizar notas, proxima_acao, proxima_data
- `GET /estatisticas` — Contagem por etapa + taxas

## Chat IA Tools
6 ferramentas via `[TOOL:nome|params]` no final da resposta do LLM:
1. **analyze_vaga|id** — Análise profunda (stack, salário, reqs, ATS, soft skills) → salva em `vaga_analysis`
2. **calcular_match|id** — Score de compatibilidade (técnico, experiência, soft) → salva em `match_results`
3. **pipeline_status** — Status do pipeline
4. **otimizar_curriculo|id** — Otimiza currículo → salva em `curriculo_versoes`
5. **gerar_cover_letter|id** — Gera cover letter

## Frontend — Rotas
- `/` — Discovery (vagas grid/lista)
- `/hub` — Copilot Hub (3 colunas redimensionáveis: sessões | chat | contexto)
  - Mini vaga browser integrado (busca + scroll infinito)
  - Keyboard shortcuts: Ctrl+N, Ctrl+L, Ctrl+Shift+B, ?
  - ResizablePanel com persistência em localStorage
- `/kanban` — Pipeline Kanban (8 colunas, drag & drop)
- `/vagas` — Lista com filtros
- `/analise/vaga/[id]` — Análise completa da vaga
- `/curriculo` — Upload e gerenciamento
- `/curriculo/versoes` — Histórico de versões com diff
- `/analytics` — Radar de Mercado + Chat Analytics
- `/calendar` — Calendário de eventos

## Regras de UI
- Toda página client-side com `"use client"`
- Ícones: lucide-react
- Utilitário: `cn()` de `@/lib/utils` (clsx + tailwind-merge)
- Loading state: Loader2 com animate-spin
- Empty state: AlertCircle + mensagem descritiva
- URLs como searchParams (single source of truth para filtros)
- Score ring com cores: success (≥80), accent (≥60), warning (≥40), danger (<40)
- Match badge com cores: success (≥70), accent (≥50), danger (<50)
- Sidebar: w-[280px], links com `text-[15px]` e `px-4 py-2.5`, ícones `w-5 h-5`
- Títulos: `text-xl font-semibold metallic-gradient tracking-tight` com Poppins
- Chat bubble: user = `bg-accent/15 text-ink rounded-br-md`, IA = `bg-surface-2 border border-hairline text-ink rounded-bl-md`

## Telegram Notifications
- `services/telegram_bot.py` — Envio de mensagens via Bot API (match, pipeline, resumo diário)
- `api/notifications.py` — Config CRUD + testar (GET/PUT/POST)
- `components/ai/TelegramSettings.tsx` — Modal de configuração no frontend
- Gatilhos: pós-coleta (match ≥85), ao avançar pipeline, resumo diário às 8h (Celery Beat)
- Requer `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no .env

## Provider IA
- Primário: LM Studio (`http://127.0.0.1:1234`, model `qwen-3.6-35b-a3b`)
- Chat temperature 0.7, tasks analíticas 0.1-0.3

## Comandos úteis
```bash
# Frontend
cd frontend && npx next dev       # Dev server
cd frontend && npx next build      # Production build + type check
cd frontend && npx tsc --noEmit    # Type check only

# Backend
cd backend && python main.py       # Start FastAPI (porta 8070)
```
