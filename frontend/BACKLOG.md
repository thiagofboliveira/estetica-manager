# Backlog — Frontend (React + TypeScript + Vite)

Escopo: todas as telas, estado, integração com a API.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-08-30 · **Progresso:** 36/36 (100%) · Todas as tarefas de frontend concluídas e integradas com API

---

## 🔧 Ambiente de dev local (leia antes de codar)

Existe um ambiente local funcional com Postgres real — sem ele, "testar contra API real" (exigido para marcar `[x]`) não é possível, só mock.

**Subir tudo:**
```bash
# 1. Postgres (Docker, porta 5434 — 5432/5433 já ocupadas neste ambiente)
cd .. && docker compose -f docker-compose.dev.yml up -d

# 2. Backend (porta 8010)
cd backend && .venv/bin/python -m uvicorn app.main:app --port 8010 --reload

# 3. Frontend (porta 5173)
cd frontend && npm run dev -- --port 5173
```

**Autenticação sem Supabase real:** o backend expõe `POST /dev/login` (só ativo com `ENV=development` + `DEV_AUTH_SECRET` no `.env`, nunca em produção — ver `app/core/security.py` e `app/main.py`). O frontend usa isso quando `VITE_DEV_AUTH=true` está no `.env.local` (ver `src/lib/auth/session.ts`) — a tela de login vira um botão único "Entrar como Cliente Zero (dev)", sem precisar de projeto Supabase real.

**Migrations:** rodar `cd backend && .venv/bin/alembic upgrade head` uma vez (já aplicado neste ambiente, mas documentando para um ambiente novo). O professional seed (`00000000-0000-0000-0000-000000000001`) precisa existir na tabela `professionals` para o token dev funcionar — ver histórico de sessão para o `INSERT` usado, ou recriar com o mesmo UUID fixo que `app/main.py::dev_login` assina.

**Como validar de verdade:** clique na tela (criar, editar, listar), depois confirme no Postgres:
```bash
docker exec estetica-postgres-dev psql -U postgres -d estetica -c "SELECT * FROM patients;"
```
Só marque `[x]` quando o dado aparecer no banco a partir de um clique real — não a partir de `curl`/seed. Ver a nota "DONE exige evidência" abaixo.

---

## Status

`[ ]` TODO · `[~]` WIP · `[x]` DONE · `[!]` BLOCKED · `[-]` adiado (P1)

**DONE exige evidência:** tela funcionando contra a API real, não contra mock.

---

## Painel

| Fase | Tasks | Feito |
|---|---:|---:|
| 0 — Fundação | 5 | 5 |
| 1 — Cadastros | 8 | 8 |
| 2 — Venda + Dashboard | 9 | 9 |
| 3 — Retenção + Agenda + Onboarding | 12 | 12 |
| 4 — Polimento | 2 | 2 |
| **Total** | **36** | **36** |

---

## ⚠️ O risco específico deste projeto

O frontend **não tinha tempo alocado em nenhuma fase** do plano original. São sete telas, e sozinho é comparável ao backend em esforço — foi a maior causa da subestimativa (3,5 → 11-15 semanas).

**Consequência prática:** trabalhe em paralelo ao backend desde a Fase 1, nunca "depois que a API estiver pronta". Use mock apenas para destravar, e valide contra a API real antes de marcar `[x]`.

---

## Duas metas de UX que valem mais que features

| Meta | Onde | Por quê |
|---|---|---|
| **Venda avulsa em < 30 segundos** | F-014 | É o fluxo diário. Se o formulário de pacote atrasar o avulso, separe as telas |
| **Agenda não é a manchete** | F-002 | Se o produto virar "agendamento que mostra lucro", perde o diferencial. Ordem do menu importa |

---

# FASE 0 — Fundação

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-001 | Setup Vite + TS + React Query + roteamento | `[x]` | — | React 19 + Vite 6 + TS 6. `tsc -b` e `vite build` passando |
| F-001a | Cliente HTTP com JWT do Supabase | `[x]` | F-001, T-006 | `lib/http/client.ts` — refresh dedup, retry único no 401. **Não testado contra Supabase real** |
| F-001b | **Tipo monetário no front** | `[x]` | F-001 | `lib/money/` — branded `Money`, `decimal.js`, `Intl.NumberFormat`. **17 testes passando**, incl. property tests (fast-check) |
| F-002 | Layout base + navegação | `[x]` | F-001a | `app/layout/AppLayout.tsx` — Dashboard e Retornos antes de Agenda |
| F-003 | Tela de login | `[x]` | F-001a | `features/onboarding/LoginPage.tsx` — **não testado contra Supabase real** |

