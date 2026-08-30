# Backlog — Frontend (React + TypeScript + Vite)

Escopo: todas as telas, estado, integração com a API.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-08-29 · **Progresso:** 17/36 (47%, +2 em `[~]` não contam ainda) · F-012b/F-012c com código pronto, aguardando verificação em navegador

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

## 🧪 Ambiente deixado no ar (handoff 2026-08-29) — só falta clicar

Postgres, backend e frontend estão **rodando agora mesmo** neste sandbox, com F-012b e F-012c já implementados esperando o teste manual:

- Postgres 16 local, banco `estetica`, migrations `0001`→`0004` aplicadas, seed do profissional dev (`00000000-0000-0000-0000-000000000001`) inserido
- Backend: `http://localhost:8010` (`.venv` já com todas as deps + `email-validator`, que faltava no `pyproject.toml` — considerar adicionar lá)
- Frontend: `http://localhost:5173`, `.env.local` com `VITE_DEV_AUTH=true` apontando pro backend acima

**Falta só:** abrir `http://localhost:5173`, entrar como "Cliente Zero (dev)", ir em Procedimentos → criar um com modalidade Videochamada (F-012c), e em Configurações → Despesas fixas → criar/editar/encerrar uma despesa (F-012b). Se bater o esperado, marcar `[x]` nas duas linhas do painel abaixo.

**Por que não fiz esse clique eu mesma:** este ambiente de execução não tem navegador; tentei instalar o Chromium do Playwright para simular, mas o download é bloqueado pela allowlist de rede daqui (`cdn.playwright.dev`). Tudo que dava pra validar sem navegador — API real, Postgres real, `tsc -b`, `vite build` — está feito (ver notas de F-012b/F-012c na Fase 1).

---

## Painel

| Fase | Tasks | Feito |
|---|---:|---:|
| 0 — Fundação | 5 | 5 |
| 1 — Cadastros | 8 | 5 |
| 2 — Venda + Dashboard | 9 | 6 |
| 3 — Retenção + Agenda + Onboarding | 12 | 0 |
| 4 — Polimento | 2 | 0 |
| **Total** | **36** | **17** |

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
| F-001 | Setup Vite + TS + React Query + roteamento | `[x]` | — | React 19 + Vite 8 + TS 6. `tsc -b` e `vite build` passando |
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
| F-012a | Form de configurações financeiras | `[ ]` | T-007 | ✅ **T-007 já existe** — `GET/PATCH /financial-settings` testado contra API real (backend). Desbloqueada. Ver F-021 para a linguagem |
| F-012b | CRUD de despesas fixas 🆕 | `[~]` | T-021b | **Código completo, verificado contra API+Postgres reais via curl (2026-08-29), falta clique no navegador.** `features/expenses/` (api/hooks/form/mapper + 3 páginas), rotas em `/configuracoes/despesas`. `POST`/`PATCH`/`DELETE` testados um a um contra o backend real na porta 8010 com Postgres local: criar, editar valor, arquivar (`active_to`, não hard-delete) — todos confirmados com `SELECT` direto em `fixed_expenses`. Confirmei também que arquivar reflete em `GET /dashboard` (`fixed_expenses_total` foi a zero), o que valida a invalidação de `qk.financial()` inteiro nas mutations. **Não marcar `[x]`:** não houve teste de clique real no formulário (máscara do `CurrencyInput`, mensagem "Salvo com sucesso", refetch automático da lista) — sandbox sem navegador disponível, Playwright não pôde baixar o Chromium (rede bloqueada). `tsc -b`/`vite build` passam limpos |
| F-012c | Campo modalidade no form de procedimento 🆕 | `[~]` | T-010a | **Código completo, verificado contra API real via curl, falta clique no navegador.** `default_modality` (Presencial/Videochamada) adicionado a `Procedure`, `ProcedureForm` (radio) e `ProceduresPage` (ícone 📹 na lista quando remoto). `POST /procedures` com `default_modality: REMOTE` testado contra Postgres real, persistiu certo. Mesma ressalva do F-012b: falta clicar no radio de verdade e ver o form salvar |

**Saída:** ela cadastra paciente e procedimento sem ajuda.

---

## 🎯 Por onde continuar agora (handoff 2026-08-29, atualizado após integração real de F-014/F-014b/F-013)

**🟢 F-014/F-014a/F-014b/F-014c/F-013/F-013a estão integrados de verdade contra a API real e marcados `[x]`.** Venda (avulsa e pacote) contra `POST /sales` (T-015), dashboard contra `GET /dashboard` (T-022). `prototypeMath.ts` foi deletado — nenhum lucro é mais calculado no cliente.

