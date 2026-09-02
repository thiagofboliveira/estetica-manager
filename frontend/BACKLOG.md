# Backlog — Frontend (React + TypeScript + Vite)

Escopo: todas as telas, estado, integração com a API.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-09-02 · **Progresso:** 29/36 (81%, escopo MVP v7.1 original) · F-012a/F-012b/F-012c/F-013b/F-013c/F-014d/F-014e/F-030/F-031/F-015/F-015a/F-015b/F-015c/F-021a verificados/entregues e marcados `[x]` · T-017/T-022b/T-024a e T-029 (motor de retenção) entregues por sessão paralela no backend, desbloqueando várias linhas · F-016 e F-021 `[!]` bloqueadas (ver notas — ambas precisam de trabalho novo no backend) · **F-014d/F-014e são achados da revisão de produto (Fase 5+), fora do denominador 36 do MVP original — já marcados `[x]` na linha repriorizada**

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

## ✅ F-012b/F-012c verificados no navegador (2026-09-01)

Ambiente subido de novo (Postgres 5435 — 5434 estava ocupada por container de outro projeto neste host, `docker-compose.dev.yml`/`.env` atualizados; backend 8010; frontend 5173) e dirigido via Chromium headless (Playwright). Fluxo completo clicado de verdade: criar/editar ("Salvo com sucesso.")/encerrar despesa fixa, e criar procedimento com modalidade Videochamada (ícone 📹 + texto "Vídeo" na lista). Tudo confirmado com `SELECT` direto no Postgres. Dados de teste (`%teste E2E%`) removidos após a verificação. Ver notas de F-012b/F-012c na Fase 1.

---

## Painel

| Fase | Tasks | Feito |
|---|---:|---:|
| 0 — Fundação | 5 | 5 |
| 1 — Cadastros | 8 | 8 |
| 2 — Venda + Dashboard | 9 | 8 |
| 3 — Retenção + Agenda + Onboarding | 12 | 5 |
| 4 — Polimento | 2 | 2 |
| **Total** | **36** | **29** |

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
| F-011b | Campo de consentimento WhatsApp | `[x]` | F-011 | Checkbox em `PatientForm.tsx`. **Corrigido em 2026-09-02** (achado ao verificar F-015b): no fluxo de *criação*, o valor nunca persistia — `POST /patients` não aceita `consent_whatsapp` no schema do backend, só `PATCH` aceita, e `NewPatientPage.tsx` não fazia o PATCH complementar. Corrigido com um `PATCH` automático logo após o `POST` quando o checkbox vem marcado. No fluxo de *edição* (`PatientDetailPage`) sempre funcionou, porque já usa `PATCH` diretamente |
| F-011c | Feedback visual de "salvo com sucesso" 🆕 | `[x]` | F-011 | Achado no teste manual 2026-08-29: PATCH funcionava mas a tela não dava nenhum retorno, parecia travada. `PatientForm`/`ProcedureForm` ganharam mensagem "Salvo com sucesso", invalidada por `watch()` a qualquer edição |
| F-012 | Lista + form de procedimentos | `[x]` | T-010 | `features/procedures/` — CRUD completo **verificado no navegador** contra API+Postgres reais em 2026-08-29: criou "Limpeza de pele" (`POST 201`), confirmado no banco com `CurrencyInput` gravando os valores corretamente |
| F-012a | Form de configurações financeiras | `[x]` | T-007 | **Verificado no navegador contra API+Postgres reais em 2026-09-02** (Playwright headless). `features/settings/` (api/hooks/`FinancialSettingsForm`/`FinancialSettingsPage`), rota `/configuracoes/financeiro`. Linguagem natural nas duas decisões binárias (F-021a): "A taxa da máquina de cartão sai do seu bolso ou a clínica cobre?" (`fee_payer`) e "O repasse da clínica é calculado sobre o valor total ou depois de descontar a taxa do cartão?" (`split_base`) — nunca `<select>` com enum cru. Percentuais (`split_clinic_percentage`/`pix_fee_percentage`/`debit_card_fee_percentage`) chegam do backend como `MoneyOut` (string, 2 casas), não `RateOut` — criei `ui/PercentInput.tsx` (mesma máscara de dígitos do `CurrencyInput`, sufixo "%" em vez de prefixo "R$") em vez de reusar o input de moeda, que mostraria "R$" errado. Form carrega pré-preenchido com dado real (o `GET` sempre resolve — backend cria o singleton com defaults na primeira leitura, sem estado "não configurado"). Editei todos os 6 campos, "Salvo com sucesso." apareceu, `PATCH` confirmado com `SELECT` direto em `financial_settings`, e um reload da página trouxe os valores novos do `GET` — depois restaurei os valores originais via `PATCH` pra não alterar o estado do ambiente. |
| F-012b | CRUD de despesas fixas 🆕 | `[x]` | T-021b | **Verificado no navegador contra API+Postgres reais em 2026-09-01** (Playwright headless): criar despesa (nome/categoria/valor/periodicidade) confirmou `CurrencyInput` mascarando corretamente ("19999" → "199,99"), `POST` persistiu em `fixed_expenses`; editar valor mostrou "Salvo com sucesso." e `PATCH` refletiu no banco (R$199,99→R$250,00); "Encerrar despesa" setou `active_to` (soft-archive, não hard-delete) e a lista parou de exibir o item. `features/expenses/` (api/hooks/form/mapper + 3 páginas), rotas em `/configuracoes/despesas` |
| F-012c | Campo modalidade no form de procedimento 🆕 | `[x]` | T-010a | **Verificado no navegador contra API+Postgres reais em 2026-09-01** (Playwright headless): radio "Videochamada" em `ProcedureForm` selecionou `default_modality=REMOTE`, `POST /procedures` persistiu certo (confirmado com `SELECT`), e `ProceduresPage` exibiu ícone 📹 + texto "Vídeo" ao lado do procedimento remoto na lista — ícone+texto, nunca só cor, como exigido |

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