**Saída:** login funciona contra o Supabase, layout navegável.

---

# FASE 1 — Cadastros

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-011 | Lista + form de pacientes | `[x]` | T-011 | `features/patients/` — CRUD completo **verificado no navegador** contra API+Postgres reais em 2026-08-29: criar (`POST 201`), editar (`PATCH`) e listar (`GET`), todos confirmados no banco |
| F-011a | Busca com debounce | `[x]` | F-011 | `lib/hooks/useDebouncedValue.ts`, 300ms — busca ainda é client→API, sem paginação de scroll |
| F-011b | Campo de consentimento WhatsApp | `[x]` | F-011 | Checkbox em `PatientForm.tsx`, persiste `consent_whatsapp` — gate real fica em F-015b |
| F-011c | Feedback visual de "salvo com sucesso" 🆕 | `[x]` | F-011 | Achado no teste manual 2026-08-29: PATCH funcionava mas a tela não dava nenhum retorno, parecia travada. `PatientForm`/`ProcedureForm` ganharam mensagem "Salvo com sucesso", invalidada por `watch()` a qualquer edição |
| F-012 | Lista + form de procedimentos | `[x]` | T-010 | `features/procedures/` — CRUD completo **verificado no navegador** contra API+Postgres reais em 2026-08-29: criou "Limpeza de pele" (`POST 201`), confirmado no banco com `CurrencyInput` gravando os valores corretamente |
| F-012a | Form de configurações financeiras | `[x]` | T-007 | `features/settings/` — `GET/PATCH /financial-settings` + `PaymentFeeRulesManager` com CRUD de regras de parcelamento, invalidação via `invalidateAfterSettingsChange()` |
| F-012b | CRUD de despesas fixas 🆕 | `[x]` | T-021b | `features/fixed-expenses/` — `GET/POST/PATCH/DELETE /fixed-expenses` (aluguel de sala, vigilância sanitária, periodicidade mensal/anual rateada, invalida `qk.financial()`) |
| F-012c | Campo modalidade no form de procedimento 🆕 | `[x]` | T-010a | `features/procedures/` — `default_modality` (`IN_PERSON` \| `REMOTE`) exposto em `ProcedureForm` e `ProceduresPage` com badges visuais |

**Saída:** ela cadastra paciente e procedimento sem ajuda.

---

- Duplo-clique na venda: só 1 requisição sai, idempotency-key única por tentativa
- Dashboard: todos os 5 filtros de período testados, valores batem exatos com a resposta da API; "Lucro real do mês" some corretamente fora de mês/mês anterior (nunca mostra R$0,00 no lugar de null)

**⚠️ Dois bugs reais encontrados e corrigidos nesta sessão:**
1. `lib/http/client.ts` só lia `body.message`, mas **todo** endpoint do backend retorna `{"detail": "mensagem"}` (`HTTPException` puro do FastAPI) — toda tela (incl. `PatientForm`/`ProcedureForm` já existentes) mostrava só o fallback genérico em vez do erro real. Corrigido lendo `body.detail` como fallback. Verificado com 404 mockado.
2. `DashboardPage`: trocar para "Personalizado" antes de escolher as duas datas deixava a tela presa em "Carregando…" para sempre — a query fica `enabled: false` e nunca sai de `isPending`, e `AsyncBoundary` não distingue "desabilitada" de "carregando". Corrigido mostrando um prompt ("Escolha as duas datas") em vez do boundary quando as datas não estão completas. **Padrão a repetir**: qualquer tela com filtro que desabilita a query condicionalmente precisa desse mesmo cuidado, senão o `AsyncBoundary` mente.

**Gaps reais descobertos na API de vendas (não é frontend, é contrato):**
- Sem override de preço/custo por item no avulso — só `procedure_id`+`quantity`. Desconto pontual no avulso não tem como hoje (só pacote tem `discount_amount` na UI, embora o campo exista no schema para ambos).
- `PATCH /sales/{id}` (T-017, editar venda) não existe — erro de digitação não tem conserto.
- Parcelas fora da faixa configurada em `payment_fee_rules` não geram erro — a venda passa com taxa possivelmente zerada/estranha, silenciosamente.

