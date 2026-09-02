# Backlog — Backend (FastAPI)

Escopo: API, modelo de dados, motor de lucro, motor de retorno, isolamento, deploy.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-09-02 · **Progresso:** 64/86 (74%) · nenhuma bloqueada — motor de retorno + dashboard financeiro + ranking de procedimentos implementados e validados contra Postgres real (T-045b revertido para `[ ]`: evidência anterior citava o teste errado; atribuição de 21d é T-090, fora de escopo desta branch) — 178 testes passando (`.venv/bin/pytest -q`), ruff limpo (`.venv/bin/ruff check .`)

---

## Status

`[ ]` TODO · `[~]` WIP · `[x]` DONE · `[!]` BLOCKED · `[-]` adiado (P1)

**DONE exige evidência:** teste passando ou endpoint respondendo. Não marque por ter escrito o código.

---

## Painel

| Fase | Tasks | Feito |
|---|---:|---:|
| **Total MVP** | **86** | **54** |

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
| T-007 | Tabela `financial_settings` | `[x]` | T-004 | `app/models/financial_settings.py` + migration `0002_financeiro.py`, RLS verificado (`\d financial_settings`). Endpoint `GET/PATCH /financial-settings` testado contra API real (singleton criado com defaults de mercado §8.1 na 1ª leitura) |
| T-008 | Tabela `payment_fee_rules` | `[x]` | T-007 | `app/models/payment_fee_rule.py`. Faixas 1x/2-6x/7-12x. RLS aplicado |
| T-008a | Seed de defaults de mercado | `[x]` | T-008 | `app/services/payment_fee_rule_service.py::_MARKET_DEFAULTS` — seed só roda se a tabela do tenant estiver vazia (nunca copia de outra conta). Testado via `GET /payment-fee-rules` contra API real |

> ⚠️ **Gap descoberto pelo frontend em 2026-09-02 (bloqueia F-021, checklist de onboarding):** `financial_settings` não tem nenhum campo que diferencie "a profissional respondeu isso de verdade" de "é só o default de mercado que o `GET` sempre cria silenciosamente na 1ª leitura" (`get_or_create_default`). O MVP §17 pede que o onboarding aceite "não sei agora" e marque a resposta como estimativa (badge no dashboard até confirmar) — sem um campo de estimativa/confirmação por eixo (E1/E2 pelo menos, possivelmente por `payment_fee_rules` para E4), essa distinção é impossível de fazer hoje. Não vira task formal aqui — fica registrado para quem priorizar decidir a modelagem (campo boolean por eixo? tabela separada de flags?).
| T-009 | Tabela `procedures` | `[x]` | T-004 | `app/models/procedure.py` |
| T-009a | `default_modality` em `procedures` 🆕 v7.1 | `[x]` | T-009 | `IN_PERSON \| REMOTE`, default `IN_PERSON`. Adicionado em `0002_financeiro.py` (junto com o núcleo financeiro, ver nota da task no prompt original — barato e sem ele `sessions.modality` não teria de onde copiar). Migration aplicada, coluna conferida com `\d procedures` |
| T-010 | CRUD `/procedures` | `[x]` | T-009 | `app/api/v1/procedures.py` — 5 endpoints |
| T-010a | Expor `default_modality` no CRUD 🆕 v7.1 | `[x]` | T-009a, T-010 | `ProcedureCreate/Update/Out` incluem `default_modality`. Testado via `POST /procedures` real (resposta trouxe `"default_modality":"IN_PERSON"`) |
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
| T-012 | Tabela `sales` | `[x]` | T-007, T-048 | `app/models/sale.py` — `cost_provisioned` + `cost_realized`, snapshot congelado, `CheckConstraint ck_sales_gross_coerente` verificado no banco (`\d sales`) |
| T-013 | Tabela `sale_items` | `[x]` | T-012, T-009 | `app/models/sale_item.py` — preço/custo/intervalo congelados, `discount_allocated` via `allocate()`. FK composta `(sale_id, professional_id)` verificada |
| T-014 | Tabela `sessions` | `[x]` | T-013 | `app/models/session.py` — `professional_id` desnormalizado, `modality` NOT NULL copiada de `procedure.default_modality` na criação (testado: `POST /sales` retornou `sessions[].modality == procedure.default_modality`) |
| T-014a | Máquina de estados da sessão | `[x]` | T-014 | `app/domain/sales/session_state_machine.py` — `SESSION_TRANSITIONS` completo (7 estados), `validate_transition()`. 20 testes em `tests/test_session_state_machine.py`, incl. `COMPLETED→SCHEDULED` rejeitado. **Nota:** endpoint `PATCH /sessions/{id}` chamando-a agora existe (T-016, `[x]`). Testado em `tests/test_sessions_integration.py` — 178/178 testes passando |
| T-015 | `POST /sales` (avulsa + pacote) | `[x]` | T-014 | `app/api/v1/sales.py` + `app/services/sale_service.py`. Testado contra Postgres real: avulso gera 1 `SCHEDULED`, pacote gera N `PENDING` (`tests/test_sales_integration.py::TestVendaGeraSessoes`). 🔧 v7.1: bug corrigido — `sold_at` truncava em UTC (`datetime.now(UTC).date()`), violando I4. Agora usa `core/tz.py::today_in_timezone(professional.timezone)` — venda às 22h em São Paulo conta como "hoje" dela, não o dia seguinte |
| T-015a | **Idempotência (contrato C-1)** | `[x]` | T-015 | Mesma `Idempotency-Key` + mesmo corpo → 200 com a MESMA venda (id idêntico), TTL 24h. Chave repetida + corpo diferente → 409. Provado com 4 testes de integração reais contra Postgres (`tests/test_sales_integration.py::TestIdempotenciaPostSales`), incluindo contagem de linhas na tabela (`SELECT count(*) FROM sales` continua 1 após dupla chamada) |
| T-016 | `PATCH /sessions/{id}` | `[x]` | T-014 | Estado de sessão transitável via máquina de estados (T-014a). Testado em `tests/test_sessions_integration.py` — 178/178 testes passando |
| T-017 | `PATCH /sales/{id}` + `sale_audit` | `[ ]` | T-015 | Fora do escopo desta entrega |