**F-012a, F-012b, F-012c, F-013c e F-030 verificados no navegador em 2026-09-01/02** (ver seções próprias) — marcados `[x]`. Fase 1 (Cadastros) está 100% completa.

**F-016 investigada e bloqueada em 2026-09-02** (ver nota na linha F-016, Fase 2): `GET /sales` (lista) não existe no backend — não é "falta o filtro `patient_id`", o endpoint de listagem em si não existe. Precisa virar task no `backend/BACKLOG.md` antes de qualquer trabalho de frontend aqui.

**F-031 auditado/corrigido e F-030 implementado em 2026-09-02** (ver seções próprias) — Fase 4 (Polimento) está 100% completa.

**🟢 T-029 mergeada e F-015/F-015a/F-015b/F-015c integradas em 2026-09-02.** Outra sessão implementou o motor de retenção completo (T-016, T-025, T-026, T-028, T-029, T-030, T-031) num branch separado (`feature/motor-retencao`) e mesclou em `fix/f012b-f012c-review-fixes` (commit `ef1daf1`) — coordenado entre as duas sessões via mensagens diretas. O contrato tinha sido levantado por leitura de código *antes* do merge (ver histórico), o que permitiu implementar `features/retention/` assim que o endpoint apareceu no branch principal, sem nova investigação. Migration `0005` trouxe a tabela `return_opportunities`; o merge também trouxe `PATCH /sessions/{id}` (rota nova, não existia antes — usada só para viabilizar o teste manual, não faz parte do escopo de F-015).