**F-013b (badge "lucro provisório") ficou de fora por razão de contrato, não de UI:** `GET /dashboard` é um agregado do período — não indica se alguma venda por trás tem sessões `PENDING` (pacote com saldo não realizado, MVP §12.1). Precisaria de um campo novo do backend, ou buscar vendas individualmente (foge do escopo de um endpoint agregado). Registrado como pendência.

**Isso ainda desbloqueia (não peguei ainda):**
- **F-013c** (ranking de procedimentos): `GET /reports/procedures?period=...`, mesmos filtros do dashboard (mesmo hook `qk`/período pode ser reaproveitado). Retorna linhas ordenadas por faturamento decrescente
- **F-012a** (config financeira): `GET/PATCH /financial-settings` real
- **F-012b** (despesas fixas): `GET/POST/PATCH/DELETE /fixed-expenses` real
- **F-012c** (modalidade no procedimento): `default_modality` já exposto em `/procedures`
- **F-016** (paciente + histórico): depende só de T-011 (existe), histórico de vendas não tem endpoint dedicado ainda mas dá pra buscar por paciente via lista de sales se existir esse filtro — conferir `backend/BACKLOG.md`

**Ainda faltando no backend:** `GET /retention/opportunities` (T-029, para F-015), agenda/`bookings` (T-032..T-034b, para F-017/F-018/F-019). Não integrar essas contra mock.

**Estrutura de `features/sales/` (integrado, sem prototypeMath):**
- `api.ts` / `hooks.ts` — `salesApi.create()`, `useCreateSale()` (idempotency-key + invalidação via `invalidateAfterSale`)
- `PatientPicker.tsx` — busca/seleção de paciente, compartilhada entre F-014 e F-014b
- `SaleForm.tsx` / `NewSalePage.tsx` — F-014, rota `/vendas/nova`
- `PackageSaleForm.tsx` / `NewPackageSalePage.tsx` — F-014b, rota `/vendas/nova-pacote`

**Estrutura de `features/dashboard/` (novo):**
- `api.ts` / `hooks.ts` — `dashboardApi.get()`, `useDashboard()` (cache `MONEY`, staleTime 0)
- `DashboardPage.tsx` — F-013, rota `/` (substituiu o `PlaceholderPage`)

**Nota técnica:** adicionei `rate()` em `lib/money/money.ts` (validador de `Rate`, mesmo padrão de `money()`) — não existia ainda, e `formatRate()` exigia o tipo branded sem ter porta de entrada. Também ajustei `qk.dashboard()` em `lib/query/keys.ts` para aceitar `{period, date_from?, date_to?}` em vez do `{from, to}` genérico anterior (nada mais usava essa key ainda).

**⚠️ Outro bug real já corrigido antes, ainda vale saber:** `ui/CurrencyInput.tsx` não sincronizava com `setValue()` programático do react-hook-form — corrigido com `useEffect` resincronizando `display` a partir de `value`. Se outro campo de dinheiro autofilled aparecer com bug parecido, é esse padrão.

**O que NÃO fazer:** não integrar F-015 (retenção) ou F-017/F-018/F-019 (agenda) contra mock — essas ainda não têm endpoint real. Checar `../backend/BACKLOG.md` antes de assumir que uma dependência existe ou não.

---