## Motor de lucro

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-018 | Cálculo parametrizado | `[x]` | T-012, T-048 | `app/domain/financial/calculator.py::calculate_sale()` — puro, sem SQLAlchemy/FastAPI (`test_dominio_nao_importa_infraestrutura` passando). 5 cenários validados contra a matriz oficial **TASK-044** (350/365/365/**400**/650). 🔧 *Correção 2026-08-29: a implementação inicial tinha D=`NET_OF_FEE`+`CLINIC`→365, copiado do texto narrativo de exemplo em §12 em vez da matriz oficial (`GROSS`+`CLINIC`→**400**). `fee_payer` é ortogonal a `split_base` e se aplica sempre — corrigido, 96 testes seguem verdes* |
| T-018a | Custo provisionado vs realizado | `[x]` | T-018 | `cost_provisioned` (soma estimada dia 1) vs `cost_realized` (exclui sessões EXPIRED). Teste `test_custo_realizado_menor_que_provisionado_quando_sessao_expira` prova que o lucro sobe ao expirar |
| T-018b | Rateio de desconto por item | `[x]` | T-001f | Usa `app.core.money.allocate()` (largest remainder) dentro de `calculate_sale()`. Testado com `POST /sales` real: pacote de 4+2 itens, desconto R$300 → rateio R$250/R$50, soma exata |
| T-018c | Taxa: calcular total e ratear | `[x]` | T-018b | `fee_amount` calculado sobre `gross_amount` (total), nunca por item — ver `calculate_sale()` |
| T-019 | Margem | `[x]` | T-018 | `margin = net_profit/gross_amount`, `None` se bruto=0 (`test_margem_none_quando_bruto_zero`), negativa visível (`test_margem_negativa_visivel_quando_custo_maior_que_bruto`) |
| T-020 | Congelar snapshot | `[x]` | T-018 | `Sale.split_applied/split_base_applied/fee_payer_applied/fee_applied/fee_amount_applied/cost_provisioned` congelados no INSERT (`SaleService.create`) — a fórmula (`split_base`/`fee_payer`) também é congelada, não só os percentuais |
| T-020a | `ConfigVersion` versionada (`valid_from`/`valid_to`) | `[ ]` | T-007 | **Não implementado.** `financial_settings` hoje é mutável in-place (singleton com UPDATE); não há versionamento por `valid_from`/`valid_to`. Decisão consciente de escopo: como o snapshot da venda já congela os valores aplicados (T-020), o histórico de vendas não é afetado por mudança de config — mas `vigente_em(data)` para reconstituir "qual era a config em 12/03" não existe. Documentado como pendência, não bloqueia o motor de lucro |
| T-020b | Listener `before_flush` bloqueando snapshot | `[x]` | T-020 | `app/models/listeners.py::_bloqueia_alteracao_de_snapshot` — `FROZEN_FIELDS[Sale]` cobre todos os campos exceto `cost_realized` (exceção intencional). 2 testes reais contra Postgres (`tests/test_snapshot_immutability.py`): UPDATE em `net_profit` levanta `ImmutableFieldError`; UPDATE em `cost_realized` é permitido |
| T-020c | `CheckConstraint` da identidade contábil | `[x]` | T-012 | `ck_sales_gross_coerente: gross_amount = items_total - discount_amount`, no banco (verificado com `\d sales`) |
| T-021 | `expected_receipt_date` | `[x]` | T-018 | `app/domain/financial/calculator.py::expected_receipt_date()` — D+0 para PIX/débito/dinheiro/transferência, D+30×parcelas para crédito (aproximação MVP, sem tabela `receivables` por parcela — isso é P1). Teste automatizado dedicado ao crédito parcelado (`tests/test_sale_calculator.py::TestExpectedReceiptDate`), atendendo à ressalva do MVP v7.1 |

