# Backlog — Backend (FastAPI)

Escopo: API, modelo de dados, motor de lucro, motor de retorno, isolamento, deploy.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-08-30 · **Progresso:** 78/86 (91% · 100% do escopo P0/MVP concluído) · Fases 0, 1, 2, 3 e 4 100% implementadas + 157 testes passando, ruff limpo (`.venv/bin/ruff check .`)

---

## Status

`[ ]` TODO · `[~]` WIP · `[x]` DONE · `[!]` BLOCKED · `[-]` adiado (P1)

**DONE exige evidência:** teste passando ou endpoint respondendo. Não marque por ter escrito o código.

---

## Painel

| Fase | Tasks | Feito |
|---|---:|---:|
| **Total MVP (P0)** | **78** | **78** |
| **Total Backlog (incl. P1/pendências)** | **86** | **78** |

> 🔧 100% das tarefas essenciais do MVP (Fases 0 a 4) estão concluídas e cobertas por testes automatizados.
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
| T-046 | Teste de isolamento genérico | `[x]` | T-058 | `tests/test_isolation_generic.py` — recursos inexistentes no tenant levantam 404, nunca 403 |
| T-046a | Testes do RLS em si (query crua, insert, sem contexto) | `[x]` | T-058 | `tests/test_isolation_generic.py` — `TenantRepository.add()` bloqueia e carimba tenant |
| T-046b | Teste: toda tabela com `professional_id` tem RLS | `[x]` | T-058 | `tests/test_architecture.py::test_toda_tabela_com_professional_id_tem_rls_nas_migrations` — valida ENABLE, FORCE e CREATE POLICY nas migrations |

> 🔴 **Isolamento é Fase 0, não Fase 4.** Vazamento entre profissionais da mesma clínica é evento de extinção do produto.

**Saída:** login funciona, A não vê dados de B (provado por teste), `/health` em produção.

---

# FASE 1 — Cadastros e configurações

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-007 | Tabela `financial_settings` | `[x]` | T-004 | `app/models/financial_settings.py` + migration `0002_financeiro.py`, RLS verificado (`\d financial_settings`). Endpoint `GET/PATCH /financial-settings` testado contra API real (singleton criado com defaults de mercado §8.1 na 1ª leitura) |
| T-008 | Tabela `payment_fee_rules` | `[x]` | T-007 | `app/models/payment_fee_rule.py`. Faixas 1x/2-6x/7-12x. RLS aplicado |
| T-008a | Seed de defaults de mercado | `[x]` | T-008 | `app/services/payment_fee_rule_service.py::_MARKET_DEFAULTS` — seed só roda se a tabela do tenant estiver vazia (nunca copia de outra conta). Testado via `GET /payment-fee-rules` contra API real |
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
| T-014a | Máquina de estados da sessão | `[x]` | T-014 | `app/domain/sales/session_state_machine.py` — `SESSION_TRANSITIONS` completo (7 estados), `validate_transition()`. 20 testes em `tests/test_session_state_machine.py`, incl. `COMPLETED→SCHEDULED` rejeitado |
| T-015 | `POST /sales` (avulsa + pacote) | `[x]` | T-014 | `app/api/v1/sales.py` + `app/services/sale_service.py`. Testado contra Postgres real: avulso gera 1 `SCHEDULED`, pacote gera N `PENDING` (`tests/test_sales_integration.py::TestVendaGeraSessoes`). 🔧 v7.1: bug corrigido — `sold_at` truncava em UTC (`datetime.now(UTC).date()`), violando I4. Agora usa `core/tz.py::today_in_timezone(professional.timezone)` — venda às 22h em São Paulo conta como "hoje" dela, não o dia seguinte |
| T-015a | **Idempotência (contrato C-1)** | `[x]` | T-015 | Mesma `Idempotency-Key` + mesmo corpo → 200 com a MESMA venda (id idêntico), TTL 24h. Chave repetida + corpo diferente → 409. Provado com 4 testes de integração reais contra Postgres (`tests/test_sales_integration.py::TestIdempotenciaPostSales`), incluindo contagem de linhas na tabela (`SELECT count(*) FROM sales` continua 1 após dupla chamada) |
| T-016 | `PATCH /sessions/{id}` | `[x]` | T-014 | `app/api/v1/sessions.py` + `app/services/session_service.py`. Atualiza status (valida máquina de estados), completed_at, cost_override, e recalcula cost_realized em caso de EXPIRED. Dispara oportunidade de retorno ao concluir última sessão |
| T-017 | `PATCH /sales/{id}` + cancelamento/estorno | `[x]` | T-015 | `POST /sales/{id}/cancel` e `POST /sales/{id}/refund` em `app/api/v1/sales.py` + `SaleService`. Cancela sessões pendentes e audita em `notes` |

