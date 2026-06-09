<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,100:d4af37&height=200&section=header&text=WORKPLUS&fontSize=60&fontColor=d4af37&animation=fadeIn&fontAlignY=35">
    <img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,100:d4af37&height=200&section=header&text=WORKPLUS&fontSize=60&fontColor=d4af37&animation=fadeIn&fontAlignY=35" width="100%">
  </picture>
</p>

<div align="center">

# WorkHunter

### *Sua plataforma inteligente de busca e gestão de vagas tech*

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![MongoDB](https://img.shields.io/badge/MongoDB_7-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_v3-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)]()
[![Status: Active](https://img.shields.io/badge/Status-Active-2ea44f?style=flat-square)]()
[![AI: Local](https://img.shields.io/badge/AI-Local_LLM-8B5CF6?style=flat-square)]()

> WorkHunter centraliza vagas de tecnologia de 12 fontes, aplica match score por IA local e organiza tudo em um pipeline kanban — coleta, analisa e acompanha oportunidades sem você precisar visitar dezenas de sites manualmente.
>
> ⚠️ O WorkHunter **não envia currículos, não preenche formulários e não se candidata automaticamente**. Todo o processo de aplicação é manual e intencional, feito diretamente no site de cada empresa. O sistema cuida da etapa anterior: a inteligência de mercado, a triagem e a organização — para que você chegue ao momento de aplicar já com informação suficiente para decidir se aquela vaga vale seu tempo.
>
> 📌 **Aviso Legal:** WorkHunter é um projeto **open source educacional**, não afiliado a nenhuma das plataformas ou portais listados. O sistema opera com limites responsáveis de requisições e respeito a `robots.txt`. Cada usuário é responsável por verificar os Termos de Serviço das fontes que utiliza. Nenhum dado pessoal é enviado a servidores externos — toda a IA roda localmente via LM Studio.

[⚡ Quick Start](#-quick-start) •
[🧠 Features](#-features) •
[📡 Fontes](#-fontes) •
[🏗️ Arquitetura](#️-arquitetura) •
[🖥️ Interface](#️-interface) •
[🛠️ Stack](#️-stack)

---

</div>

## 📋 Sobre o Projeto

O WorkHunter é uma plataforma pessoal de busca e gestão de vagas de tecnologia, construída para automatizar todo o processo de encontrar, avaliar e acompanhar oportunidades de emprego. Em vez de visitar dezenas de sites manualmente, o sistema faz isso de forma contínua em segundo plano e entrega apenas as vagas mais relevantes, já analisadas e pontuadas.

### Coleta de Vagas

O sistema acessa **12 fontes diferentes** — incluindo APIs públicas de plataformas de recrutamento, portais de emprego e sites de carreira corporativos. Após a coleta, as vagas passam por:
- Deduplicação (evita repetições entre fontes)
- Filtragem de relevância (baseada no perfil do usuário)
- Filtragem geográfica (apenas vagas brasileiras)
- Extração automática do modelo de trabalho (remoto, híbrido, presencial) e estado (UF)

### Pontuação e Análise

Cada vaga recebe automaticamente uma **pontuação de 0 a 100** calculada com base em título, stack tecnológica, salário, tipo de contrato, localização e reputação da fonte. O sistema também detecta automaticamente vagas "fake júnior" — aquelas com título de nível júnior mas que exigem experiência de sênior na descrição.

Para vagas de interesse, uma análise mais profunda pode ser solicitada via IA, gerando resumo da oportunidade, nível de senioridade real, stack principal estimada, score de compatibilidade personalizado e sugestões de desenvolvimento.

### Gestão de Currículo

- Upload de currículo em **PDF ou DOCX**
- Extração automática via IA para montar perfil estruturado (habilidades, experiências, preferências)
- Perfil calibra os scores de match e os termos de busca das coletas
- **Versionamento completo**: múltiplas versões, histórico de alterações, restauração e exportação

### Notificações

| Tipo | Gatilho | Canal |
|------|---------|-------|
| Alerta de vaga | Score ≥ 85 | Telegram (link direto) |
| Resumo diário | Todos os dias às 8h | Telegram (melhores vagas do dia anterior) |

---

## 🧠 Features

| | Feature | Descrição |
|:-:|---------|-----------|
| 🤖 | **Coleta de Vagas** | Busca manual em diversas fontes com um clique — você decide quando iniciar |
| 📊 | **Match Score IA** | Pontuação 0-100 por título, stack, salário, tipo, localização e fonte |
| 🧪 | **Fake Júnior Detection** | Detecta vagas que pedem requisitos de sênior mas se intitulam júnior |
| 📄 | **Currículo Inteligente** | Upload PDF/DOCX → extração automática → versionamento com diff → export |
| 💬 | **Copilot de Carreira** | Chat IA com análise de vagas, match, pipeline, busca e cover letter |
| 📋 | **Pipeline Kanban** | 8 estágios drag-and-drop com histórico e estatísticas de conversão |
| 📈 | **Radar de Mercado** | Stacks mais pedidas, salários por tecnologia, skills populares, timeline |
| 📱 | **Telegram Bot** | Notificações de match ≥85% e resumo diário às 8h |
| 📅 | **Calendário de Entrevistas** | Agende e visualize entrevistas, prazos e eventos vinculados ao pipeline |
| 🔍 | **Filtro Inteligente** | Relevância por perfil, filtro geográfico, extração automática de UF e modelo de trabalho |

---

## 📡 Fontes

O WorkHunter consulta vagas de tecnologia através de plataformas abertas e portais de emprego:

| | Fonte | Tipo |
|:-:|-------|------|
| <img src="https://www.google.com/s2/favicons?domain=greenhouse.io&sz=16" width="16"> | **Greenhouse** | Plataforma de recrutamento |
| <img src="https://www.google.com/s2/favicons?domain=lever.co&sz=16" width="16"> | **Lever** | Plataforma de recrutamento |
| <img src="https://www.google.com/s2/favicons?domain=workable.com&sz=16" width="16"> | **Workable** | Plataforma de recrutamento |
| <img src="https://www.google.com/s2/favicons?domain=gupy.io&sz=16" width="16"> | **Gupy** | Plataforma de recrutamento |
| <img src="https://www.google.com/s2/favicons?domain=infojobs.com.br&sz=16" width="16"> | **InfoJobs** | Portal de empregos |
| <img src="https://www.google.com/s2/favicons?domain=vagas.com.br&sz=16" width="16"> | **Vagas.com.br** | Portal de empregos |
| <img src="https://www.google.com/s2/favicons?domain=apinfo.com&sz=16" width="16"> | **APInfo** | Portal de empregos |
| <img src="https://www.google.com/s2/favicons?domain=programathor.com.br&sz=16" width="16"> | **Programathor** | Portal de empregos tech |
| <img src="https://www.google.com/s2/favicons?domain=99jobs.com&sz=16" width="16"> | **99Jobs** | Portal de empregos |
| <img src="https://www.google.com/s2/favicons?domain=myworkdayjobs.com&sz=16" width="16"> | **Workday** | Plataforma de recrutamento |
| <img src="https://www.google.com/s2/favicons?domain=taqe.com.br&sz=16" width="16"> | **Taqe** | Plataforma de recrutamento |
| <img src="https://www.google.com/s2/favicons?domain=bancointer.com.br&sz=16" width="16"> | **Próprio ATS** | Sites de carreira corporativos |

---

## 🏗️ Arquitetura

```mermaid
graph TB
    subgraph Frontend ["Frontend — Next.js 15 · TypeScript · Tailwind"]
        DISC["/ — Discovery"]
        HUB["/hub — Copilot Hub"]
        KANBAN["/kanban — Pipeline"]
        ANALYTICS["/analytics — Market Radar"]
        CURRICULO["/curriculo — Gestão"]
        CAL["/calendar — Eventos"]
    end

    subgraph Backend ["Backend — FastAPI · Python 3.11"]
        API["REST API — 16 Routers"]
        AI["AI Client — LM Studio"]
        CHAT["Chat IA — SSE Streaming + Tools"]
        TELEGRAM["Telegram Bot"]
        CELERY["Celery Tasks — Coleta 2/2h"]
    end

    subgraph Data ["Data Layer"]
        MONGODB[("MongoDB 7<br/>vagas · pipeline · chat<br/>curriculos · analytics")]
        REDIS[("Redis — Broker Celery")]
    end

    subgraph Integrations ["Integrações"]
        API_COL["APIs Públicas"]
        WEB_COL["Portais de Emprego"]
        ATS_COL["Sites de Carreira"]
    end

    Frontend <-->|"REST + SSE"| API
    API --> AI
    API --> TELEGRAM
    API --> CELERY
    API --> MONGODB
    CELERY --> REDIS
    CELERY --> Integrations

    AI -->|"LM Studio :1234"| LMSTUDIO["LM Studio — LLM Local"]

    style LMSTUDIO fill:#2d1b69,stroke:#8B5CF6,stroke-width:2px
```

### Fluxo de Coleta

```
Perfil do Usuário (termos de busca)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  APIs Públicas (Gupy, Greenhouse, Lever, Workable)   │
│  Portais de Emprego (InfoJobs, Vagas.com, APInfo)    │
│  Sites de Carreira (Workday, Taqe, entre outros)     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Deduplicação por hash                                │
│  Filtro de Relevância (perfil do usuário)             │
│  Filtro Geográfico (apenas Brasil)                    │
│  Extração de UF e Modelo de Trabalho                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Match Score (0-100)                                  │
│  Fake Júnior Detection                                │
│  Notificação Telegram (score ≥ 85)                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
                  MongoDB (workplus)
```

---

## 🔄 Fluxo do Usuário

### Visão Macro — Navegação entre Módulos

```mermaid
flowchart TB
  subgraph NAV["🧭 Sidebar (280px fixa)"]
    direction TB
    n1["Discovery /"]
    n2["Copilot /hub"]
    n3["Pipeline /kanban"]
    n4["Vagas /vagas"]
    n5["Currículo /curriculo"]
    n6["Analytics /analytics"]
    n7["Calendário /calendar"]
  end

  subgraph CROSS["Conexões entre Módulos"]
    direction LR

    n1 -- "Explorar Todas →" --> n4
    n1 -- "Ver Kanban →" --> n3
    n1 -- "Salvar vaga" --> n3

    n4 -- "Analisar → abre chat\ncom contexto da vaga" --> n2
    n4 -- "Salvar / Aplicar" --> n3

    n2 -- "analyze_vaga\ncalcular_match" --> DB_ANALYSIS[("vaga_analysis\nmatch_results")]
    n2 -- "pipeline_status" --> n3
    n2 -- "Usa CV ativo" --> n5

    n3 -- "proxima_data →\nsync eventos" --> n7
    n3 -- "Avançar etapa →\nTelegram" --> TG["📱 Telegram"]

    n5 -- "CV ativo →\nmatch + cover letter" --> n2

    n6 -- "Dados agregados de" --> n4
    n6 -- "Dados agregados de" --> n3
    n6 -- "Config Telegram" --> TG

    n7 -- "Eventos sincronizados\ndo Pipeline" --> n3
  end

  style NAV fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style CROSS fill:#0d1117,stroke:#30363d,color:#f0f0f0
  style DB_ANALYSIS fill:#2d1f0e,stroke:#d4a843,color:#d4a843
  style TG fill:#0e2a1f,stroke:#26a641,color:#26a641
```

### Jornada Completa — End to End

```mermaid
flowchart TD
  START(("🚀 Início")) --> UPLOAD_CV["1. Upload Currículo\n/curriculo"]
  UPLOAD_CV --> COLETA["2. Iniciar Coleta\n/discovery"]
  COLETA --> BROWSE["3. Explorar Vagas\n/vagas (filtros + bulk match)"]

  BROWSE --> ANALYZE["4. Analisar com IA\n/hub (analyze_vaga)"]
  ANALYZE --> MATCH["5. Calcular Match\n/hub (calcular_match)"]
  MATCH --> DECIDE{"Score bom?"}

  DECIDE -- "Sim ≥70" --> SAVE_PIPE["6. Salvar no Pipeline\netapa: salva"]
  DECIDE -- "Não" --> BROWSE

  SAVE_PIPE --> APPLY["7. Aplicar\netapa: aplicada"]
  APPLY --> COVER["8. Gerar Cover Letter\n/hub (gerar_cover_letter)"]

  COVER --> ADVANCE["9. Avançar Etapas\n/kanban (drag & drop)"]

  ADVANCE --> SCHEDULE["10. Agendar Entrevista\n(proxima_data)\n→ sync /calendar"]

  SCHEDULE --> INTERVIEW["11. Entrevista\n/calendar (consultar)"]

  INTERVIEW --> RESULT{"Resultado?"}
  RESULT -- "✅ Aprovado" --> HIRED["🎉 Contratado"]
  RESULT -- "❌ Reprovado" --> REJECTED["Rejeitado"]
  RESULT -- "↩️ Próxima fase" --> ADVANCE

  BROWSE -. "Monitorar tendências" .-> ANALYTICS["📊 Analytics\n/analytics"]
  COLETA -. "Match ≥85" .-> TG_ALERT["📱 Telegram Alert"]
  ADVANCE -. "Mudança de etapa" .-> TG_PIPE["📱 Telegram Update"]

  style START fill:#d4a843,stroke:#d4a843,color:#1a1a2e
  style HIRED fill:#0e2a1f,stroke:#26a641,color:#26a641
  style REJECTED fill:#2e0e0e,stroke:#f85149,color:#f85149
  style DECIDE fill:#2d1f0e,stroke:#d4a843,color:#d4a843
  style RESULT fill:#2d1f0e,stroke:#d4a843,color:#d4a843
```

<details>
<summary><strong>📊 Discovery — Fluxo Detalhado</strong></summary>

```mermaid
flowchart TD
  ENTRY["Usuário abre o app"] --> DISC["📊 Discovery"]

  DISC --> OV["Overview Cards\n• Total Radar\n• Match Score médio\n• Fake Junior count\n• Top Matches ≥85"]
  DISC --> COLETA["🔄 Iniciar Coleta"]
  DISC --> GRID["📋 Últimas 20 Vagas\n(grid 3 colunas)"]
  DISC --> PIPE_SUM["Pipeline Summary\n(contadores por etapa)"]
  DISC --> ALERTS["🚨 High-Score ≥85\nOportunidades"]

  COLETA --> COLETA_FLOW["Termo de busca →\nPOST /sistema/coletar-agora\n→ Polling progresso\n→ Cancel disponível"]

  GRID --> ACT_EXT["🔗 Abrir URL externa"]
  GRID --> ACT_AI["🤖 Analisar com IA\n→ salva em vaga_analysis"]
  GRID --> ACT_SAVE["💾 Salvar no Pipeline\n→ etapa: salva\n→ sync eventos"]

  PIPE_SUM -- "Link" --> KANBAN["/kanban"]
  ALERTS -- "Investigar" --> HUB_VAGA["/hub com contexto"]
  GRID -- "Explorar Todas" --> VAGAS["/vagas"]

  style DISC fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style COLETA fill:#2d1f0e,stroke:#d4a843,color:#d4a843
  style ACT_AI fill:#1a2e1a,stroke:#26a641,color:#26a641
  style ACT_SAVE fill:#1a2e1a,stroke:#26a641,color:#26a641
```

</details>

<details>
<summary><strong>🤖 Copilot Hub — Fluxo Detalhado</strong></summary>

```mermaid
flowchart TD
  HUB["🤖 Copilot Hub\n(2 painéis redimensionáveis)"] --> LEFT["⬅ Painel Esquerdo\nHubChat"]
  HUB --> RIGHT["➡ Painel Direito\nHubContext"]

  LEFT --> SESS["Sessões (tabs)\n• Ctrl+N: Nova\n• Delete: Excluir\n• Até 10 tabs"]
  LEFT --> MSG["Enviar Mensagem\n→ SSE Streaming"]

  MSG --> STREAM["Eventos SSE:\nreasoning → content →\ntool_start → tool_result → done"]

  STREAM --> TOOLS{"Tool Detectada?\n[TOOL:nome|params]"}
  TOOLS -- "Sim" --> EXEC["Executa Handler\nno Backend"]
  TOOLS -- "Não" --> RESP["Resposta texto\nno chat bubble"]

  EXEC --> T1["analyze_vaga\n→ vaga_analysis"]
  EXEC --> T2["calcular_match\n→ match_results"]
  EXEC --> T3["analisar_match\n(read-only CV vs Vaga)"]
  EXEC --> T4["pipeline_status\n(contadores)"]
  EXEC --> T5["buscar_vagas\n(até 15 resultados)"]
  EXEC --> T6["gerar_cover_letter\n(CV + Vaga)"]

  T1 & T2 & T3 & T4 & T5 & T6 --> CTX_UPDATE["Atualiza\nPainel Direito"]

  RIGHT --> VIEWS["Views Dinâmicas:\n• welcome (default)\n• vaga (detalhes)\n• analyze_vaga\n• calcular_match\n• pipeline_status\n• gerar_cover_letter\n• analisar_match\n• buscar_vagas\n• analise_completa\n• vagas_browser"]

  LEFT --> QUICK["Quick Actions:\n• Pipeline Status\n• Analisar Vaga\n• Calcular Match\n• Cover Letter"]

  LEFT --> BROWSER["📂 Mini Vaga Browser\nCtrl+Shift+B\n→ busca + scroll infinito\n→ click seleciona vaga"]

  style HUB fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style TOOLS fill:#2d1f0e,stroke:#d4a843,color:#d4a843
  style CTX_UPDATE fill:#1a2e1a,stroke:#26a641,color:#26a641
```

</details>

<details>
<summary><strong>📋 Pipeline / Kanban — Fluxo Detalhado</strong></summary>

```mermaid
flowchart LR
  subgraph STAGES["8 Etapas do Pipeline"]
    direction LR
    S1["🔘 Salvas"] --> S2["🟡 Aplicadas"]
    S2 --> S3["🟡 Em Análise"]
    S3 --> S4["🟡 Entrevista RH"]
    S4 --> S5["🟡 Entrevista Técnica"]
    S5 --> S6["🟡 Teste Técnico"]
    S6 --> S7["🟢 Contratado"]
    S3 --> S8["🔴 Rejeitado"]
  end

  DND["🖱 Drag & Drop\n→ Optimistic UI\n→ PATCH etapa\n→ Reverte se erro"] --> STAGES

  CARD["📇 Card Actions\n(JobDetailSheet)"] --> DETAIL["Slide-out:\n• Match score badge\n• Próxima Ação (input)\n• Data Próximo Contato\n• Notas (textarea)\n• Salvar → sync eventos\n• Portal da Vaga\n• Remover (confirm)"]

  DETAIL -- "proxima_data" --> CAL["📅 Sync → Calendar"]
  DND -- "Avançar etapa" --> TG["📱 Telegram\nnotificar_pipeline"]

  FILTERS["Filtros:\n• Empresa (searchable)\n• Stats: total + conversão"] --> STAGES

  style STAGES fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style DND fill:#2d1f0e,stroke:#d4a843,color:#d4a843
  style CAL fill:#0e1a2e,stroke:#58a6ff,color:#58a6ff
  style TG fill:#0e2a1f,stroke:#26a641,color:#26a641
```

</details>

<details>
<summary><strong>🔍 Vagas — Fluxo Detalhado</strong></summary>

```mermaid
flowchart TD
  VAGAS["📋 Vagas\n(paginada, 24/página)"] --> FILTERS

  subgraph FILTERS["Barra de Filtros"]
    F1["🔍 Busca texto"]
    F2["📡 Fonte (12 opções)"]
    F3["📍 Estado/UF"]
    F4["🏠 Modelo\nRemoto · Híbrido · Presencial"]
    F5["⭐ Score\nAny · ≥80 · ≥60 · ≥40"]
    F6["📌 Status\nFav · Aplicada · Analisada\nIgnorada · Arquivada"]
    F7["🔀 Ordenação\nData · Score · Salário\nEmpresa · Título"]
    F8["🏷 Categoria (pills)"]
  end

  VAGAS --> VIEW["Toggle View:\n🔲 Grid (3 cols) · 📄 Lista"]

  VIEW --> ACTIONS["Ações por Vaga"]
  ACTIONS --> A1["❤️ Favoritar\n(optimistic UI)"]
  ACTIONS --> A2["💾 Salvar → Pipeline\netapa: salva + sync"]
  ACTIONS --> A3["📤 Aplicar → Pipeline\netapa: aplicada + sync"]
  ACTIONS --> A4["🤖 Analisar\n→ Abre /hub\ncom contexto da vaga"]
  ACTIONS --> A5["🔗 Link Externo"]

  VAGAS --> BULK["Bulk Match Scores\nPOST /analise/match/bulk\n→ badges em cada card"]

  FILTERS -. "searchParams\n(URL = source of truth)" .-> VAGAS

  style VAGAS fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style FILTERS fill:#0d1117,stroke:#30363d,color:#f0f0f0
  style A4 fill:#1a2e1a,stroke:#26a641,color:#26a641
```

</details>

<details>
<summary><strong>📄 Currículo — Fluxo Detalhado</strong></summary>

```mermaid
flowchart TD
  CV["📄 Currículo"] --> CHECK{"Tem CV?"}

  CHECK -- "Não" --> UPLOAD["⬆️ UploadZone\nDrag & Drop\n• Parser Inteligente\n• Preservação Total\n• Match Score"]

  UPLOAD --> PARSE["Backend Parser\n→ nome, exp, formação,\nskills, projetos, idioma,\nconfidence score"]

  PARSE --> SAVE["Salva em\ncurriculo_versoes"]

  CHECK -- "Sim" --> LAYOUT["Layout 3 Colunas"]

  LAYOUT --> SIDEBAR["⬅ VersaoSidebar\n• Selecionar versão\n• Duplicar\n• Deletar\n• Renomear\n• Definir padrão\n• Upload nova"]

  LAYOUT --> VIEWER["📄 Document Viewer\n• Estruturado (parsed)\n• PDF Original (iframe)"]

  LAYOUT --> INSIGHTS["💡 Insights Panel\n• Seções detectadas\n• Skills identificadas\n• Experiências\n• Idioma principal\n• Parser warnings"]

  CV --> EXPORT["📥 Exportar\nPDF · DOCX"]

  CV --> VERSOES["/curriculo/versoes\nHistórico com diff"]

  SIDEBAR -- "CV Ativo usado por:" --> USED["🤖 calcular_match\n🤖 gerar_cover_letter\n🤖 contexto do chat\n🤖 otimizar_curriculo"]

  style CV fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style UPLOAD fill:#2d1f0e,stroke:#d4a843,color:#d4a843
  style USED fill:#1a2e1a,stroke:#26a641,color:#26a641
```

</details>

<details>
<summary><strong>📈 Analytics — Fluxo Detalhado</strong></summary>

```mermaid
flowchart TD
  ANA["📊 Analytics\n(10 chamadas paralelas)"] --> SECTION1
  ANA --> SECTION2
  ANA --> SECTION3

  subgraph SECTION1["Radar de Mercado"]
    C1["📊 Demandas Tecnológicas\n(horizontal bar, top 12)"]
    C2["💰 Projeção Salarial\n(grouped bar, min/max)"]
    C3["🛠 Skills em Alta\n(horizontal bar, top 12)"]
    C4["📡 Distribuição por Fonte\n(donut pie)"]
    C5["🎯 Senioridade Declarada\n(donut pie)"]
    C6["📈 Volume Histórico\n(area chart, 30d)"]
    C7["⭐ Score Médio por Fonte\n(bar chart)"]
  end

  subgraph SECTION2["Pipeline Analytics"]
    P1["🔄 Funil do Pipeline\n(8 etapas, progress bars)\nTotal · Conversão · Rejeição"]
  end

  subgraph SECTION3["Chat Analytics"]
    CH1["💬 4 Cards:\nSessões · Mensagens\nTools · Resultados"]
    CH2["📊 Tools Executadas\n(bar chart)"]
    CH3["📅 Atividade Diária 7d\n(bar chart)"]
  end

  ANA --> ALERTS["🚨 High-Score ≥85"]
  ANA --> TG_BTN["⚙️ Config Telegram\n(abre modal)"]

  style ANA fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style SECTION1 fill:#0d1117,stroke:#30363d,color:#f0f0f0
  style SECTION2 fill:#0d1117,stroke:#30363d,color:#f0f0f0
  style SECTION3 fill:#0d1117,stroke:#30363d,color:#f0f0f0
```

</details>

<details>
<summary><strong>📅 Calendário — Fluxo Detalhado</strong></summary>

```mermaid
flowchart TD
  CAL["📅 Calendário"] --> VIEWS["Views:\n📅 Semana (7 cols, 7h-22h)\n📋 Dia (cards lista)"]

  CAL --> TOOLBAR["Toolbar:\n🔄 Sincronizar Pipeline\n🧹 Limpar Órfãos\n📍 Hoje\n◀ ▶ Navegar\nDia / Semana toggle"]

  SYNC["🔄 Sync Pipeline\nPOST /eventos/sync-pipeline"] --> TYPES

  subgraph TYPES["Tipos de Evento"]
    E1["🟡 Entrevista RH"]
    E2["🟠 Entrevista Técnica"]
    E3["🔵 Teste Técnico"]
    E4["⚪ Follow-up"]
  end

  VIEWS --> CLICK["Click no Evento →\nModal Detalhes"]
  CLICK --> M1["📋 Info: empresa,\ntipo, data, título,\nlocal, descrição"]
  CLICK --> M2["🔗 Abrir Vaga (URL)"]
  CLICK --> M3["🗑 Excluir (confirm)"]

  TOOLBAR --> ORPHANS["Limpar Órfãos:\nRemove eventos cujo\npipeline_id não existe mais"]

  NOTE["⚠️ Eventos NÃO são\ncriados manualmente.\nSempre via sync do Pipeline\n(proxima_data → evento)"]

  style CAL fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style TYPES fill:#0d1117,stroke:#30363d,color:#f0f0f0
  style NOTE fill:#2d1f0e,stroke:#d4a843,color:#d4a843
```

</details>

<details>
<summary><strong>🗄️ Fluxo de Dados — MongoDB Collections</strong></summary>

```mermaid
flowchart LR
  subgraph COLLECTIONS["MongoDB Collections"]
    direction TB
    V["vagas"]
    VU["vagas_usuarios"]
    P["pipeline"]
    EV["eventos"]
    CS["chat_sessoes"]
    CM["chat_mensagens"]
    VA["vaga_analysis"]
    MR["match_results"]
    CR["curriculo_versoes"]
  end

  subgraph RELATIONS["Relações"]
    VU -- "vaga_id → _id" --> V
    P -- "vaga_id → _id" --> V
    EV -- "pipeline_id → _id" --> P
    CM -- "sessao_id → _id" --> CS
    VA -- "vaga_id → _id" --> V
    MR -- "vaga_id → _id" --> V
  end

  subgraph WRITES["Quem Escreve"]
    W_COLETA["Coleta\n(integradores)"] --> V
    W_USER["Ações do\nUsuário"] --> VU
    W_USER --> P
    W_SYNC["Pipeline\nSync"] --> EV
    W_CHAT["Chat\nIA"] --> CS
    W_CHAT --> CM
    W_TOOLS["AI Tools"] --> VA
    W_TOOLS --> MR
    W_UPLOAD["Upload /\nOtimizar"] --> CR
  end

  style COLLECTIONS fill:#1a1a2e,stroke:#d4a843,color:#f0f0f0
  style RELATIONS fill:#0d1117,stroke:#30363d,color:#f0f0f0
  style WRITES fill:#0e2a1f,stroke:#26a641,color:#26a641
```

</details>

<details>
<summary><strong>📱 Telegram — Gatilhos de Notificação</strong></summary>

```mermaid
flowchart LR
  T1["📡 Pós-Coleta\nmatch ≥ 85"] -- "notificar_match" --> BOT["🤖 Telegram Bot\n(httpx → Bot API)"]
  T2["🔄 Avançar Etapa\nPATCH /pipeline/etapa"] -- "notificar_pipeline" --> BOT
  T3["⏰ Celery Beat\n8h diário"] -- "notificar_resumo_diario" --> BOT
  BOT --> CHAT["📱 Chat do Usuário\n(HTML formatado)"]

  CONFIG["⚙️ Config\n(Analytics page)\n• enabled toggle\n• chat_id\n• 3 toggles\n• test button"] --> BOT

  style BOT fill:#0e2a1f,stroke:#26a641,color:#26a641
  style CONFIG fill:#2d1f0e,stroke:#d4a843,color:#d4a843
```

</details>

---

## 🖥️ Interface

### Páginas

| Rota | Função |
|------|--------|
| `/` — **Discovery** | Grade/lista de vagas com busca e filtros (fonte, score, UF, modelo, categoria) |
| `/hub` — **Copilot Hub** | 3 colunas redimensionáveis: sessões \| chat IA \| contexto com 7 views |
| `/kanban` — **Pipeline** | 8 colunas drag-and-drop: salva → contratado / rejeitado |
| `/vagas` — **Vagas** | Lista completa com filtros avançados |
| `/analise/vaga/[id]` — **Análise** | Score de match, análise IA, histórico de status |
| `/curriculo` — **Currículo** | Upload PDF/DOCX, gerenciamento de versões |
| `/curriculo/versoes` — **Versões** | Histórico com diff entre versões |
| `/analytics` — **Market Radar** | Stacks, salários, fontes, skills, timeline 30d |
| `/calendar` — **Calendário** | Eventos de entrevistas e prazos vinculados ao pipeline |

### Copilot Hub

O chat com IA oferece 6 ferramentas executáveis:

| Ferramenta | Função |
|------------|--------|
| `analyze_vaga` | Análise profunda de qualquer vaga |
| `calcular_match` | Score de compatibilidade com breakdown |
| `analisar_match` | Forças, lacunas e sugestões de desenvolvimento |
| `pipeline_status` | Status completo de todas as candidaturas |
| `buscar_vagas` | Busca em linguagem natural no banco de vagas |
| `gerar_cover_letter` | Carta de apresentação personalizada |

---

## 🗺️ Roadmap

- [x] **v1.0** — Coleta + análise offline + pipeline básico
- [x] **v2.0** — Chat IA Copilot + Hub + Currículo inteligente
- [x] **v2.1** — Analytics + Pipeline Kanban + Telegram
- [x] **v2.4** — Notificações por e-mail + Split layout + Novas fontes ATS
- [ ] **v3.0** — Refinamentos de UX + novas integrações

---

## ⚡ Quick Start

```bash
# 1. Infraestrutura (MongoDB + Redis)
docker compose up -d mongodb redis

# 2. Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8070

# 3. Frontend
cd frontend
npm install
npm run dev
```

Ou use `start.bat` na raiz para subir tudo automaticamente.

### IA Local (Opcional)

```bash
# Baixe o LM Studio em https://lmstudio.ai
# Carregue seu modelo em http://127.0.0.1:1234

# Sem IA local? A plataforma funciona,
# mas sem análise de vagas e match score
```

---

## 🛠️ Stack

<details open>
<summary><strong>Runtime & Language</strong></summary>

![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js_20-339933?style=for-the-badge&logo=node.js&logoColor=white)

</details>

<details open>
<summary><strong>Backend</strong></summary>

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB_7-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</details>

<details open>
<summary><strong>Frontend</strong></summary>

![Next.js](https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_v3-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)

</details>

<details open>
<summary><strong>Inteligência Artificial</strong></summary>

![LM Studio](https://img.shields.io/badge/LM_Studio-8B5CF6?style=for-the-badge&logo=local&logoColor=white)

</details>

---

## 📁 Estrutura

```
workplus/
├── backend/
│   ├── api/                  # 16 routers FastAPI
│   │   ├── ai.py             # Chat IA + SSE streaming + tools
│   │   ├── sistema.py        # Health check, coleta manual, status
│   │   ├── vagas.py          # Listagem, busca, detalhe
│   │   ├── pipeline.py       # Pipeline CRUD + drag-and-drop
│   │   ├── resume.py         # Upload, extração, versões
│   │   ├── analytics.py      # 9 endpoints de analytics
│   │   ├── notifications.py  # Telegram + Email config
│   │   └── ...               # analise, perfil, ai, eventos...
│   ├── integrations/         # 12 integrações com fontes de vagas
│   │   ├── portais.py         # Portais brasileiros (InfoJobs, Vagas, etc)
│   │   ├── plataformas.py     # Plataformas de recrutamento (Gupy, etc)
│   │   └── ats/               # Sites de carreira (Workday, Taqe, etc)
│   ├── core/                 # Config, DB, Logger, Auth
│   ├── models/               # Pydantic models (11 coleções)
│   ├── services/             # Serviços (scoring, dedup, IA, currículo...)
│   ├── tasks/                # Celery (tarefas em segundo plano)
│   └── ai/                   # Cliente IA (LM Studio)
├── frontend/
│   └── src/
│       ├── app/              # 7 rotas (discovery, hub, kanban...)
│       ├── components/       # 30+ componentes React
│       │   ├── chat/         # ChatPanel, ChatMessage
│       │   ├── kanban/       # KanbanBoard, JobDetailSheet
│       │   ├── vagas/        # VagaCard, FilterBar
│       │   └── ui/           # ResizablePanel, Skeleton, badges
│       └── lib/              # API client, chat context, utils
├── docker-compose.yml        # MongoDB + Redis
├── start.bat                 # Auto-install + startup
└── .env.example              # Template de configuração
```

---

## 🔧 Configuração

<details>
<summary><strong>🤖 IA</strong></summary>

```env
LM_STUDIO_URL=http://127.0.0.1:1234
LM_STUDIO_MODEL=nome-do-seu-modelo
```

</details>

<details>
<summary><strong>📱 Telegram</strong></summary>

```env
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

</details>

<details>
<summary><strong>📧 E-mail (IMAP/SMTP)</strong></summary>

```env
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_USER=seu_email@gmail.com
EMAIL_IMAP_PASS=sua_senha_ou_app_password
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

</details>

<details>
<summary><strong>⚙️ Gerais</strong></summary>

```env
MONGODB_URI=mongodb://localhost:27017/workplus
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=uma-chave-segura-aqui
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

</details>

---

---

## ⚖️ Aviso Legal

WorkHunter é um projeto **open source educacional**, criado como portfólio e ferramenta de uso pessoal.

- **Não afiliado** a nenhuma das plataformas, portais ou empresas listadas
- **Não automatiza candidaturas** — todo processo de aplicação é manual
- **Respeita `robots.txt`** e opera com limites responsáveis de requisições
- **IA 100% local** — nenhum dado pessoal sai da sua máquina
- Cada usuário é responsável por verificar os Termos de Serviço das fontes que utiliza
- Para uso comercial, consulte as autorizações necessárias junto a cada plataforma

<div align="center">

### **Descubra. Organize. Analise.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)]()
[![PRs: Welcome](https://img.shields.io/badge/PRs-Welcome-ff69b4?style=for-the-badge)]()

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:d4af37,100:1a1a2e&height=120&section=footer" width="100%">

</div>