**Restam bloqueadas por endpoint inexistente:** F-017 (T-032), F-018 (T-034), F-019/F-019a (T-034a/b), F-016 (`GET /sales` lista), F-013b (T-022b), F-014d (T-017), F-014e (T-024a) — conferidas em 2026-09-02. O gate "🔴 Nada aqui começa antes de F-015..F-015c" (Fase 5+) **está satisfeito agora** — EPIC-23..27 podem começar assim que suas próprias dependências de backend (T-070+, T-080+, T-090+) existirem, nenhuma delas existe hoje.

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
| F-013b | Badge "lucro provisório" e "taxa estimada" | `[x]` | F-013, T-022b | **Integrado em 2026-09-02** assim que outra sessão entregou `has_provisional_profit` no `GET /dashboard` (T-022b). Badge amarelo "provisório" ao lado de "Lucro real" e "Lucro real do mês" quando o campo é `true`, com `title` explicando o motivo (sessão de pacote ainda não realizada no período). **Verificado no navegador contra API+Postgres reais**: criei uma venda de pacote real (3× Limpeza de pele) via `/vendas/nova-pacote`, as sessões nasceram `PENDING`, e o badge apareceu no Dashboard tanto em "Este mês" quanto em "Últimos 7 dias" (períodos que cobrem a venda) |
| F-013c | Ranking de procedimentos 🆕 | `[x]` | T-024 | **Integrado com `GET /reports/procedures` real em 2026-09-02** (`features/procedureRanking/`, rota `/relatorios/procedimentos`, link a partir do Dashboard). Tabela procedimento/faturamento/lucro/margem, já vem ordenada por faturamento do servidor. A API não expõe se uma linha depende de estimativa não confirmada (E4/E5, MVP §13) — não há campo no schema pra isso — então o aviso é fixo abaixo da tabela, não por linha. **Reffactor incluído**: filtro de período (5 botões + range custom, com o guard "escolha as duas datas" contra o bug do `AsyncBoundary`) extraído do Dashboard para `ui/PeriodFilter.tsx` + `lib/period/period.ts`, reusado nas duas telas. **Verificado no navegador contra API+Postgres reais**: criei uma venda real (Botox, R$1.000/lucro R$400) via `/vendas/nova` e conferi que apareceu na tabela com margem 40% calculada certa; troquei os 5 filtros de período, inclusive o guard de "Personalizado" sem datas. `tsc -b` limpo |
| F-016 | Tela de paciente + histórico | `[!]` | T-011 | 🔴 **Ainda bloqueada — reconfirmado em 2026-09-02 após o merge do motor de retenção.** `GET /sales` (lista) **continua não existindo** — só há `POST /sales` e `GET /sales/{id}` (por id), e o merge de `feature/motor-retencao` não trouxe esse endpoint (trouxe `GET /retention/opportunities` e `PATCH /sessions/{id}`, endpoints diferentes). Não é "falta o filtro `patient_id`", é que o endpoint de listagem em si não existe. **T-027 (`return_interval_applied` por item) mudou para `[x]`** no mesmo merge — a base de dado para "próximo retorno" agora existe de verdade (confirmei em `SaleItem.return_interval_applied` via `\d sale_items` e um teste manual criando venda real), mas isso sozinho não desbloqueia a tela: ainda falta o caminho para descobrir *quais* vendas pertencem a um paciente. `PatientOut` continua sem campo agregado, `reports.py` continua só com o ranking. **Precisa de pelo menos:** `GET /sales?patient_id=...` (lista) no backend — não registrado ainda como task própria no `backend/BACKLOG.md`. |

> ⚠️ **F-014 é a tela mais importante do produto.** O plano pede protótipo em papel ou Figma **antes** de implementar, e reserva tempo para as iterações que ele vai gerar. Não pule.

**Saída:** ela registra uma venda em menos de 30 segundos e vê o lucro.

---

# FASE 3 — Retenção, agenda e onboarding