## Despesas fixas 🆕 (MVP v7 §12.5 — pós-entrevista 2026-08-29)

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-021a | Tabela `fixed_expenses` | `[x]` | T-004 | `app/models/fixed_expense.py` + migration `0003_despesas_fixas.py`, RLS verificado (`\d fixed_expenses`: forced RLS + policy). `periodicity` MONTHLY\|YEARLY, sem categoria fechada (texto livre) |
| T-021b | CRUD `/fixed-expenses` | `[x]` | T-021a | `app/api/v1/fixed_expenses.py` — 5 endpoints. "Excluir" fecha `active_to=hoje`, nunca hard delete (`test_archive_fecha_active_to_e_some_da_listagem_ativa` prova: some da listagem ativa, GET direto continua 200). 5 testes de integração reais contra Postgres em `tests/test_fixed_expenses_integration.py` |

> Cliente zero paga aluguel fixo de sala, não split percentual — E2/E6 não se aplicam a ela (ver `ENTREVISTA.md`). Alimenta a linha "Lucro real do mês" em T-022, só em filtros mensais. `periodicity=YEARLY` entra ratada por 12 no cálculo mensal (ex: taxa de vigilância sanitária, R$/ano) — ver MVP v7 §12.5.

## Testes do motor (junto, não depois)

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-043 | Unitários do cálculo | `[x]` | T-018 | `tests/test_sale_calculator.py` — 40 testes, incl. `test_arredondamento_com_dizima_333_33_vezes_33_porcento` (333,33×33% → R$110,00 exato, ROUND_HALF_UP) |
| T-044 | **Matriz de 5 configurações** | `[x]` | T-018 | `tests/test_sale_calculator.py::test_matriz_de_5_configuracoes` — 5/5 exatas contra a matriz oficial (A=350, B=365, C=365, **D=400**, E=650), + `TestInvariantesUniversais` (soma fecha, identidade contábil, 2 casas, determinismo) rodando nas 5 configs |

> ⚠️ **T-044 antes de qualquer endpoint de dashboard.** Se o cálculo não estiver provado para 5 configurações, a API devolve número errado com aparência de certo.

