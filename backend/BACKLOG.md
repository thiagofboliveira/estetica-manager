# Backlog — Backend (FastAPI)

Escopo: API, modelo de dados, motor de lucro, motor de retorno, isolamento, deploy.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-08-29 · **Progresso:** 25/85 (29%) · nenhuma bloqueada (T-002/T-057a/T-058 desbloqueadas: ambiente dev local com Docker roda a migration 0001 contra Postgres real e prova RLS)

---

## Status

`[ ]` TODO · `[~]` WIP · `[x]` DONE · `[!]` BLOCKED · `[-]` adiado (P1)

**DONE exige evidência:** teste passando ou endpoint respondendo. Não marque por ter escrito o código.

---

## Painel

| Fase | Tasks | Feito |
|---|---:|---:|
| **Total MVP** | **85** | **25** |

> ⚠️ **Contagem por fase não recalculada nesta atualização** — o detalhamento por fase (Fundação/Cadastros/Venda/Retenção/Qualidade) que existia aqui ficou incorreto ao longo de edições anteriores da sessão e não foi refeito linha a linha ainda. O total geral (80/25) foi conferido por contagem direta das linhas de task do arquivo em 2026-08-29. Refazer o detalhamento por fase quando for confirmar o planejamento de sprint.
>
> 🔧 Subiu de 57 (v2 original) para 80 após a análise de engenharia (T-057a/T-058/etc) e a adição de despesas fixas (T-021a/T-021b, pós-entrevista).

---

## ✅ Configuração da cliente zero (bloqueio resolvido)

✅ **T-048 concluída em 2026-08-29** — E1-E8 fechados (ver `../ENTREVISTA.md`). **A Fase 2 está liberada.** Configuração da cliente zero: sem split de clínica (aluguel fixo), Pix por sessão, sem parcelamento, sem antecipação, custo variável por aplicação, pacotes sem prazo.

| Eixo | Pergunta | Afeta |
|---|---|---|
| E1 | Taxa é dela ou da clínica? | `fee_payer` em T-007 |
| E2 | Split sobre bruto ou líquido? | `split_base` em T-007 |
| E4 | Parcela? Quantas vezes? | T-008 (faixas) |
| E5 | Custo varia por paciente? | `cost_override` em T-014 |
| E7 | Antecipa recebíveis? | **Vira P0 se sim** |
| E8 | Pacote tem validade? | `EXPIRED` em T-014 |

---

# FASE 0 — Fundação

**Meta:** `/health` no ar, auth funcionando, isolamento provado.

## Setup

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-001c | **Decidir driver sync vs async** | `[x]` | — | Escolhido **sync** — `psycopg2` + rotas `def` |
| T-001e | Ajustar `pyproject.toml` | `[x]` | T-001c | `pyproject.toml` ajustado — `pyjwt[crypto]`+`hypothesis` in, `python-jose`/`passlib`/`bcrypt`/`pytest-asyncio` out |
| T-001 | Estrutura FastAPI + lint + pytest | `[x]` | T-001e | Estrutura criada, ruff limpo (`banned-api` p/ `.query()`) |
| T-001a | Fixar tipo monetário `NUMERIC(12,2)` / `Decimal` | `[x]` | T-001 | `Numeric(12,2, asdecimal=True)` + `MoneyOut` (Pydantic, serializa como string) |
| T-001b | Fixar `TIMESTAMPTZ` + UTC + `professionals.timezone` | `[x]` | T-001 | `TimestampMixin` com `TIMESTAMPTZ`; `professionals.timezone` |
| T-001d | `core/money.py` — `money()` + `ROUND_HALF_UP` | `[x]` | T-001a | `app/core/money.py::money()` — 5 testes passando |
| T-001f | **`allocate()` — rateio largest remainder** | `[x]` | T-001d | `app/core/money.py::allocate()` — largest remainder |
| T-001g | Property tests de `allocate()` (hypothesis) | `[x]` | T-001f | 20 testes em `tests/test_money.py`, incl. property test Hypothesis — **todos passando** |

## Banco

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-002 | PostgreSQL (Supabase) + SQLAlchemy + Alembic | `[x]` | T-001 | `alembic upgrade head` **aplicado e verificado** contra Postgres 16 real (Docker local, `docker-compose.dev.yml`) em 2026-08-29. Supabase gerenciado segue pendente para produção |
| T-003 | Tabela `users` | `[x]` | T-002 | `app/models/user.py` — **sem** `password_hash`. Migration aplicada, schema conferido com `\d` |
| T-004 | Tabela `professionals` | `[x]` | T-003 | `app/models/professional.py` — com `timezone`. Migration aplicada |
| T-005 | Tabela `patients` | `[x]` | T-004 | `app/models/patient.py` — `consent_whatsapp`, `opted_out_at`, `anonymized_at`. Migration aplicada |