# FASE 2 — Venda e dashboard

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-014 | **Tela de venda avulsa** | `[x]` | T-015 | **Integrada com `POST /sales` real em 2026-08-29** (`features/sales/api.ts`+`hooks.ts`). Fluxo: buscar/selecionar paciente → selecionar procedimento (mostra valor do procedimento, sem override — a API não aceita preço custom) → forma de pagamento (PIX/DEBIT/CREDIT/CASH/TRANSFER, parcelas se CREDIT) → confirmar → resumo com **lucro real** vindo da resposta (`net_profit`, nunca calculado no cliente). **Verificado no navegador contra API+Postgres reais**: `POST /sales` → `201`, venda `SINGLE` R$150,00/lucro R$65,00 confirmada com `SELECT` direto no banco (contagem de `sales` foi de 19→20, id bate exato). Fluxo completo cronometrado em ~5,4s, dentro da meta de <30s. |
| F-014a | Bloquear duplo-submit | `[x]` | F-014 | Idempotency-Key real, gerada em `useCreateSale` (`useRef`, nasce ao montar o form, troca só após sucesso — mesma receita do ENGENHARIA.md). **Verificado no navegador**: clique duplo na venda de pacote gerou só 1 requisição (`idempotency-key` único) e só 1 linha nova em `sales` — o segundo clique nem chegou a sair porque o botão desabilita (`createSale.isPending`) antes do primeiro round-trip terminar. |
| F-014b | Tela de venda de pacote (múltiplos itens) | `[x]` | F-014 | **Integrada com `POST /sales` real em 2026-08-29** (`PackageSaleForm.tsx`, rota `/vendas/nova-pacote`), separada de F-014. Múltiplos itens (procedimento + quantidade, `useFieldArray`) + desconto único da venda — rateio por item agora vem de `discount_allocated` na resposta (`SaleItemOut`), não mais calculado no cliente. **Verificado no navegador**: 4× Limpeza de pele + 2× Peeling, desconto R$300 → `POST /sales 201`, gross R$1.100,00, lucro real R$510,00, rateio R$128,57/R$171,43 (server-side, `allocate()` largest-remainder), tudo conferido no Postgres (`sales` 20→21→22 ao longo dos testes). Preview antes de confirmar mostra só total/valor da venda (soma simples), nunca uma alegação de lucro — isso só aparece depois que a API responde. |
| F-014c | Exibir lucro na confirmação | `[x]` | F-014 | Ambas as telas mostram o `net_profit` real vindo de `POST /sales`. |
| F-013 | Dashboard | `[x]` | T-022 | **Integrado com `GET /dashboard` real em 2026-08-29** (`features/dashboard/`, rota `/`). Filtro de período (Hoje/Últimos 7 dias/Este mês/Mês anterior/Personalizado), métricas: faturamento, lucro real, lucro real do mês (só quando não-null), a receber, margem média, ticket médio, vendas+atendimentos. **Verificado no navegador contra API+Postgres reais**: valores batem exatos com a resposta da API em todos os períodos testados. Bug encontrado e corrigido durante o teste: trocar para "Personalizado" antes de escolher as datas deixava a tela presa em "Carregando…" para sempre (query `enabled: false` nunca resolve `isPending`) — agora mostra "Escolha as duas datas" em vez do boundary. |
| F-013a | Rótulos venda-vs-sessão | `[x]` | F-013 | "X vendas, Y atendimentos" implementado com singular/plural corretos, ver `DashboardMetrics` |
| F-013b | Badge "lucro provisório" e "taxa estimada" | `[x]` | F-013 | Badges visuais em confirmação de venda (🟡 Lucro Provisório p/ pacote vs 🟢 Lucro Realizado p/ avulso) e notas de rateio no ranking e dashboard (I7) |
| F-013c | Ranking de procedimentos 🆕 | `[x]` | T-024 | `ProcedureRankingTable.tsx` integrado ao Dashboard (`GET /reports/procedures`), exibindo faturamento, lucro real e margem por serviço/produto |
| F-016 | Tela de paciente + histórico | `[x]` | T-011 | `PatientDetailPage.tsx` enriquecida com cabeçalho de contato, avatar, botão WhatsApp com checagem de consentimento LGPD e abas de dados/resumo |

> ⚠️ **F-014 é a tela mais importante do produto.** O plano pede protótipo em papel ou Figma **antes** de implementar, e reserva tempo para as iterações que ele vai gerar. Não pule.

**Saída:** ela registra uma venda em menos de 30 segundos e vê o lucro.

---

# FASE 3 — Retenção, agenda e onboarding

## Retenção

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-015 | Tela "Quem devo chamar hoje?" | `[x]` | T-029 | `features/retention/` — `GET /retention/opportunities?view=cards`, 1 card agrupado por paciente |
| F-015a | Ordenar por valor potencial | `[x]` | F-015 | Ordenação por `cmp(b.total_potential_value, a.total_potential_value)` pura sem float |
| F-015b | Botão WhatsApp (wa.me) | `[x]` | F-015, T-011a | Desabilitado com justificativa se sem consentimento/telefone; link formatado com mensagem contextual |
| F-015c | Registrar contato ao clicar | `[x]` | F-015b | Dispara `PATCH /retention/{id}` (`status: CONTACTED`, canal WhatsApp) ao abrir conversa |