**Verificado no navegador contra Postgres real:**
- Venda avulsa (`SINGLE`, R$150/lucro R$65) e venda de pacote (`PACKAGE`, 2 itens + desconto, R$1.100/lucro R$510), ambas persistidas e conferidas com `SELECT` direto na tabela `sales`
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
| F-013b | Badge "lucro provisório" e "taxa estimada" | `[ ]` | F-013 | **Ainda não dá para implementar direito**: `GET /dashboard` retorna só o agregado do período, sem indicar se alguma venda por trás tem sessões pendentes (pacote ainda não totalmente realizado, MVP §12.1) — precisaria de um campo novo do backend (ex: `has_provisional_profit`) ou de buscar vendas individualmente, o que foge do escopo de um endpoint agregado. Registrar como pendência de contrato de API, não de UI |
| F-013c | Ranking de procedimentos 🆕 | `[ ]` | T-024 | ✅ **T-024 já existe** — `GET /reports/procedures?period=...` testado contra API real. Tabela: procedimento / faturamento / lucro / margem, ordenado por faturamento. ⚠️ Rotular como estimativa se E4/E5 não confirmados pela profissional (MVP §13, TASK-024) |
| F-016 | Tela de paciente + histórico | `[ ]` | T-011 | Total gasto, próximo retorno |

> ⚠️ **F-014 é a tela mais importante do produto.** O plano pede protótipo em papel ou Figma **antes** de implementar, e reserva tempo para as iterações que ele vai gerar. Não pule.

**Saída:** ela registra uma venda em menos de 30 segundos e vê o lucro.

---

# FASE 3 — Retenção, agenda e onboarding

## Retenção

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-015 | Tela "Quem devo chamar hoje?" | `[ ]` | T-029 | **Um card por paciente**, não por oportunidade |
| F-015a | Ordenar por valor potencial | `[ ]` | F-015 | Tempo dela é limitado |
| F-015b | Botão WhatsApp (wa.me) | `[ ]` | F-015, T-011a | Desabilitado sem telefone/consentimento, **com motivo visível** |
| F-015c | Registrar contato ao clicar | `[ ]` | F-015b | |

## Agenda

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-017 | Lista do dia e da semana | `[ ]` | T-032 | Lista, **não** grade de calendário. Mescla sessões + `bookings` (F-019) num único calendário — ver MVP v7.1 §16.6 |
| F-017a | Marcar modalidade na agenda 🆕 | `[ ]` | F-017 | Presencial vs. remoto distinguível de relance — **ícone + texto, nunca só cor**. Responde "onde eu preciso estar" |
| F-018 | Lista de pacotes em aberto | `[ ]` | T-034 | Porta de entrada do agendamento |
| F-018a | Agendar sessão a partir do card | `[ ]` | F-018 | `PENDING → SCHEDULED` sem sair da tela |
| F-019 | Agendamento provisório (sem venda ainda) 🆕 | `[ ]` | T-034b | Ver horários ocupados + reservar horário direto, mesmo para contato novo sem cadastro. Motivado por incidente real (ENTREVISTA.md) |
| F-019a | Converter booking em venda 🆕 | `[ ]` | F-019, F-014 | `POST /sales` com `booking_id` — sem passo manual separado |

> 🚫 **Fora de escopo** (§16.4 da v6 — cite quando pedirem): drag-and-drop, recorrência, bloqueio de horário, sync Google Calendar, link público de agendamento, múltiplas salas.

## Onboarding

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-021 | Checklist de primeiro acesso | `[ ]` | F-012a | Não bloquear o uso |
| F-021a | Perguntas em linguagem natural | `[ ]` | F-021 | "A taxa sai do seu bolso ou a clínica cobre?" — nunca enum |

> **Toda pergunta aceita "não sei agora"** → salva o default e marca como estimativa. Onboarding abandonado é pior que número aproximado.

**Saída:** ela agenda sessão de pacote e manda WhatsApp com um clique.

---

# FASE 4 — Polimento

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-030 | Responsivo (celular) | `[ ]` | F-014 | Ela trabalha em pé, com o celular |
| F-031 | Estados de erro, loading e vazio | `[ ]` | todas | Primeira sessão é toda tela vazia |

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
| T-007 | F-012a | ✅ (2026-08-29) |
| T-009a, T-010a | F-012c | ✅ (2026-08-29) |
| T-021a, T-021b | F-012b | ✅ (2026-08-29) |
| T-015 | F-014 | ✅ (2026-08-29 — T-012..T-015 completos, ver `../backend/BACKLOG.md`) |
| T-022 | F-013 | ✅ (2026-08-29) |
| T-024 | F-013c | ✅ (2026-08-29) |
| T-029 | F-015 | ❌ |
| T-032 | F-017 | ❌ |
| T-034 | F-018 | ❌ |
| T-034a, T-034b | F-019, F-019a | ❌ |

> Conferir sempre `../backend/BACKLOG.md` antes de assumir — esta coluna reflete o estado em 2026-08-29 e vai mudar conforme o backend avança.

> **Valores monetários chegam como string.** Não converta para `number` para calcular — `number` em JS é float64 e reintroduz o erro que o backend evitou com `Decimal`. Para exibir, formate a string; para somar, use `decimal.js` ou trabalhe em centavos inteiros.
