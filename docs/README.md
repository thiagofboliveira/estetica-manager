# docs/ — Índice da documentação

Organização por **estado de execução**, não por assunto. A pergunta que esta pasta responde é: *o que já foi feito, o que está em andamento, e o que falta.*

**Última auditoria de estado:** 2026-09-05 (verificada contra o código e contra os gates, não contra os docs)

---

## Estrutura

| Pasta | Significado | Regra |
|---|---|---|
| [`finished/`](finished/) | Entregue e verificado | Só entra aqui com evidência: teste passando, ou verificação no código |
| [`in_progress/`](in_progress/) | Começado, com itens abertos | Sai daqui quando o último `[ ]` fechar |
| [`pending/`](pending/) | Não começado | Backlog de futuro |

Documentos **atemporais** (não têm estado de execução) ficam na raiz de `docs/` ou do repo:
`ENGENHARIA.md` (invariantes), [`FREE_TIER_SERVICES.md`](FREE_TIER_SERVICES.md) (infraestrutura e cotas gratuitas), `LGPD_CONTRATO_OPERADOR.md`, `ENTREVISTA.md`, `requisitos.md`, o MVP spec.

---

## finished/

| Arquivo | Conteúdo | Estado |
|---|---|---|
| [`BACKLOG_SPRINT3_backend.md`](finished/BACKLOG_SPRINT3_backend.md) | Split por procedimento (E6), Exportação CSV, Projeção de recebíveis, Antecipação (E7) | 16/16 ✅ |
| [`BACKLOG_SPRINT2_backend.md`](finished/BACKLOG_SPRINT2_backend.md) | ROI, Anti-No-Show, Importação em lote, Templates + 3 ações corretivas (AC-01, AC-02, AC-07) | 23/23 ✅ |
| [`BACKLOG_SPRINT2_frontend.md`](finished/BACKLOG_SPRINT2_frontend.md) | ROI, Anti-No-Show, Importação em lote, Templates, PWA + 4 ações corretivas | 27/27 ✅ |
| [`BACKLOG_V2_frontend.md`](finished/BACKLOG_V2_frontend.md) | CSS Modules, Error Boundaries, Templates de mensagem, Telemetria | 13/13 ✅ |
| [`QA_CONSOLIDADO.md`](finished/QA_CONSOLIDADO.md) | Relatório de QA das Sprints 1-3 | Histórico |
| [`QA_backend.md`](finished/QA_backend.md) | Auditoria de bugs — backend | Histórico |
| [`QA_frontend.md`](finished/QA_frontend.md) | Auditoria de bugs — frontend | Histórico |

> ⚠️ **Os três relatórios de QA estão defasados.** Auditoria de 2026-09-03 verificou os 5 bugs que eles listam como abertos — **todos já corrigidos no código**:
>
> | Bug | Estado real |
> |---|---|
> | `BUG-BACK-S2-02` telefone em bookings | ✅ `session_service.py` lê `b.patient.phone` |
> | `BUG-FRONT-S2-05` separador `;` no import | ✅ `line.split(/[\t,;]/)` |
> | `BUG-FRONT-S3-01` PWA `crypto` Node 18 | ✅ polyfill em `vite.config.ts` |
> | `BUG-FRONT-S2-03` prefixo `/api/v1` duplo | ✅ paths relativos via `client.ts` |
> | `BUG-FRONT-S2-02` fuso UTC no `NoShowAlert` | ✅ consome a API sem refiltrar |
>
> Mantidos como histórico. Consolidá-los é a task `V1-01` do backlog pendente.

---

## in_progress/

| Arquivo | Conteúdo | Estado |
|---|---|---|
| [`BACKLOG_AUDITORIA_2026-09-05.md`](in_progress/BACKLOG_AUDITORIA_2026-09-05.md) | 🔴 **Comece aqui.** Auditoria pós-Fase 2: agenda pública entregue fora do plano e sem consentimento, porta de decisão da Fase 3 travada por dependência circular, medição que mede setup e não valor | 1/16 — `A-01` (gate `ruff`) fechada em 2026-09-05 |

> Antes disso, `BACKLOG_SPRINT2_backend.md` moveu para `finished/` em 2026-09-04 após as 3 ações corretivas (AC-01, AC-02, AC-07) serem corrigidas e testadas.

---

## pending/

| Arquivo | Conteúdo | Escopo |
|---|---|---|
| [`BACKLOG_GO_LIVE.md`](pending/BACKLOG_GO_LIVE.md) | Go-live: 5 bloqueadores do primeiro login + 3 de segurança + pesquisa de concorrência e preço. Fases 0-2 ✅ concluídas | Do MVP pronto ao primeiro uso real |
| [`BACKLOG_VERSAO_COMPLETA.md`](pending/BACKLOG_VERSAO_COMPLETA.md) | Backlog da versão completa — 74 tasks em 8 épicos (V1 a V8) | Do go-live até SaaS em escala |
| [`BACKLOG_FILTROS_E_LAYOUT.md`](pending/BACKLOG_FILTROS_E_LAYOUT.md) | Filtros, sidebar, carrosséis, reengajamento (E1-E6) | ✅ Entregue — só `F6-05` aberto (decisão de escopo) |

**As 4 lacunas do `BACKLOG_VERSAO_COMPLETA.md`** — reauditadas em 2026-09-04:

| # | Lacuna | Estado real (auditado no código) |
|---|---|---|
| L-1 | Não sabe cobrar | ✅ **Confirmada.** Zero `subscription`/`billing`; `clinics.plan` é string livre e nunca verificado em request |
| L-2 | Não tem cadastro público | ✅ **Confirmada.** Os 3 caminhos exigem privilégio preexistente |
| L-3 | Não tem produção | ⚠️ **Parcialmente desatualizada.** `backend/Dockerfile` e `railway.json` **existem**. Falta CI e infra do frontend |
| L-4 | Não se mede | ✅ **Confirmada, e pior:** o produto não mede o no-show evitado, que é seu maior alvo econômico |

> 🔴 **A auditoria de 2026-09-05 encontrou a maior entrega da semana sem documento algum:**
> a **agenda pública** (`/agendar/:slug`, migrations `0017`–`0021`, `api/v1/public_agenda.py`)
> é a `V8-04`, listada como fora de escopo no MVP spec e no último épico do
> `BACKLOG_VERSAO_COMPLETA.md`. Ela quebrou o gate `ruff` (8 erros, ✅ corrigidos) e coleta nome e telefone
> da paciente sem consentimento registrado. Tudo em
> [`BACKLOG_AUDITORIA_2026-09-05.md`](in_progress/BACKLOG_AUDITORIA_2026-09-05.md).

> 🔴 **A auditoria de 2026-09-04 encontrou 5 bloqueadores que nenhum documento registrava** —
> entre eles, a senha do setup ser coletada pela tela e descartada pelo backend
> (`system_service.py:29`). Estão todos em [`BACKLOG_GO_LIVE.md`](pending/BACKLOG_GO_LIVE.md).

---

## Onde fica o backlog vivo

O índice de coordenação de features entregues está em [`finished/BACKLOG.md`](finished/BACKLOG.md) — Super Admin, Multi-Tenant SaaS, Sprints 2 e 3, com links para esta pasta.

## Manutenção

- Ao fechar o último `[ ]` de um doc em `in_progress/`, mova para `finished/` com `git mv`.
- Ao começar um doc de `pending/`, mova para `in_progress/`.
- **Atualize o estado no momento da mudança, não em lote.** Este README existe porque a documentação anterior tinha divergido do código.