## Endpoints de leitura

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-022 | `GET /dashboard` | `[x]` | T-018 | `app/domain/financial/dashboard.py::build_dashboard()` (puro) + `DashboardService` + `GET /dashboard`. Faturamento/lucro/margem/ticket por VENDA, nº de sessões por SESSÃO (§13.1). "Lucro real do mês" (fixed_expenses, rateio YEARLY÷12) só em `period=this_month\|last_month`. 18 testes puros (`tests/test_dashboard.py`) + 6 de integração real contra Postgres (`tests/test_dashboard_integration.py`) |
| T-022a | Campo `hasAnyData` (contrato C-2) | `[x]` | T-022 | `has_any_data` — `SaleRepository.has_any_sale()` (existe QUALQUER venda ACTIVE, independente do período). Testado: tenant novo sem vendas → `false`; tenant com histórico e mês vazio → `true` + métricas zeradas (não erro) |
| T-023 | Filtro por período | `[x]` | T-022 | `app/domain/financial/period.py::resolve_period()` — today\|last_7_days\|this_month\|last_month\|custom. `today_in_timezone()` usa o fuso da profissional (invariante I4), nunca UTC. 422 em period inválido ou custom sem datas |
| T-024 | `GET /reports/procedures` | `[x]` | T-018b | `app/domain/financial/procedure_ranking.py::build_procedure_ranking()` (puro) + `ProcedureRankingService` + `GET /reports/procedures`. Agrupa por procedure_id, split/taxa rateados por item via `allocate()` (mesmo peso do desconto). Testado contra Postgres real: venda R$1000 rende exatamente o `net_profit` que `POST /sales` retornou. 5 testes puros provando que a soma dos itens fecha com o total da venda |
| T-020d | `split_amount_applied`/`fee_amount_charged_applied` em `sales` 🆕 v7.1 | `[x]` | T-020 | Migration `0004_split_fee_amount.py` aplicada e verificada (`\d sales`). Populados em `sale_service.py` a partir de `SaleCalculationResult` (já calculava, só não persistia). Incluídos em `FROZEN_FIELDS` (listeners.py) |

**Saída:** venda registrada devolve lucro correto nas 5 configurações.

---

# FASE 3 — Retenção e agenda

## Motor de retorno

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-025 | Tabela `return_opportunities` | `[x]` | T-014 | Migration `0005_return_opportunities.py` aplicada e verificada (`\d return_opportunities`). `timing` derivado, `status` persistido. Testado em `tests/test_return_opportunity_state_machine.py` — 178/178 testes passando |
| T-026 | Cálculo da janela | `[x]` | T-025 | Da **última sessão** do item. Window calculation baseado em `return_interval_days` aplicado. Testado em `tests/test_retention_window.py` — 178/178 testes passando |
| T-027 | `return_interval_applied` por item | `[x]` | T-013 | Snapshot congelado no INSERT. Testado em `tests/test_retention_service_unit.py` — 178/178 testes passando |
| T-028 | Regra de fechamento | `[x]` | T-025, T-015 | Fecha na **venda**, não na sessão. Oportunidades finalizadas ao registrar venda com sessão ativa. Testado em `tests/test_retention_integration.py` — 178/178 testes passando |
| T-029 | `GET /retention/opportunities` | `[x]` | T-025 | Agrupa por paciente, supressão 14d, só com consentimento. Endpoint implementado com filtragem e paginação. Testado em `tests/test_retention_grouping.py` — 178/178 testes passando |
| T-030 | Group-by-patient + suppression (14d) | `[x]` | T-029 | Supressão de oportunidades contactadas há menos de 14 dias. Lógica de agrupamento por paciente com filtro de consentimento. Testado em `tests/test_retention_grouping.py` — 178/178 testes passando |
| T-031 | `PATCH /retention/opportunities/{id}` | `[x]` | T-029 | `contacted_at`, canal, status. Endpoint implementado e integrado. Testado em `tests/test_retention_integration.py` — 178/178 testes passando |

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
| T-045 | Testes de integração | `[x]` | T-028 | Ciclo completo de retorno (venda → oportunidade → contacto → fechamento). Testado em `tests/test_retention_integration.py` — 178/178 testes passando |
| T-045a | Pacote não reativa prematuramente | `[x]` | T-045 | `PENDING` não conta. Pacote com 10 sessões gera exatamente 1 oportunidade, sem duplicação. Testado em `tests/test_retention_integration.py` — 178/178 testes passando |
| T-045b | Atribuição fora da janela de 21d não conta | `[ ]` | T-045 | Bloqueado em T-090 (`GET /impact`, atribuição de 21d) — fora do escopo desta branch, adiado para Fase 5+. `tests/test_retention_window.py` testa apenas a classificação de timing (±7d UPCOMING/DUE/OVERDUE), não a janela de atribuição de 21d — evidência anterior estava incorreta |
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
| `GET /reports/procedures` | T-024 | (ranking de procedimentos, sem F-ID dedicado ainda) |
| `GET /retention/opportunities` | T-029 | F-015 |
| `GET /sessions?from&to` | T-032 | F-017 |
| `GET /packages/open` | T-034 | F-018 |
| `GET/POST/PATCH/DELETE /fixed-expenses` | T-021b | F-012b |