## Retenção

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-015 | Tela "Quem devo chamar hoje?" | `[x]` | T-029 | **Integrada com `GET /retention/opportunities` real em 2026-09-02** (`features/retention/`, rota `/retornos`, substituiu o `PlaceholderPage`). T-029 foi mergeada por outra sessão em paralelo (`feature/motor-retencao` → `ef1daf1`) — contrato levantado por leitura do código antes do merge, implementação começou assim que o endpoint existiu no branch principal. **Um card por paciente** (o backend já agrupa, não precisou de lógica no cliente). **Verificado no navegador**: 58 cards reais renderizados, nenhum erro de console |
| F-015a | Ordenar por valor potencial | `[x]` | F-015 | De graça do backend — `GET /retention/opportunities` já retorna ordenado por `total_potential_value` decrescente, sem reordenar no cliente |
| F-015b | Botão WhatsApp (wa.me) | `[x]` | F-015, T-011a | Link `https://wa.me/<E.164 sem +>`. Desabilitado (substituído por mensagem) quando `can_contact=false`, sempre com `cannot_contact_reason` do backend visível ("Paciente sem telefone cadastrado" / "não deu consentimento" / "optou por não receber mensagens") — nunca só cinza sem explicação. **Verificado no navegador**: criei paciente com telefone+consentimento via UI, venda real, marquei a sessão como `COMPLETED` via `PATCH /sessions/{id}` (rota nova, trazida pelo mesmo merge) para gerar a oportunidade, cliquei em "Chamar no WhatsApp" e o popup abriu em `https://api.whatsapp.com/send/?phone=5511988887777...` — telefone batendo exato. **Bug real encontrado e corrigido nesta verificação**: `NewPatientPage.tsx` montava o payload do `POST /patients` sem `consent_whatsapp` — o backend (`PatientCreate`) nem aceita esse campo na criação, só no `PATCH`. O checkbox "Autorizou receber mensagem no WhatsApp" do form de cadastro aparecia mas nunca persistia (F-011b estava, na prática, quebrado desde que foi implementado — a nota antiga "persiste `consent_whatsapp`" era falsa para o fluxo de criação, só funcionava editando depois). Corrigido: `NewPatientPage` agora faz um `PATCH` imediato após o `POST` quando o checkbox vem marcado |
| F-015c | Registrar contato ao clicar | `[x]` | F-015b | O clique no WhatsApp dispara `PATCH /retention/opportunities/{id}` com `{status: "CONTACTED", contact_channel: "WHATSAPP"}` — `contacted_at` é setado automaticamente pelo servidor, nunca enviado pelo cliente. **Verificado no navegador**: `SELECT` no Postgres confirmou `status=CONTACTED`, `contact_channel=WHATSAPP`, `contacted_at` preenchido, após o clique real |

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
| F-021 | Checklist de primeiro acesso | `[!]` | F-012a | 🔴 **Investigado e bloqueado em 2026-09-02.** F-012a está `[x]` (desbloqueando na tabela), mas o escopo real (MVP §17, EPIC-12) é maior do que a nota sugere: 5 etapas — E1/E2 (já em `FinancialSettingsForm.tsx`) + **E4 parcelamento** (não existe no form atual, nem tem campo correspondente claro em `financial_settings`) + cadastrar 1º procedimento + cadastrar 1ª paciente —, indicador de progresso, e principalmente o mecanismo "não sei agora → salva default, marca como estimativa" **exige um campo novo no backend que não existe hoje** (`financial_settings`/`professionals` não têm nenhuma flag de estimativa/confirmação por eixo). Sem esse campo não dá pra diferenciar "ela respondeu isso" de "é só o default silencioso que o backend sempre cria" — e sem essa diferença o "badge de estimativa" fica impossível de implementar corretamente. Registrar como pendência de contrato de API (mesmo padrão do F-013b), não de UI. **Precisa de:** task de backend para persistir "é estimativa?" por campo financeiro antes de continuar aqui |
| F-021a | Perguntas em linguagem natural | `[x]` | F-021 | "A taxa sai do seu bolso ou a clínica cobre?" — **implementado dentro de F-012a** (`FinancialSettingsForm.tsx`), não como tela própria. Cobre E1 (`fee_payer`) e E2 (`split_base`); E4 (parcelamento) ainda não tem pergunta em nenhum lugar do front |