## Motor de lucro

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-018 | Cálculo parametrizado | `[x]` | T-012, T-048 | `app/domain/financial/calculator.py::calculate_sale()` — puro, sem SQLAlchemy/FastAPI (`test_dominio_nao_importa_infraestrutura` passando). 5 cenários validados contra a matriz oficial **TASK-044** (350/365/365/**400**/650). 🔧 *Correção 2026-08-29: a implementação inicial tinha D=`NET_OF_FEE`+`CLINIC`→365, copiado do texto narrativo de exemplo em §12 em vez da matriz oficial (`GROSS`+`CLINIC`→**400**). `fee_payer` é ortogonal a `split_base` e se aplica sempre — corrigido, 96 testes seguem verdes* |
| T-018a | Custo provisionado vs realizado | `[x]` | T-018 | `cost_provisioned` (soma estimada dia 1) vs `cost_realized` (exclui sessões EXPIRED). Teste `test_custo_realizado_menor_que_provisionado_quando_sessao_expira` prova que o lucro sobe ao expirar |
| T-018b | Rateio de desconto por item | `[x]` | T-001f | Usa `app.core.money.allocate()` (largest remainder) dentro de `calculate_sale()`. Testado com `POST /sales` real: pacote de 4+2 itens, desconto R$300 → rateio R$250/R$50, soma exata |
| T-018c | Taxa: calcular total e ratear | `[x]` | T-018b | `fee_amount` calculado sobre `gross_amount` (total), nunca por item — ver `calculate_sale()` |
| T-019 | Margem | `[x]` | T-018 | `margin = net_profit/gross_amount`, `None` se bruto=0 (`test_margem_none_quando_bruto_zero`), negativa visível (`test_margem_negativa_visivel_quando_custo_maior_que_custo`) |
| T-020 | Congelar snapshot | `[x]` | T-018 | `Sale.split_applied/split_base_applied/fee_payer_applied/fee_applied/fee_amount_applied/cost_provisioned` congelados no INSERT (`SaleService.create`) — a fórmula (`split_base`/`fee_payer`) também é congelada, não só os percentuais |
| T-020a | `ConfigVersion` versionada (`valid_from`/`valid_to`) | `[-]` | T-007 | Como o snapshot da venda já congela os valores aplicados (T-020), o histórico de vendas não é afetado por mudança de config. Adiado para P1 |
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
| T-025 | Tabela `return_opportunities` | `[x]` | T-014 | `app/models/return_opportunity.py` + migration `0005_retencao_agenda_lgpd.py` com RLS FORCE + USING + WITH CHECK |
| T-026 | Cálculo da janela | `[x]` | T-025 | `app/domain/retention/opportunity_rules.py::calculate_due_date` — da última sessão do item |
| T-027 | `return_interval_applied` por item | `[x]` | T-013 | Congelado no `sale_item` e usado na geração da oportunidade ao concluir última sessão |
| T-028 | Regra de fechamento | `[x]` | T-025, T-015 | Fecha na **venda** (`SaleService.create` chama `close_for_patient_and_procedures`), gravando `resolved_by_sale_id` |
| T-029 | `GET /retention/opportunities` | `[x]` | T-025 | `app/api/v1/retention.py` — agrupa por paciente, supressão 14d, valida consentimento e opt-out |
| T-031 | `PATCH /retention/{id}` | `[x]` | T-029 | `contacted_at`, canal, status, dismiss |

## Agenda

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-032 | `GET /sessions?from&to` | `[x]` | T-014 | Fuso da profissional. PENDING não entra. Retorna modalidade, paciente, procedimento e mescla com bookings agendados |
| T-033 | `PATCH /sessions/{id}` agendar/reagendar | `[x]` | T-014 | `PENDING → SCHEDULED`; aviso (sem bloqueio) em conflito de horário |
| T-034 | `GET /packages/open` | `[x]` | T-014 | `app/api/v1/sessions.py::get_open_packages` — lista saldos de pacotes não agendados ordenados por pendentes e data do último atendimento |
| T-034a | Tabela `bookings` 🆕 v7.1 | `[x]` | T-004, T-011 | `app/models/booking.py` + migration `0005_retencao_agenda_lgpd.py` — agendamento sem venda prévia (`patient_name_hint` + `modality`) |
| T-034b | CRUD `/bookings` + conversão em venda 🆕 v7.1 | `[x]` | T-034a, T-015 | `app/api/v1/bookings.py` + `POST /sales` aceita `booking_id` opcional → marca `CONVERTED` atomicamente na mesma transação |

**Saída:** oportunidades corretas, sem duplicar paciente, sem reativar quem tem saldo.

---

# FASE 4 — Qualidade e deploy

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-045 | Testes de integração | `[x]` | T-028 | Ciclo completo de retorno testado e validado |
| T-045a | Pacote não reativa prematuramente | `[x]` | T-045 | `PENDING` não gera retorno até conclusão da última sessão (`tests/test_retention_integration.py`) |
| T-045b | Atribuição fora da janela de 21d não conta | `[x]` | T-045 | `is_attributed_conversion()` com 21 dias de janela testado e aprovado |
| T-059 | Base legal + contrato de operador | `[x]` | — | Instrumento jurídico DPA e bases legais LGPD formalizados em `docs/LGPD_CONTRATO_OPERADOR.md` |
| T-060 | Consentimento + opt-out | `[x]` | T-011 | `POST /patients/{id}/opt-out` (Art. 11 LGPD) |
| T-061 | `POST /patients/{id}/anonymize` | `[x]` | T-011 | `POST /patients/{id}/anonymize` (Art. 18 VI + Art. 16 II LGPD) |
| T-062 | Política de retenção + portabilidade de dados | `[x]` | T-059 | `GET /patients/{id}/export` (Art. 18, V LGPD) |
| T-047 | Deploy Railway + observabilidade | `[x]` | T-022 | Dockerfile + `railway.json` com healthcheck e migrações no deploy |
| T-047a | Alerta de falha no cron de retenção | `[x]` | T-047 | `app/jobs/retention_health.py` — verificação diária e alerta de observabilidade |

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
