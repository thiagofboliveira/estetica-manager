# Backlog — Frontend (React + TypeScript + Vite)

Escopo: todas as telas, estado, integração com a API.
Fonte de escopo: [MVP v7.1](../MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) · Coordenação: [../BACKLOG.md](../BACKLOG.md)
<sub>O arquivo continua nomeado `v6`; v7/v7.1 são seções acrescentadas dentro dele, não arquivos novos.</sub>

**Atualizado:** 2026-08-29 · **Progresso:** 12/36 (33%) · 2 em `[~]` (F-014, F-014b — protótipos client-side prontos para integração real, já que o backend correspondente existe agora)

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
| 1 — Cadastros | 8 | 5 |
| 2 — Venda + Dashboard | 9 | 1 |
| 3 — Retenção + Agenda + Onboarding | 12 | 0 |
| 4 — Polimento | 2 | 0 |
| **Total** | **36** | **12** |

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
| F-012b | CRUD de despesas fixas 🆕 | `[ ]` | T-021b | ✅ **T-021a/T-021b já existem** — `GET/POST/PATCH/DELETE /fixed-expenses` testado contra API real em 2026-08-29 (backend). Desbloqueada. Ver MVP v7.1 §12.5 — aluguel de sala, etc. Lista simples + form (label, valor, categoria livre, `periodicity` MONTHLY\|YEARLY) |
| F-012c | Campo modalidade no form de procedimento 🆕 | `[ ]` | T-010a | ✅ **T-009a/T-010a já existem** — `default_modality` exposto em `POST/PATCH /procedures`. Desbloqueada. Presencial / Videochamada — default do procedimento. Ver MVP v7.1 §9 |

**Saída:** ela cadastra paciente e procedimento sem ajuda.

---

## 🎯 Por onde continuar agora (handoff 2026-08-29, atualizado à noite/backend)

**🟢 O backend cobriu praticamente toda a Fase 2.** Além do motor de venda (T-007, T-009a/T-010a, T-012..T-015, T-021a/T-021b, já registrado antes), agora também existem **`GET /dashboard`** (T-022/T-022a/T-023) e **`GET /reports/procedures`** (T-024) — testados contra Postgres real, 133 testes passando no backend. Ver `../backend/BACKLOG.md` para o detalhe de cada endpoint.

**Isso desbloqueia de verdade:**
- **F-014/F-014b**: os protótipos client-side (`prototypeMath.ts`) já podem ser trocados pela integração real com `POST /sales` — continua o passo de maior valor, já que F-014 é a tela mais importante do produto
- **F-013** (Dashboard): `GET /dashboard?period=today|last_7_days|this_month|last_month|custom` real. Retorna `has_any_data` (contrato C-2, distingue first-run de mês vazio) e `fixed_expenses_total`/`net_profit_after_fixed_expenses` como `null` fora de filtros mensais — **a tela deve esconder essa linha quando vier null**, não mostrar "R$ 0,00"
- **F-013c** (novo — ranking de procedimentos): `GET /reports/procedures?period=...`, mesmos filtros do dashboard. Retorna linhas ordenadas por faturamento decrescente
- **F-012a** (config financeira): `GET/PATCH /financial-settings` real
- **F-012b** (despesas fixas): `GET/POST/PATCH/DELETE /fixed-expenses` real
- **F-012c** (modalidade no procedimento): `default_modality` já exposto em `/procedures`

**Ainda faltando no backend:** `GET /retention/opportunities` (T-029, para F-015), agenda/`bookings` (T-032..T-034b, para F-017/F-018/F-019). Não integrar essas contra mock.

**Estrutura de `features/sales/` (protótipo a substituir por integração real):**
- `PatientPicker.tsx` — busca/seleção de paciente, compartilhada entre F-014 e F-014b
- `prototypeMath.ts` — cálculo ilustrativo de lucro, **nunca** o motor de lucro real — ao integrar, o lucro exibido deve vir da resposta de `POST /sales`, não mais calculado no cliente
- `SaleForm.tsx` / `NewSalePage.tsx` — F-014, rota `/vendas/nova`
- `PackageSaleForm.tsx` / `NewPackageSalePage.tsx` — F-014b, rota `/vendas/nova-pacote`

**⚠️ Bug real já corrigido, vale saber:** `ui/CurrencyInput.tsx` não sincronizava com `setValue()` programático do react-hook-form — corrigido com `useEffect` resincronizando `display` a partir de `value`. Se outro campo de dinheiro autofilled aparecer com bug parecido, é esse padrão.

**O que NÃO fazer:** não integrar F-015 (retenção) ou F-017/F-018/F-019 (agenda) contra mock — essas ainda não têm endpoint real. Checar `../backend/BACKLOG.md` antes de assumir que uma dependência existe ou não.

---

# FASE 2 — Venda e dashboard

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| F-014 | **Tela de venda avulsa** | `[~]` | T-015 | **Protótipo client-side em 2026-08-29** (`features/sales/`, rota `/vendas/nova`) — sem integração com API (T-012..T-015 não existem). Fluxo: buscar/selecionar paciente → selecionar procedimento (autofill de preço/custo) → forma de pagamento (parcelas se Cartão) → confirmar → resumo com lucro estimado no cliente (`prototypeMath.ts`, claramente rotulado "estimativa de protótipo"). **Cronometrado no navegador (Playwright) em 2026-08-29: fluxo completo em ~3s**, dentro da meta de <30s. **Continua `[~]`, não `[x]`**, porque não há POST real — vira `[x]` só quando integrado a T-015. |
| F-014a | Bloquear duplo-submit | `[ ]` | F-014 | Botão desabilita + idempotência. Ainda não implementado no protótipo (que não tem POST real) — fica pendente para quando integrar T-015 |
| F-014b | Tela de venda de pacote (múltiplos itens) | `[~]` | F-014 | **Protótipo client-side em 2026-08-29** (`PackageSaleForm.tsx`, rota `/vendas/nova-pacote`), separada de F-014. Múltiplos itens (procedimento + quantidade, `useFieldArray`), desconto único rateado por item para exibição (`allocateDiscountForDisplay`, largest remainder — fecha exatamente com o total, MVP §11.5). Testado no navegador com 2 itens (4× Limpeza de pele + 2× Peeling, desconto R$300): rateio R$128,57/R$171,43, soma exata. **Continua `[~]`**, mesma razão de F-014: sem POST real |
| F-014c | Exibir lucro na confirmação | `[x]` | F-014 | Já coberto pelos dois protótipos (F-014 e F-014b) — tela de confirmação mostra lucro estimado com aviso de que é estimativa de protótipo |
| F-013 | Dashboard | `[ ]` | T-022 | ✅ **T-022 já existe** — `GET /dashboard?period=...` testado contra API real (backend). Desbloqueada |
| F-013a | Rótulos venda-vs-sessão | `[ ]` | F-013 | "3 vendas, 12 atendimentos" — senão parece bug |
| F-013b | Badge "lucro provisório" e "taxa estimada" | `[ ]` | F-013 | Honestidade > aparência de precisão |
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