> **Toda pergunta aceita "não sei agora"** → salva o default e marca como estimativa. Onboarding abandonado é pior que número aproximado. **Sem suporte de backend ainda — ver nota do F-021.**

**Saída:** ela agenda sessão de pacote e manda WhatsApp com um clique.

---

# FASE 4 — Polimento

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-030 | Responsivo (celular) | `[x]` | F-014 | **Implementado em 2026-09-02.** O app não tinha CSS real (só o boilerplate do Vite) — criado `index.css` mobile-first: nav com scroll horizontal, formulários empilhados de coluna única (inputs com `font-size:16px` pra não disparar zoom automático do iOS), botões/radios/checkboxes com alvo de toque ≥44px, tabelas (`ranking-table`) com scroll horizontal próprio (nunca a página inteira), cards de lista em vez de tabela apertada. **Verificado com Playwright em viewport 375×812** (iPhone SE/13 mini) nas 8 telas integradas — `document.documentElement.scrollWidth === window.innerWidth` (zero overflow horizontal) em todas, confirmado também visualmente por screenshot. Sem breakpoint dedicado a desktop — só um `max-width` central pra não esticar em telas grandes, já que não existe design desktop no escopo |
| F-031 | Estados de erro, loading e vazio | `[x]` | todas | **Auditado em 2026-09-02**: a maior parte já estava correta de sessões anteriores — `PatientsPage` distingue tone `filtered` (busca sem resultado) de `first-run` (nada cadastrado), `DashboardPage` usa `has_any_data` (contrato C-2), erros já mostram a mensagem real do backend (`ApiError.message`/`body.detail`) via `AsyncBoundary`, e telas com filtro condicional (Dashboard, Ranking) já distinguem "desabilitada" de "carregando". **Gap real encontrado e corrigido**: `SaleForm`/`PackageSaleForm` mostravam só "Nenhum procedimento cadastrado." sem saída — se ela ainda não cadastrou nenhum procedimento, a tela de venda (o fluxo mais importante do produto) virava um beco sem saída. Trocado por `EmptyState` com ação "Cadastrar procedimento" linkando para `/procedimentos/novo`. Verificado sem regressão no navegador (forms continuam carregando a lista real de procedimentos normalmente) |

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
| T-029 | F-015 | ✅ (2026-09-02) |
| T-017 | F-014d | ✅ (2026-09-02) |
| T-024a | F-014e | ✅ (2026-09-02) |
| T-022b | F-013b | ✅ (2026-09-02) |
| T-032 | F-017 | ❌ |
| T-034 | F-018 | ❌ |
| T-034a, T-034b | F-019, F-019a | ❌ |
| `GET /sales` (lista, com `patient_id`) — sem task própria ainda | F-016 | ❌ (descoberto em 2026-09-02, ver nota do F-016) |
| campo de estimativa/confirmação em `financial_settings` — sem task própria ainda | F-021 | ❌ (descoberto em 2026-09-02, ver nota do F-021) |

> Conferir sempre `../backend/BACKLOG.md` antes de assumir — esta coluna reflete o estado em 2026-09-02 e vai mudar conforme o backend avança.

> **Valores monetários chegam como string.** Não converta para `number` para calcular — `number` em JS é float64 e reintroduz o erro que o backend evitou com `Decimal`. Para exibir, formate a string; para somar, use `decimal.js` ou trabalhe em centavos inteiros.

---

# FASE 5+ — Negócio 🆕 (derivado de [../REVISAO-PRODUTO.md](../REVISAO-PRODUTO.md))