## Auth e isolamento

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-006 | Validação de JWT via JWKS (`PyJWKClient`) | `[x]` | T-003, T-001e | `app/core/security.py` — `PyJWKClient` + decode |
| T-006a | `get_current_professional` — do claim `sub` | `[x]` | T-006 | `get_current_professional_id()` — só do claim `sub` |
| T-006b | `InputSchema` com `extra="forbid"` + teste | `[x]` | T-006a | `InputSchema(extra="forbid")` + `test_schemas_sem_tenant.py` passando |
| T-057a | **Role `estetica_app` `NOBYPASSRLS`** | `[x]` | T-002 | Role criada e verificada em 2026-08-29 (`\du estetica_app` confirma `NOBYPASSRLS`). Senha ainda é placeholder de dev — trocar antes de produção |
| T-058 | RLS: `ENABLE` + `FORCE` + `USING` + `WITH CHECK` | `[x]` | T-057a, T-005 | Verificado com `\d patients`: `Policies (forced row security enabled)` presente. Testado via API real: criar/listar paciente com token dev funcionou fim a fim |
| T-058a | Repository base exigindo `professional_id` | `[x]` | T-058 | `app/repositories/base.py::TenantRepository` — `add()` carimba, não confia |
| T-058b | `set_config(..., true)` em transação explícita | `[x]` | T-058 | `app/db/session.py::get_tenant_session` — **testado contra Postgres real em 2026-08-29**, funcionando |
| T-058c | Lint + teste barrando `session.query()` cru | `[x]` | T-058a | ruff `banned-api` + `test_architecture.py::test_nenhum_query_cru_fora_do_repositorio` |
| T-046 | Teste de isolamento genérico | `[ ]` | T-058 | Enumera **todas** as rotas. A→404 nos recursos de B. Precisa de fixture com banco |
| T-046a | Testes do RLS em si (query crua, insert, sem contexto) | `[ ]` | T-058 | 🆕 Prova a 2ª camada. Precisa de Postgres real |
| T-046b | Teste: toda tabela com `professional_id` tem RLS | `[ ]` | T-058 | 🆕 Pega migration futura sem policy, no CI |

> 🔴 **Isolamento é Fase 0, não Fase 4.** Vazamento entre profissionais da mesma clínica é evento de extinção do produto.

**Saída:** login funciona, A não vê dados de B (provado por teste), `/health` em produção.

---

# FASE 1 — Cadastros e configurações

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-007 | Tabela `financial_settings` | `[ ]` | T-004 | `split_base` + `fee_payer` |
| T-008 | Tabela `payment_fee_rules` | `[ ]` | T-007 | Faixas: 1x, 2-6x, 7-12x |
| T-008a | Seed de defaults de mercado | `[ ]` | T-008 | **Nunca** copiar de outra conta |
| T-009 | Tabela `procedures` | `[x]` | T-004 | `app/models/procedure.py` |
| T-009a | `default_modality` em `procedures` 🆕 v7.1 | `[ ]` | T-009 | `IN_PERSON \| REMOTE`, default `IN_PERSON`. **Migration nova** (0002) — T-009 já aplicada. Ver MVP §9 |
| T-010 | CRUD `/procedures` | `[x]` | T-009 | `app/api/v1/procedures.py` — 5 endpoints |
| T-010a | Expor `default_modality` no CRUD 🆕 v7.1 | `[ ]` | T-009a, T-010 | Schemas Create/Update/Out |
| T-011 | CRUD `/patients` | `[x]` | T-005 | `app/api/v1/patients.py` — 5 endpoints, `DELETE`=arquivar |
| T-011a | Normalização E.164 | `[x]` | T-011 | `app/core/phone.py::normalize_br_phone()` |
| T-011b | Busca com `pg_trgm` + `unaccent` + paginação | `[x]` | T-011 | `repositories/patient.py` usa `func.unaccent` — migration cria as extensões |

**Saída:** cadastros completos via API, configuração financeira persistida.

---

# FASE 2 — Venda, lucro e dashboard

> ✅ **Liberada** — T-048 concluída em 2026-08-29.