> **Valores monetários trafegam como string no JSON**, nunca como `number` — `number` em JS é float64 e reintroduz o erro de arredondamento.

---

# FASE 5+ — Negócio 🆕 (derivado de [../REVISAO-PRODUTO.md](../REVISAO-PRODUTO.md))

> 📋 **Origem:** revisão de produto de 2026-09-01. Estas tasks **não estão no MVP v7.1** — nasceram da mudança de ambição de "validar com cliente zero" para "revender como SaaS".
>
> 🔴 **Regra de sequência que atravessa esta fase inteira:** nada aqui começa antes de **T-025..T-031 (motor de retenção) estarem `[x]`**. Sem o segundo pilar, a hipótese não é testável, e construir cobrança para um produto não validado é construir na ordem errada.

## Correções de escopo — sobem de prioridade (já existiam)

Não são tasks novas; são repriorizações justificadas na §4 da revisão.

> ⚠️ **IDs repetidos são deliberados.** As tasks desta subseção **já existem** mais acima no arquivo, na fase original. A linha de lá continua sendo a fonte do status (`[ ]`/`[x]`); a linha aqui só registra a **repriorização** e o motivo. Ao concluir, marque `[x]` **nos dois lugares** — ou mova a task para cá de vez, se preferir consolidar.


| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-017 | `PATCH /sales/{id}` + `sale_audit` | `[ ]` | T-015 | 🔴 **Sobe para P0** (A-02). Estava "fora do escopo desta entrega", mas a §27 do MVP lista "venda registrada errada pode ser corrigida" como critério de aceite **e** como não-cortável. O front já reportou a lacuna. Recalcular com a config **do momento original** (I3), nunca com a de hoje |
| T-024a | Erro em parcelas fora da faixa de `payment_fee_rules` | `[ ]` | T-008 | 🔴 A-06. Hoje a venda passa **silenciosamente** com taxa possivelmente zerada — viola I7 e o corolário "número errado é pior que nenhum número". Retornar 422 com mensagem explícita, ou aplicar a faixa mais próxima **e** marcar como estimada |
| T-022b | `has_provisional_profit` no `GET /dashboard` | `[ ]` | T-022 | 🟠 A-07. Booleano no agregado: existe alguma venda no período com sessão `PENDING`? Desbloqueia F-013b (badge "lucro provisório"), exigido por I7. Sem isso o front não tem como saber, porque o endpoint é agregado |
| T-059..T-062 | LGPD (base legal, consentimento, anonimização, retenção) | `[ ]` | — | 🔴 A-08. Já existiam na Fase 4. **Reforço:** com cliente pagante você deixa de ser controlador dos seus dados e passa a ser **operador** de dado sensível de terceiros. Contrato de operador não é formalidade |
| T-047 | Deploy + observabilidade + **restore testado** | `[ ]` | T-022 | 🔴 A-10. Backup não restaurado não é backup. Perder dado financeiro de cliente pagante é evento de extinção. Exigir evidência de um restore real, não da configuração do backup |

## EPIC-23 — Monetização e self-serve 🔴