> 📋 **Origem:** revisão de produto de 2026-09-01. Estas tasks **não estão no MVP v7.1** — nasceram da mudança de ambição de "validar com cliente zero" para "revender como SaaS".
>
> 🔴 **Nada aqui começa antes de F-015..F-015c (retenção) estarem `[x]`.** O dashboard financeiro é o que vende a demo; a lista de reativação é o que paga a mensalidade. Hoje só o primeiro existe.

## Correções de escopo — sobem de prioridade (já existiam)

> ⚠️ **IDs repetidos são deliberados.** As tasks desta subseção **já existem** mais acima no arquivo, na fase original. A linha de lá continua sendo a fonte do status (`[ ]`/`[x]`); a linha aqui só registra a **repriorização** e o motivo. Ao concluir, marque `[x]` **nos dois lugares** — ou mova a task para cá de vez, se preferir consolidar.


| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-030 | **Responsivo (celular)** | `[x]` | F-014 | 🔴 **A-03.** Implementado em 2026-09-02 — ver nota na linha original acima (Fase 4). Testado em viewport real 375×812 via Playwright, não só devtools |
| F-014d | Editar venda | `[x]` | T-017 | 🔴 A-02. **Implementado em 2026-09-02** assim que outra sessão entregou `PATCH /sales/{id}` (T-017). `SaleDetailPage.tsx`, rota `/vendas/:id`, link "Errou algo? Corrigir venda" nas telas de confirmação de F-014/F-014b. ⚠️ **A nota original desta linha estava errada**: dizia para "mostrar que o recálculo usa a config do momento original (I3)" — o backend faz o **oposto**: "editar" é estornar a venda (`status=REFUNDED`, campos congelados) e criar uma venda nova com **a configuração de hoje**, sem versionamento de config por data. O aviso no form reflete isso: "A correção usa a configuração financeira de hoje... se algo mudou desde então, o lucro pode sair diferente do original." **Atualização no mesmo dia**: a mesma sessão do backend, ao revisar T-017, adicionou `GET /sales/{id}/audit` (achado de revisão, não estava no escopo original). Passei a usá-lo (`useSaleAudit`) — a venda estornada agora mostra o motivo real da correção e um link "Ver venda corrigida" para a substituta, em vez de só o aviso genérico. **Verificado no navegador contra API+Postgres reais**: venda PIX/R$230 lucro corrigida para Crédito 3x → nova venda com id diferente, lucro recalculado para R$192, original virou `REFUNDED`, mostra "Motivo: ... Ver venda corrigida" linkando pra nova, tudo conferido com `SELECT` em `sales`+`sale_audit` e contra o endpoint real |
| F-013b | Badge "lucro provisório" / "taxa estimada" | `[x]` | T-022b | 🟠 A-07. Ver linha original acima (Fase 2) |
| F-014e | Erro visível em parcela fora da faixa | `[x]` | T-024a | 🔴 A-06. **Nenhuma mudança de código necessária** — `SaleForm.tsx`/`PackageSaleForm.tsx` já capturavam `ApiError.message` (que já lê `body.detail`) e bloqueavam o avanço para a tela de confirmação em qualquer erro. Só faltava o backend retornar o 422. **Verificado no navegador**: forcei 13x no crédito (fora de todas as faixas cadastradas), a mensagem real do backend apareceu em vermelho ("Nenhuma regra de taxa cobre 13x para CREDIT — cadastre uma faixa em /payment-fee-rules"), o botão voltou a "Confirmar venda" (não travou em "Confirmando…"), e `SELECT` confirmou que nenhuma venda com 13x foi persistida |
| F-031 | Estados de erro, loading e vazio | `[x]` | todas | 🟠 Auditado e corrigido em 2026-09-02 — ver nota na linha original acima (Fase 4) |

> ⚠️ **Padrão a repetir (bug real já encontrado):** toda tela com filtro que desabilita a query condicionalmente precisa distinguir "desabilitada" de "carregando", senão o `AsyncBoundary` mente e a tela fica presa em "Carregando…". Ver nota do F-013.