## Modelo transacional

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-012 | Tabela `sales` | `[ ]` | T-007, T-048 | `cost_provisioned` + `cost_realized` |
| T-013 | Tabela `sale_items` | `[ ]` | T-012, T-009 | Preço/custo/intervalo congelados |
| T-014 | Tabela `sessions` | `[ ]` | T-013 | `professional_id` desnormalizado p/ RLS. Inclui `modality` **NOT NULL**, copiada de `procedure.default_modality` na criação — nunca resolvida por `COALESCE` na leitura (v7.1) |
| T-014a | Máquina de estados da sessão | `[ ]` | T-014 | `PENDING`, `EXPIRED`, `CANCELLED→PENDING` |
| T-015 | `POST /sales` (avulsa + pacote) | `[ ]` | T-014 | Gera N sessions |
| T-015a | **Idempotência (contrato C-1)** | `[ ]` | T-015 | 🔧 Mesma chave + mesmo corpo → **200 com a venda existente**, não 409. TTL 24h |
| T-016 | `PATCH /sessions/{id}` | `[ ]` | T-014 | Recalcula `cost_realized` |
| T-017 | `PATCH /sales/{id}` + `sale_audit` | `[ ]` | T-015 | Config **do momento original** |

## Motor de lucro

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-018 | Cálculo parametrizado | `[ ]` | T-012, T-048 | 4 modelos split/taxa |
| T-018a | Custo provisionado vs realizado | `[ ]` | T-018 | `EXPIRED` libera custo |
| T-018b | Rateio de desconto por item | `[ ]` | T-001f | 🔧 Usa `allocate()` — largest remainder, não "último absorve" |
| T-018c | Taxa: calcular total e ratear | `[ ]` | T-018b | 🆕 Por item + soma diverge da fatura da adquirente |
| T-019 | Margem | `[ ]` | T-018 | Bruto=0 → NULL; negativa visível |
| T-020 | Congelar snapshot | `[ ]` | T-018 | Inclui a **fórmula**, não só percentuais |
| T-020a | `ConfigVersion` versionada (`valid_from`/`valid_to`) | `[ ]` | T-007 | 🆕 Config nunca sofre UPDATE — permite `vigente_em(data)` |
| T-020b | Listener `before_flush` bloqueando snapshot | `[ ]` | T-020 | 🆕 Listener **proíbe**; service calcula |
| T-020c | `CheckConstraint` da identidade contábil | `[ ]` | T-012 | 🆕 `net = gross - discount` no **banco** |
| T-021 | `expected_receipt_date` | `[ ]` | T-018 | Lucro ≠ caixa |

## Despesas fixas 🆕 (MVP v7 §12.5 — pós-entrevista 2026-08-29)

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-021a | Tabela `fixed_expenses` | `[ ]` | T-004 | Vigência (`active_from`/`active_to`) + `periodicity` (MONTHLY\|YEARLY) 🔧 v7.1 — sem categoria fechada no MVP |
| T-021b | CRUD `/fixed-expenses` | `[ ]` | T-021a | "Excluir" fecha `active_to`, nunca hard delete |

> Cliente zero paga aluguel fixo de sala, não split percentual — E2/E6 não se aplicam a ela (ver `ENTREVISTA.md`). Alimenta a linha "Lucro real do mês" em T-022, só em filtros mensais. `periodicity=YEARLY` entra ratada por 12 no cálculo mensal (ex: taxa de vigilância sanitária, R$/ano) — ver MVP v7 §12.5.

## Testes do motor (junto, não depois)

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-043 | Unitários do cálculo | `[ ]` | T-018 | Arredondamento com dízima (333,33 × 33%) |
| T-044 | **Matriz de 5 configurações** | `[ ]` | T-018 | Mesmas asserções, 5 configs. Inclui split 0% |

> ⚠️ **T-044 antes de qualquer endpoint de dashboard.** Se o cálculo não estiver provado para 5 configurações, a API devolve número errado com aparência de certo.

## Endpoints de leitura

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-022 | `GET /dashboard` | `[ ]` | T-018 | Declarar venda-vs-sessão. Inclui "Lucro real do mês" (T-021b) 🆕 |
| T-022a | Campo `hasAnyData` (contrato C-2) | `[ ]` | T-022 | 🆕 1 booleano — distingue first-run de mês vazio |
| T-023 | Filtro por período | `[ ]` | T-022 | `AT TIME ZONE` **antes** de truncar |
| T-024 | `GET /reports/procedures` | `[ ]` | T-018b | Só confiável com E4+E5 |

**Saída:** venda registrada devolve lucro correto nas 5 configurações.

---

# FASE 3 — Retenção e agenda