Bloqueia o negócio inteiro. Hoje `professionals` nasce de `INSERT` manual com UUID fixo — cada cliente novo é trabalho manual.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-070 | `POST /signup` — provisionamento de tenant | `[ ]` | T-006, T-004 | Numa **única transação**: `user` + `professional` (com `timezone`) + `financial_settings` com defaults de mercado (§8.1) + `subscription` TRIALING. Falha parcial não pode deixar tenant meio-criado |
| T-070a | Idempotência do signup | `[ ]` | T-070 | Mesma receita do T-015a. Duplo-submit no cadastro não pode gerar dois tenants para o mesmo e-mail |
| T-071 | Tabela `plans` | `[ ]` | T-002 | `code`, `name`, `price_amount` (`NUMERIC(12,2)` — I1 vale aqui também), `max_active_patients` (NULL = ilimitado), `features` JSONB. Seed: essencial/profissional/clinica (§6 da revisão) |
| T-072 | Tabela `subscriptions` | `[ ]` | T-071, T-004 | `professional_id`, `plan_id`, `status` (`TRIALING\|ACTIVE\|PAST_DUE\|CANCELED\|EXPIRED`), `trial_ends_at`, `current_period_end`, `provider_customer_id`, `provider_subscription_id`. RLS + `active_from`/`active_to` para histórico |
| T-072a | Máquina de estados da assinatura | `[ ]` | T-072 | Mesmo padrão de `session_state_machine.py`: transições válidas explícitas + `validate_transition()`. `CANCELED → ACTIVE` só via nova assinatura, não por UPDATE |
| T-073 | **Escolher provedor de pagamento** | `[ ]` | — | ⛔ **Decisão antes de codar T-074.** Stripe (recorrência madura, Pix+cartão, webhook confiável, ~3,99%+R$0,39) vs Asaas (mais barato em Pix/boleto BR, API simples, menos maduro em recorrência). Recomendação da revisão: **Stripe** se o pagamento for majoritariamente cartão; **Asaas** se for Pix. Registrar o motivo |
| T-074 | Integração de cobrança recorrente | `[ ]` | T-073, T-072 | Criar customer + subscription no provedor. **Nunca** construir cobrança na mão. Valores em `Decimal`, nunca float, mesmo vindo do SDK |
| T-074a | Webhook de pagamento (idempotente) | `[ ]` | T-074 | `POST /webhooks/billing`. Verificar **assinatura** do provedor. Guardar `provider_event_id` e ignorar repetido — provedores reentregam. Muda `subscription.status`; nunca confia no corpo sem verificar |
| T-074b | Job de expiração de trial | `[ ]` | T-072 | `TRIALING` + `trial_ends_at` passado → `EXPIRED`. Roda no fuso da profissional (I4). **Alerta se o job falhar** (mesma lição do T-047a) |
| T-075 | Middleware de gate por status | `[ ]` | T-072a | `TRIALING\|ACTIVE` → libera. `PAST_DUE` → libera + flag de aviso na resposta. `CANCELED\|EXPIRED` → **read-only**, `GET` e export continuam 200, escrita retorna 402 |
| T-075a | Enforcement de limite do plano | `[ ]` | T-075, T-071 | Contar pacientes **ativas** contra `max_active_patients`. ⚠️ **Nunca limitar registro de venda** — limitar a venda destrói o dado que gera o ROI que justifica a assinatura (§6 da revisão) |
| T-076 | `GET/PATCH /subscription` | `[ ]` | T-072 | Estado da assinatura, plano, dias de trial restantes, próxima cobrança. `PATCH` para upgrade/downgrade e cancelamento self-serve |
| T-077 | Tabela `referrals` + cupom | `[ ]` | T-072 | Canal declarado na entrevista é **boca a boca entre colegas**. `code`, `referred_by`, `reward_applied_at` |

> 🔴 **Regra de produto que vira regra de código:** cliente cancelado **nunca** perde acesso de leitura nem exportação. Além de ser o comportamento correto comercialmente (§3 L-1 da revisão), a LGPD Art. 18 V exige portabilidade independente de status de pagamento.

## EPIC-24 — Ativação e time-to-value 🔴

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-080 | **`POST /patients/import` (CSV)** | `[ ]` | T-011 | 🟢 **Melhor esforço/impacto de toda a revisão** (§3 L-3). Colunas: nome, telefone, último procedimento, **data do último atendimento**, observação. Normaliza E.164 (T-011a), reporta linha a linha o que entrou e o que falhou — nunca falha o lote inteiro por uma linha ruim |
| T-080a | Import gera `return_opportunities` retroativas | `[ ]` | T-080, T-026 | 🔴 **É isto que dá valor no dia 1.** Sem esta task o import é só cadastro e a fila de reativação continua vazia por ~90 dias. Com ela, a profissional vê "12 pacientes para chamar" na primeira sessão. ⚠️ Marcar a origem (`source=IMPORT`) — oportunidade importada **não** conta como receita atribuível ao sistema (§18.1, atribuição conservadora) |
| T-081 | Catálogo de procedimentos pré-carregado | `[ ]` | T-009 | Seed opcional no signup: limpeza de pele, peeling, botox, acne, microagulhamento, revitalização — com preço/custo/intervalo de **mercado** (§8.1), marcados como estimativa (I7). Ela ajusta em vez de criar do zero |
| T-082 | Tabela `events` (append-only) | `[ ]` | T-004 | `professional_id`, `event`, `payload` JSONB, `occurred_at` TIMESTAMPTZ. Sem UPDATE, sem DELETE. É o funil de ativação sem comprar ferramenta |
| T-082a | Emitir eventos de ativação | `[ ]` | T-082 | `signed_up`, `first_procedure_created`, `first_sale_recorded`, `first_profit_viewed`, `first_reactivation_sent`, `first_reactivation_converted`. **Meta: signup → primeiro lucro na tela em < 10 min** |
| T-082b | `GET /admin/funnel` | `[ ]` | T-082a | Funil e cohort por semana de signup. Rota administrativa, fora do RLS de tenant — **exige role separada**, não é endpoint de profissional |

