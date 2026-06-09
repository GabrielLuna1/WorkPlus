# WorkHunter — Especificação: Biblioteca de Vagas (v1.2.0)

## 1. Problema

O dashboard `/` carrega apenas 50 vagas das 502+ existentes, sem paginação
real, filtros avançados, ou gerenciamento individual. O usuário não consegue
explorar, organizar, ou acompanhar o status das vagas de forma eficiente.

## 2. Solução

Criar uma **página dedicada `/vagas`** com ferramentas completas de
gerenciamento, e reduzir o dashboard `/` ao seu propósito original: Discovery
(descoberta de novas vagas).

## 3. Separação de Domínios

### Coleção `vagas` (dados da vaga — global)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| ativa | bool | Vaga ainda disponível |
| encerrada_em | datetime | Quando foi encerrada |
| removida | bool | Removida do sistema |
| expirada | bool | Expirada por tempo |
| duplicada | bool | Marcada como duplicata |

### Coleção `vagas_usuarios` (interação do usuário)
| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| user_id | string | "default" | Identificador do usuário |
| vaga_id | ObjectId | — | Referência à vaga |
| favoritada | bool | false | Favoritada pelo usuário |
| aplicada | bool | false | Usuário se candidatou |
| analisada | bool | false | Analisada por IA |
| ignorada | bool | false | Ignorada/descartada |
| arquivada | bool | false | Arquivada |
| notas | string | "" | Notas pessoais |

**Index:** compound unique `{user_id: 1, vaga_id: 1}`

## 4. Endpoints

### `GET /api/v1/vagas` — Listar vagas (refatorado)

**Query Params:**

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| page | int | 1 | Número da página |
| limit | int | 24 | Itens por página (max 100) |
| fonte | str | — | Filtrar por fonte |
| score_min | int | — | Score mínimo |
| score_max | int | — | Score máximo |
| busca | str | — | Busca textual |
| status | str | — | Filtrar por ação do usuário |
| order_by | str | coletada_em | Campo de ordenação |
| order_dir | str | desc | asc ou desc |
| ativa | bool | true | Apenas vagas ativas |

**Response:**

```json
{
  "data": [
    {
      "id": "...",
      "titulo": "Desenvolvedor React",
      "empresa": "Tech Corp",
      "score": 85,
      "fonte": "gupy",
      "localizacao": "Remoto",
      "salario_min": 6000,
      "salario_max": 10000,
      "tipo_contrato": "CLT",
      "data_publicacao": "2026-05-20",
      "coletada_em": "2026-05-25T19:16:00",
      "ativa": true,
      "url": "https://...",
      "analise": { "fake_junior": false, "nivel_estimado": "pleno" },
      "analise_ia": null,
      "usuario_status": {
        "favoritada": true,
        "analisada": false,
        "aplicada": false,
        "ignorada": false,
        "arquivada": false,
        "notas": ""
      }
    }
  ],
  "total": 502,
  "page": 1,
  "limit": 24,
  "total_pages": 21
}
```

### `POST /api/v1/vagas-usuarios/favoritar/{vaga_id}`
Toggle favorito. Retorna `{ favoritada: bool }`.

### `GET /api/v1/vagas-usuarios/status/{vaga_id}`
Retorna o documento `vagas_usuarios` para a vaga + usuário.

### `POST /api/v1/vagas-usuarios/bulk-status`
Body: `{ vaga_ids: string[] }`
Retorna `{ [vaga_id]: VagaUsuarioStatus }` — lookup em lote.

### `PATCH /api/v1/vagas-usuarios/{vaga_id}`
Body parcial: `{ notas?, ignorada?, arquivada?, ... }`

## 5. Frontend — Página `/vagas`

### Rota
`/vagas` → `src/app/vagas/page.tsx`

### Layout
```
┌──────────────────────────────────────────────────────────┐
│ Vagas (metallic-gradient h1)                             │
│ "502 oportunidades — 12 novas hoje"                      │
├──────────────────────────────────────────────────────────┤
│ [🔍 Buscar vagas...] [Fonte ▼] [Score ▼] [Status ▼]    │
│ Ordenar: [Data ↓]                           [Grid][Lista]│
│ badges: [React ×] [Gupy ×] [≥ 80 ×] [Favoritadas ×]    │
├──────────────────────────────────────────────────────────┤
│ Grid/Lista de vagas                                      │
│ (VagaCard ou VagaListItem)                               │
├──────────────────────────────────────────────────────────┤
│ « 1 2 3 ... 21 »   Ir para: [___]                       │
└──────────────────────────────────────────────────────────┘
```

### VagaCard (Grid)
```
┌─────────────────────────┐
│ [♥]  ScoreRing(85)      │
│ Tech Corp               │
│ Desenvolvedor React     │
│                         │
│ 📍 Remoto               │
│ 💰 R$ 6k - R$ 10k       │
│ 🏷️ Pleno · CLT          │
│ 📅 20/05/2026            │
│                         │
│ [🔗 Visitar] [✨ IA]    │
└─────────────────────────┘
```

### VagaListItem (Lista)
```
[♥] Score 85  Tech Corp  |  Desenvolvedor React  |  Remoto  |  R$ 6k-10k  |  Pleno  |  20/05  |  [🔗]
```

### Componentes

| Componente | Descrição |
|------------|-----------|
| `VagaCard` | Card com indicadores completos e ação de favoritar |
| `VagaListItem` | Versão linha para layout lista |
| `FilterBar` | Inputs de filtro + badges ativos |
| `VagaPagination` | Navegação numérica + input de página |
| `ViewToggle` | Alternância Grid/Lista com ícones |
| `EmptyState` | Estado vazio por filtro, busca sem resultados, ou banco vazio |
| `LoadingSkeleton` | Esqueleto de carregamento em grid (6 cards) |

### Gestão de Estado

- **Estado dos filtros:** URLSearchParams (fonte única da verdade)
- **Dados:** useState normal, recarregar via useEffect quando searchParams mudar
- **Debounce busca:** 300ms antes de atualizar a URL
- **Favoritar:** optimistic update — inverte UI imediatamente, reverte em erro
- **Layout view:** localStorage persiste preferência grid/lista

### URL State

```
/vagas?q=react&fonte=gupy&score_min=80&status=favoritada&sort=score&dir=desc&page=2&view=grid
```

## 6. Dashboard Refatorado `/`

- Apenas últimas 20 vagas
- Métricas: total de vagas, score médio, fake juniors detectados, novas hoje
- Cards em grid simplificado (sem filtros complexos)
- Botão "Explorar Todas as Vagas →" para `/vagas`
- Botão "Executar Scrapers" mantido
- Alertas de vagas high-score

## 7. Sidebar

- Novo item: `Vagas` (Database icon) entre Kanban e Currículo
- Ativo quando rota `/vagas`

## 8. Fluxo de Dados

```
[Frontend]                              [Backend]
    │                                        │
    ├─ GET /vagas?page=1&busca=react ──────► │
    │                                        ├─ db.vagas.find({$text: /react/i})
    │                                        ├─ db.vagas_usuarios.findOne() p/ cada
    │                                        └─ { data: [...], total, page, total_pages }
    │◄───────────────────────────────────────┤
    │                                        │
    ├─ POST /vagas-usuarios/favoritar/id ──► │
    │                                        ├─ db.vagas_usuarios.updateOne($toggle)
    │                                        └─ { favoritada: true }
    │◄───────────────────────────────────────┤
```

## 9. Não-Escopo (v1.2.0)

- Autenticação multiusuário
- Notificações push para vagas favoritas
- Exportação de dados
- Comparação de vagas
- Tags personalizadas pelo usuário