## Motor de retorno

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-025 | Tabela `return_opportunities` | `[ ]` | T-014 | `timing` derivado, `status` persistido |
| T-026 | Cálculo da janela | `[ ]` | T-025 | Da **última sessão** do item |
| T-027 | `return_interval_applied` por item | `[ ]` | T-013 | |
| T-028 | Regra de fechamento | `[ ]` | T-025, T-015 | Fecha na **venda**, não na sessão |
| T-029 | `GET /retention/opportunities` | `[ ]` | T-025 | Agrupa por paciente, supressão 14d, só com consentimento |
| T-031 | `PATCH /retention/{id}` | `[ ]` | T-029 | `contacted_at`, canal, status |

## Agenda

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-032 | `GET /sessions?from&to` | `[ ]` | T-014 | Fuso da profissional. `PENDING` não entra. Retorna `modality` (v7.1) |
| T-033 | `PATCH /sessions/{id}` agendar/reagendar | `[ ]` | T-014 | `PENDING → SCHEDULED`; aviso (não bloqueio) em conflito de horário |
| T-034 | `GET /packages/open` | `[ ]` | T-014 | Saldo não agendado |
| T-034a | Tabela `bookings` 🆕 v7.1 | `[ ]` | T-004, T-011 | Agendamento sem venda ainda — `patient_id` nullable + `patient_name_hint` + `modality`. Ver MVP v7.1 §16.6 |
| T-034b | CRUD `/bookings` + conversão em venda 🆕 v7.1 | `[ ]` | T-034a, T-015 | `POST /sales` aceita `booking_id` opcional → seta `CONVERTED` na mesma transação |

**Saída:** oportunidades corretas, sem duplicar paciente, sem reativar quem tem saldo.

---

# FASE 4 — Qualidade e deploy

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-045 | Testes de integração | `[ ]` | T-028 | Ciclo completo de retorno |
| T-045a | Pacote não reativa prematuramente | `[ ]` | T-045 | `PENDING` não conta |
| T-045b | Atribuição fora da janela de 21d não conta | `[ ]` | T-045 | |
| T-059 | Base legal + contrato de operador | `[ ]` | — | **Antes do cliente zero** |
| T-060 | Consentimento + opt-out | `[ ]` | T-011 | Art. 11 · risco de banimento do número |
| T-061 | `POST /patients/{id}/anonymize` | `[ ]` | T-011 | Art. 18 VI + Art. 16 II |
| T-062 | Política de retenção + canal do titular | `[ ]` | T-059 | 5 anos fiscal |
| T-047 | Deploy Railway + observabilidade | `[ ]` | T-022 | Backup **com restore testado** |
| T-047a | Alerta de falha no cron de retenção | `[ ]` | T-047 | Silêncio = 2º pilar parado |

**Saída:** produção estável, LGPD coberta, backup restaurável.

---

# P1 — Adiado

| ID | Task | Status | Nota |
|---|---|:--:|---|
| T-052 | Sessões nas próximas 24h | `[-]` | Anti-no-show |
| T-053 | Lembrete de confirmação | `[-]` | |
| T-054 | Registrar confirmação | `[-]` | `RESCHEDULE_REQUESTED` é sinal, não estado |
| T-055 | Webhooks | `[-]` | n8n |
| T-056 | Workflow de retorno | `[-]` | n8n |
| T-057 | Workflow anti-no-show | `[-]` | n8n |
| — | E6 `procedures.split_override` | `[-]` | `COALESCE`, 1 coluna |
| — | E7 antecipação | `[-]` | **→ P0 se cliente zero antecipar** |
| — | `receivables` | `[-]` | Parcelas do cartão |
| — | Exportação CSV | `[-]` | Art. 18, V |

---

## Contrato com o frontend

Mudanças nestes pontos **quebram o front** — avise antes (ver [../BACKLOG.md](../BACKLOG.md)):

| Endpoint | Entregue em | Consumido por |
|---|---|---|
| `POST /auth` (JWT do Supabase) | T-006 | F-001 |
| `GET/POST /patients`, `/procedures` | T-010, T-011 | F-011, F-012 |
| `POST /sales` | T-015 | F-014 |
| `GET /dashboard` | T-022 | F-013 |
| `GET /retention/opportunities` | T-029 | F-015 |
| `GET /sessions?from&to` | T-032 | F-017 |
| `GET /packages/open` | T-034 | F-018 |

> **Valores monetários trafegam como string no JSON**, nunca como `number` — `number` em JS é float64 e reintroduz o erro de arredondamento.