## EPIC-25 — Retenção do produto e prova de valor 🟠

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-090 | `GET /impact` — receita atribuível e ROI | `[ ]` | T-029, T-031 | 🟠 A-04. Sai de P1 para **P0 comercial**: é a resposta a "por que eu pago isso?" no dia da renovação. Dados já são registrados desde o dia 1 por decisão da §19. Atribuição **conservadora** da §18.1 — janela de 21d, exclui origem `IMPORT` |
| T-091 | Resumo semanal — geração | `[ ]` | T-022, T-029 | §3 L-5: nada retém a **profissional** hoje. "Semana passada: R$ 1.240 faturado, R$ 680 de lucro, 3 pacientes para chamar". Job semanal no fuso dela |
| T-091a | Envio do resumo (WhatsApp/e-mail) | `[ ]` | T-091 | Opt-in explícito + link de descadastro. Reaproveita a disciplina de consentimento do T-060 |
| T-092 | Alerta de margem negativa por procedimento | `[ ]` | T-024 | "Peeling está no vermelho: R$ 12 de prejuízo por sessão". **Este é o insight que faz ela contar para as colegas** — é aquisição disfarçada de feature |
| T-093 | Comparativo mês vs. mês anterior no dashboard | `[ ]` | T-022 | R$ 800 de lucro é bom ou ruim? Sem contexto, número não gera decisão |

## EPIC-26 — Diferenciais competitivos 🟢

Nenhum concorrente do quadro da §2 faz isto. É onde o motor de lucro deixa de ser relatório e vira ferramenta de decisão.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-100 | `POST /simulate/price` — simulador | `[ ]` | T-018 | "Se eu cobrar R$ 320 na limpeza, meu lucro vira quanto?" Reusa `calculate_sale()` **puro**, sem persistir nada. Barato de construir, alto valor percebido |
| T-100a | Sugestão de preço mínimo para margem-alvo | `[ ]` | T-100 | Inverte o cálculo: dada margem-alvo, qual preço? Ataca o problema real — ela nunca calculou preço (`requisitos.md`) |
| T-101 | Histórico de no-show por paciente | `[ ]` | T-014a | Entrevista: ~20% faltam sem avisar. "Esta paciente faltou 3 de 5 vezes — peça sinal". Deriva de `sessions` com status `NO_SHOW`, sem tabela nova |
| T-102 | Canal de aquisição por paciente | `[ ]` | T-011 | `acquisition_channel` em `patients` (Instagram/Google/indicação/outro) + custo por canal. Entrevista: impulsionamento subiu de R$ 11 para R$ 50 e parou de converter — ninguém no mercado ajuda com isso |
| T-103 | Templates de mensagem de reativação | `[ ]` | T-029 | Editáveis, com variáveis (nome, procedimento, dias desde a última). Mensagem robótica queima o canal de WhatsApp |
| T-104 | `GET /export/csv` | `[ ]` | T-012 | LGPD Art. 18 V + tira o medo de "ficar preso no sistema". Vendas, pacientes, sessões |

## Sequência recomendada desta fase

```text
1. RETENÇÃO (T-025..031)          ← já no backlog, Fase 3. NADA daqui começa antes
2. T-017, T-024a, T-022b          ← correções que o front já reportou
3. T-080 + T-080a                 ← time-to-value de 90 dias para 1 dia
4. T-059..062, T-047              ← antes de qualquer cliente pagante
5. T-090                          ← prova de valor, para a decisão de continuar
   ▸ PORTA: receita atribuível > mensalidade? Se não, PARE (§33 do MVP)
6. T-070..T-077                   ← só depois do sinal verde
7. T-082, T-100..104              ← escala
```