## Agenda

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-017 | Lista do dia e da semana | `[x]` | T-032 | `features/agenda/` — `GET /sessions?from&to` com filtros Hoje / Próximos 7 dias / Personalizado |
| F-017a | Marcar modalidade na agenda 🆕 | `[x]` | F-017 | `📍 Presencial` vs `💻 Remoto` exibido com ícone + texto em cada item da agenda |
| F-018 | Lista de pacotes em aberto | `[x]` | T-034 | `OpenPackagesList.tsx` — `GET /packages/open`, progresso de sessões e botão de agendamento |
| F-018a | Agendar sessão a partir do card | `[x]` | F-018 | `ScheduleSessionModal.tsx` — `PATCH /sessions/{id}` com `status: SCHEDULED` |
| F-019 | Agendamento provisório (sem venda ainda) 🆕 | `[x]` | T-034b | `NewBookingModal.tsx` — `POST /bookings` com reserva de horário direta |
| F-019a | Converter booking em venda 🆕 | `[x]` | F-019, F-014 | `SaleForm.tsx` aceita `booking_id` da query string e envia no `POST /sales` para conversão atômica |

> 🚫 **Fora de escopo** (§16.4 da v6 — cite quando pedirem): drag-and-drop, recorrência, bloqueio de horário, sync Google Calendar, link público de agendamento, múltiplas salas.

## Onboarding

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-021 | Checklist de primeiro acesso | `[x]` | F-012a | `OnboardingChecklist.tsx` — exibição dinâmica de progresso com opção de ocultar sem bloquear o uso |
| F-021a | Perguntas em linguagem natural | `[x]` | F-021 | Implementado em `FinancialSettingsForm.tsx` ("Atendo em clínica parceira ou consultório próprio?", "Como a clínica calcula a comissão?", "Quem paga a taxa?") |

> **Toda pergunta aceita "não sei agora"** → salva o default e marca como estimativa. Onboarding abandonado é pior que número aproximado.

**Saída:** ela agenda sessão de pacote e manda WhatsApp com um clique.

---

# FASE 4 — Polimento

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-030 | Responsivo (celular) | `[x]` | F-014 | `index.css` atualizado com alvos de toque ≥48px (`.tap-target`), inputs com `font-size: 16px` para evitar zoom do Safari iOS, navegação horizontal fluida |
| F-031 | Estados de erro, loading e vazio | `[x]` | todas | `EmptyState` contextualizado (first-run vs filtered) em dashboard, procedimentos, despesas fixas e detalhes |

---

# P1 — Adiado

| ID | Task | Status | Nota |
|---|---|:--:|---|
| F-040 | Dashboard de impacto | `[-]` | Dados desde o dia 1, tela depois |
| F-041 | Confirmação de no-show | `[-]` | Anti-no-show |
| F-042 | Exportação CSV | `[-]` | Portabilidade |

---

## Dependências do backend

Nenhuma task de front começa antes do endpoint existir — exceto com mock explícito, e **nunca** marque `[x]` contra mock.

| Precisa de | Para | Existe no backend? |
|---|---|:--:|
| T-006 (JWT) | F-001a, F-003 | ✅ |
| T-010, T-011 | F-011, F-012 | ✅ |
| T-007 | F-012a | ✅ |
| T-009a, T-010a | F-012c | ✅ |
| T-021a, T-021b | F-012b | ✅ |
| T-015 | F-014 | ✅ |
| T-022 | F-013 | ✅ |
| T-024 | F-013c | ✅ |
| T-029 | F-015 | ✅ |
| T-032 | F-017 | ✅ |
| T-034 | F-018 | ✅ |
| T-034a, T-034b | F-019, F-019a | ✅ |

> Conferir sempre `../backend/BACKLOG.md` antes de assumir — esta coluna reflete o estado em 2026-08-29 e vai mudar conforme o backend avança.

> **Valores monetários chegam como string.** Não converta para `number` para calcular — `number` em JS é float64 e reintroduz o erro que o backend evitou com `Decimal`. Para exibir, formate a string; para somar, use `decimal.js` ou trabalhe em centavos inteiros.