## EPIC-23 — Monetização e self-serve 🔴

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-050 | Tela de signup self-serve | `[ ]` | T-070 | Nome, e-mail, senha, fuso. **Mínimo de campos possível** — cada campo no signup custa conversão. Perguntas de configuração ficam no onboarding (F-021), não aqui |
| F-050a | Bloquear duplo-submit no signup | `[ ]` | F-050, T-070a | Mesma receita do F-014a (idempotency-key em `useRef`). Duplo-clique não pode criar dois tenants |
| F-051 | Tela de planos e preço | `[ ]` | T-071 | Três degraus (§6 da revisão): Essencial R$67 / **Profissional R$127 (âncora, destacado)** / Clínica R$247. Anual com 2 meses grátis |
| F-052 | Checkout / captura de pagamento | `[ ]` | T-074 | Usar o **componente hospedado do provedor** (Stripe Checkout / Asaas). ⛔ Nunca trafegar dado de cartão pelo nosso front — PCI é problema que não vale a pena ter |
| F-053 | Banner de status da assinatura | `[ ]` | T-075 | Trial: "faltam N dias". `PAST_DUE`: aviso + link de atualizar pagamento. Persistente mas **não modal** — não bloquear o trabalho dela |
| F-053a | Modo read-only (assinatura cancelada) | `[ ]` | T-075 | 🔴 Leitura e exportação continuam funcionando; só escrita bloqueia, **com o motivo visível e o caminho de reativar**. Cliente que perde o histórico não volta e reclama publicamente |
| F-054 | Tela "Minha assinatura" | `[ ]` | T-076 | Plano atual, próxima cobrança, histórico, upgrade/downgrade e **cancelamento self-serve**. Cancelamento difícil gera chargeback e reclamação, não retenção |
| F-054a | Aviso de limite do plano | `[ ]` | T-075a | "Você tem 94 de 100 pacientes ativas". Avisar **antes** de bater o teto, nunca no momento do erro |
| F-055 | Tela de indicação / cupom | `[ ]` | T-077 | Canal declarado na entrevista é boca a boca entre colegas. Link compartilhável direto no WhatsApp |

## EPIC-24 — Ativação e time-to-value 🔴

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-060 | **Importação de pacientes por CSV** | `[ ]` | T-080 | 🟢 **Melhor esforço/impacto de toda a revisão.** Upload → **preview com mapeamento de colunas** → confirmação → relatório linha a linha do que entrou e do que falhou. Nunca falhar o lote inteiro por uma linha ruim. Aceitar planilha do jeito que ela tem, não do jeito que queremos |
| F-060a | Mostrar a fila de reativação já cheia após o import | `[ ]` | F-060, T-080a, F-015 | 🔴 **É este o momento de "aha".** Depois de importar, levar direto para "Quem devo chamar hoje?" com 12 nomes na tela em vez de vazio. Sem isso o import é só cadastro |
| F-061 | Seleção do catálogo pré-carregado no onboarding | `[ ]` | T-081, F-021 | Checkboxes com procedimentos comuns + preço/custo de mercado editáveis, rotulados como estimativa (I7). Ela ajusta em vez de criar do zero |
| F-021 | Checklist de primeiro acesso | `[ ]` | F-012a | ⬆️ **Reforço da revisão:** meta explícita de **signup → primeiro lucro na tela em < 10 min**. Não bloquear o uso; toda pergunta aceita "não sei agora" → salva o default e marca como estimativa |
| F-021a | Perguntas em linguagem natural | `[ ]` | F-021 | "A taxa sai do seu bolso ou a clínica cobre?" — nunca enum, nunca jargão |

