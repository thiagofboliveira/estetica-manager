# docs/ — Índice da documentação

Organização por **estado de execução**, não por assunto. A pergunta que esta pasta responde é: *o que já foi feito, o que está em andamento, e o que falta.*

**Última auditoria de estado:** 2026-09-03 (verificada contra o código, não contra os docs)

---

## Estrutura

| Pasta | Significado | Regra |
|---|---|---|
| [`finished/`](finished/) | Entregue e verificado | Só entra aqui com evidência: teste passando, ou verificação no código |
| [`in_progress/`](in_progress/) | Começado, com itens abertos | Sai daqui quando o último `[ ]` fechar |
| [`pending/`](pending/) | Não começado | Backlog de futuro |

Documentos **atemporais** (não têm estado de execução) ficam na raiz de `docs/` ou do repo:
`ENGENHARIA.md` (invariantes), `LGPD_CONTRATO_OPERADOR.md`, `ENTREVISTA.md`, `requisitos.md`, o MVP spec.

---

## finished/

| Arquivo | Conteúdo | Estado |
|---|---|---|
| [`BACKLOG_SPRINT3_backend.md`](finished/BACKLOG_SPRINT3_backend.md) | Split por procedimento (E6), Exportação CSV, Projeção de recebíveis, Antecipação (E7) | 16/16 ✅ |
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
| [`BACKLOG_SPRINT2_backend.md`](in_progress/BACKLOG_SPRINT2_backend.md) | ROI, Anti-No-Show, Importação, Templates | **20/23** — features prontas, 3 fixes de code review abertos |

**Os 3 itens abertos** (verificados no código em 2026-09-03, genuinamente pendentes):

1. **`query()` cru no repositório de retenção** — `return_opportunity.py:82` usa `self._session.query(ReturnOpportunity, Sale)` em vez de `select()` com `_scoped()`. Viola o padrão SQLAlchemy 2.0 que o `test_architecture.py` protege no resto do código.
2. **`GET /templates` com dependência desnecessária** — `procedures.py:27` injeta `ProcedureSvc` para chamar uma função pura de catálogo. Rota de leitura de constante não precisa de sessão de banco.
3. **Rate limiting na importação em lote** — ausente. Sem isso, um loop no cliente pode disparar importações ilimitadas.

---

## pending/

| Arquivo | Conteúdo | Escopo |
|---|---|---|
| [`BACKLOG_VERSAO_COMPLETA.md`](pending/BACKLOG_VERSAO_COMPLETA.md) | Backlog da versão completa — 74 tasks em 8 épicos (V1 a V8) | Do estado atual até SaaS vendável |

**As 4 lacunas que ele endereça:**

| # | Lacuna | Evidência |
|---|---|---|
| L-1 | Não sabe cobrar | Zero `subscription`/`billing` no backend; `clinics.plan` é string livre |
| L-2 | Não tem cadastro público | `/system/setup` só com zero usuários; `POST /users` exige admin |
| L-3 | Não tem produção | Nenhum Dockerfile de app, CI ou deploy |
| L-4 | Não se mede | Nenhuma tabela de eventos, funil ou cohort |

---

## Onde fica o backlog vivo

O índice de coordenação continua em [`../BACKLOG.md`](../BACKLOG.md) — features já entregues (Super Admin, Multi-Tenant SaaS, Sprints 2 e 3) com links para esta pasta.

## Manutenção

- Ao fechar o último `[ ]` de um doc em `in_progress/`, mova para `finished/` com `git mv`.
- Ao começar um doc de `pending/`, mova para `in_progress/`.
- **Atualize o estado no momento da mudança, não em lote.** Este README existe porque a documentação anterior tinha divergido do código.