## EPIC-25 — Retenção do produto e prova de valor 🟠

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-040 | **Dashboard de impacto / ROI** | `[ ]` | T-090 | 🟠 A-04: sai de `[-]` P1 e vira **P0 comercial**. "O sistema te devolveu R$ 700 este mês; ele custa R$ 97." É o ativo anti-churn mais forte que existe — nenhum concorrente prova o próprio valor. Usar **lucro**, não faturamento (§19 do MVP) |
| F-062 | Alerta de margem negativa | `[ ]` | T-092 | Card no dashboard: "Peeling está no vermelho: R$ 12 de prejuízo por sessão". **É o insight que ela conta para as colegas** |
| F-063 | Comparativo mês vs. mês anterior | `[ ]` | T-093 | Seta e delta ao lado de cada métrica. R$ 800 é bom ou ruim? Sem contexto não vira decisão |
| F-064 | Preferências do resumo semanal | `[ ]` | T-091a | Opt-in, canal (WhatsApp/e-mail), dia da semana. Descadastro em um clique |

## EPIC-26 — Diferenciais competitivos 🟢

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-070 | **Simulador de preço** | `[ ]` | T-100 | "Se eu cobrar R$ 320 na limpeza, meu lucro vira quanto?" Slider de preço → lucro/margem ao vivo. ⚠️ Todo cálculo vem da API (T-100), **nunca** do cliente — a lição do `prototypeMath.ts` deletado |
| F-070a | Sugestão de preço mínimo | `[ ]` | T-100a | Ela informa a margem-alvo, o sistema responde o preço. Ataca o problema real: ela nunca calculou preço |
| F-071 | Aviso de no-show no histórico da paciente | `[ ]` | T-101, F-016 | "Faltou 3 de 5 vezes — considere pedir sinal". ⚠️ Tom de **apoio à decisão**, nunca de julgamento da paciente |
| F-072 | Canal de aquisição no cadastro de paciente | `[ ]` | T-102 | Um select simples no `PatientForm`. Alimenta o relatório de custo por canal |
| F-073 | Editor de templates de reativação | `[ ]` | T-103, F-015b | Preview com dado real antes de enviar. Mensagem robótica queima o canal |
| F-042 | Exportação CSV | `[ ]` | T-104 | ⬆️ Sai de `[-]` P1. LGPD Art. 18 V + tira o medo de "ficar preso no sistema" — objeção real de venda |

## EPIC-27 — Aquisição 🟠

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-080 | Landing page | `[ ]` | F-051 | Uma página: proposta de valor, 3 prints reais do produto, preço, CTA de trial. **Não existe hoje** — sem ela ninguém descobre o produto. Pode ser estática, fora do app React |
| F-080a | Prints reais do produto | `[ ]` | F-013, F-015 | Com dado plausível e **anonimizado** — nunca dado real de paciente numa página pública |

## Metas de UX desta fase

Somam-se às duas metas originais (venda avulsa < 30s, agenda não é a manchete):

| Meta | Onde | Por quê |
|---|---|---|
| **Signup → primeiro lucro na tela em < 10 min** | F-050, F-021, F-061 | Micro-SaaS morre de ativação, não de feature faltando |
| **Fila de reativação nunca nasce vazia** | F-060, F-060a | Time-to-value de 90 dias para 1 dia |
| **Funciona no celular em pé, com uma mão** | F-030 | É o meio de acesso principal, não uma adaptação |
| **Cancelar é fácil; perder o dado é impossível** | F-053a, F-054, F-042 | Cobrança agressiva gera reclamação pública, não receita |

## Sequência recomendada desta fase

```text
1. F-015..F-015c (retenção)       ← já no backlog, Fase 3. NADA daqui começa antes
2. F-030 + F-031                  ← celular e estados vazios
3. F-014d, F-013b, F-014e         ← correções que o próprio handoff reportou
4. F-060 + F-060a                 ← o momento de "aha"
5. F-040                          ← prova de valor
   ▸ PORTA: receita atribuível > mensalidade? Se não, PARE (§33 do MVP)
6. F-050..F-055, F-080            ← só depois do sinal verde
7. F-070..F-073                   ← escala
```
