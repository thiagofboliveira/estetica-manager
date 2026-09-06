# Backlog — Auditoria pós-Fase 2: o que a agenda pública mudou

**Produto:** Lumina Estética Manager · **Papel:** PO/PM · **Data:** 2026-09-05
**Branch:** `feature/mvp-release` · **Auditoria:** código, banco e gates reais, não docs
**Estado:** `A-01` fechada em 2026-09-05 · 15 tasks abertas (`A-02` a `A-16`)

> **O que este documento é.** Uma revisão de produto e arquitetura feita **depois** que o
> [`BACKLOG_GO_LIVE.md`](../pending/BACKLOG_GO_LIVE.md) declarou as Fases 0-2 concluídas. Ela encontrou
> um bloco de trabalho entregue que **nenhum documento registra** — a agenda pública — e as
> consequências disso: um gate vermelho, um gap de LGPD numa superfície nova, e uma porta de
> decisão que não pode fechar.
>
> **Por que ele existe separado.** Os épicos `G-*` continuam válidos. O que mudou não foi o
> plano, foi o **estado**: o repositório voltou a divergir do código, desta vez por omissão.
> Os itens aqui são pré-requisitos do que o go-live já planejava, não substitutos dele.

---

## 1. Veredito

**O produto está bom. O processo escorregou, e escorregou na direção do concorrente errado.**

| Gate | Resultado auditado |
|---|---|
| `pytest -q` | ✅ **294 passed** (era 286 no CI de `G-03`) |
| `npx tsc -b` | ✅ limpo, exit 0 |
| `ruff check .` | ✅ **All checks passed** — corrigido em `A-01` nesta data (eram 8 erros; `--fix` resolveu 9, um em cascata) |
| `npm run lint` | ✅ exit 0, 23 warnings, **0 erros** |
| `@oxlint/binding-win32-x64-msvc` | ✅ removido do `package.json` — `V1-03` está resolvida, e o `CLAUDE.md` ainda a registra como aberta |

Desde 2026-09-05 foram entregues 5 migrations (`0017`-`0021`), um router público
(`api/v1/public_agenda.py`), duas telas (`/agendar/:slug`, `/agendamento/:id`) e uma suíte de
teste (`test_public_agenda_integration.py`) — tudo para a **agenda pública**.

Isso é a `V8-04` do [`BACKLOG_VERSAO_COMPLETA.md`](../pending/BACKLOG_VERSAO_COMPLETA.md), cujo épico
diz *"entra quando 5+ clínicas pagando, churn < 5%"*, e que o MVP spec lista como **fora de
escopo duas vezes** (linhas 1384 e 2123: *"produto diferente, superfície pública, LGPD
própria"*).

> O padrão que o [`docs/README.md`](../README.md) alerta se inverteu de novo. Antes os docs
> mentiam por **otimismo** (bugs corrigidos listados como abertos). Depois por **pessimismo**
> (`L-3` dizia que não havia Dockerfile, e havia). Agora por **omissão**: a maior entrega da
> semana não existe em documento algum.

---

## 2. O que está bom — e por quê

Nada aqui vira task. Está registrado porque decisão boa precisa de memória tanto quanto erro.

| Área | Evidência auditada |
|---|---|
| **O eixo competitivo está pronto e é real** | `calculate_sale()` puro com 5 configurações provadas + `return_opportunities`. Nenhum dos 8 concorrentes da §4.1 do go-live vende lucro unitário — vendem fluxo de caixa e chamam de financeiro |
| **Disciplina de invariantes** | I1-I7 não são texto: `test_snapshot_immutability.py`, `test_money.py` com property tests, `test_isolation_platform.py` cobrindo cross-tenant em `users`/`clinics`/`professionals` |
| **Segurança fechada de verdade** | `S-01a-d`: o fail-open do `ENV` virou default que **nega**, com 7 testes, incluindo varredura do router inteiro para pegar `/dev/*` futuro. É a diferença entre disciplina e garantia |
| **`G-09` bem resolvido** | `attribution_service.py:43-52` lê `financial_settings.subscription_fee` do tenant; o parâmetro explícito ficou só para simulação e teste. O número exibido é o número real (I7) |
| **A pesquisa de preço** | §4.1/§4.3 do go-live é o melhor artefato do repositório. Matou o plano-âncora de R$ 127 com dado (15,9% do lucro dela) e ancorou em R$ 39 com argumento quantificado: *"uma paciente recuperada paga o trimestre"* |
| **A porta de decisão antes do billing** | Recusar 4-6 semanas de cobrança antes de provar disposição a pagar é a decisão de PO mais cara e mais correta do projeto |
| **A agenda pública, tecnicamente** | Rate limit por IP (20 bookings/h, 120 queries/h), lookup por `management_token`, `unsafe_session_without_tenant` nomeado explicitamente, suíte de integração. Não foi feita às pressas — foi feita fora do plano |

---

## 3. Os achados

| ID | Achado | Severidade | Evidência |
|---|---|:--:|---|
| `A-01` | ✅ ~~Gate `ruff` vermelho~~ **Resolvido 2026-09-05** | 🔴 | Eram 8 erros, **todos** nos arquivos da agenda pública |
| `A-02` | Agenda pública coleta dado pessoal sem base legal | 🔴 | `public_agenda.py:299-306` vs. `PublicBookingPage.tsx` sem consentimento |
| `A-03` | Agenda pública não existe em documento algum | 🔴 | `grep -rn "public_agenda" docs/` → zero |
| `A-04` | Duplo agendamento possível no link público | 🟠 | `public_agenda.py:290-297`, sem constraint no banco |
| `A-05` | A porta de decisão da Fase 3 não pode fechar | 🟠 | `G-14` depende de `B-02`, que está na Fase 4, que depende da porta da Fase 3 |
| `A-06` | Só 3 dos 7 eventos de ativação são emitidos | 🟠 | `domain/events.py` define 7; `grep EventName\.` encontra 3 |
| `A-07` | `V1-03` resolvida, `CLAUDE.md` ainda a registra como aberta | 🟢 | `package.json` sem `@oxlint/binding-win32-x64-msvc` |
| `A-08` | "Sem fidelidade" nunca virou task | 🟢 | §4.2 do go-live registra a oportunidade; nenhum backlog a executa |

### 3.1 `A-01` — o gate declarado estava vermelho ✅ resolvido

```text
alembic/versions/0017..0021_*.py         I001  Import block is un-sorted   ×5
alembic/versions/0021_populate_...py:10  F401  sqlalchemy imported but unused
app/api/v1/public_agenda.py:97           I001
app/api/v1/users.py:30                   I001
Found 8 errors.  [*] 8 fixable with the `--fix` option.
```

`G-04` fechou isso em 2026-09-04 com **0 erros**, e `G-03` configurou CI que roda
`ruff check .`. Regrediu em 4 dias, o que significa que o branch tem build vermelho. Não é o
tamanho do erro que importa — é que o mecanismo criado para impedir exatamente isso não
impediu.

### 3.2 `A-02` — o gap de LGPD que também é um gap de funil

`public_agenda.py:299-306` grava `patient_name` + `patient_phone` vindos de um formulário
público. `PublicBookingPage.tsx` não tem uma linha sobre consentimento, privacidade ou termos.

O resto do produto é rigoroso nisso: `opportunity_rules.py:145-148` **bloqueia** o WhatsApp
sem `consent_whatsapp` registrado. E é daí que vem a consequência que não é jurídica:

> 🔴 **A agenda pública alimenta o motor de retenção com leads mortos.** A paciente agenda
> pelo link → o telefone entra na base → ela vira paciente → gera oportunidade de retorno →
> e a fila "Quem chamar hoje?" mostra *"Sem consentimento de WhatsApp registrado."*
> O novo canal de aquisição abastece o pilar de retenção com contatos que o próprio produto
> se proíbe de contatar.

O formulário público é **o melhor lugar do produto inteiro** para capturar consentimento — é
o único momento em que a titular está digitando os próprios dados, por vontade própria — e é
o único que não captura. Um checkbox fecha o gap jurídico e destrava o funil ao mesmo tempo.

### 3.3 `A-05` — a dependência circular da Fase 3

O go-live §7 coloca `G-14` (time-to-value) na Fase 3, e a Fase 3 termina na **porta de
decisão** que autoriza construir cobrança. Mas `G-14` depende de `B-02` (signup público), que
foi **deliberadamente adiado para a Fase 4** — que só começa depois da porta passar.

O plano exige medir o funil de signup antes de construir o signup.

**A saída não é antecipar `B-02`** (o raciocínio do §7 "Por que `B-02` está na Fase 4"
continua correto: a cliente zero não precisa de signup). A saída é medir a coisa certa:
**primeiro login → primeiro lucro na tela**. A cliente zero não passa por signup; o número
que decide se o onboarding presta é quanto tempo ela leva do login ao valor.

### 3.4 `A-06` — a medição mede setup, não valor

`app/domain/events.py` define 7 nomes. Emitidos: `FIRST_PROCEDURE_CREATED`,
`FIRST_PATIENT_IMPORTED`, `FIRST_SALE_RECORDED`.

Faltam: `SIGNED_UP`, `FIRST_PROFIT_VIEWED`, `FIRST_REACTIVATION_SENT`,
**`FIRST_REACTIVATION_CONVERTED`**.

Os 3 instrumentados medem *configuração*. Os 4 que faltam medem *valor* — e
`FIRST_REACTIVATION_CONVERTED` é literalmente a métrica da porta de decisão. `G-13` foi
marcado `[x]` com "escopo parcial deliberado", e o efeito prático é que a infraestrutura de
medição existe e o que ela precisa medir não está sendo medido. É a lacuna `L-4` vestida de
resolvida.

---

## 4. Concorrência — três correções à análise do go-live

A §4.2 do [`BACKLOG_GO_LIVE.md`](../pending/BACKLOG_GO_LIVE.md) está correta e **não deve ser mexida** no
essencial: não persiga anamnese e fotos (dado de saúde muda o regime jurídico e apaga o único
eixo em que somos únicos). O que segue são correções à luz do estado real, não substituições.

### 4.1 A agenda pública já foi construída — capitalize, não reverta

O erro foi de **processo**, não de estratégia. Olhando a [`ENTREVISTA.md`](../../ENTREVISTA.md):

| Dado real da cliente zero | Consequência |
|---|---|
| Pacientes vêm de **Instagram e Google** | Tráfego que hoje termina em conversa manual no WhatsApp |
| Anúncio subiu de **R$ 11 → R$ 50/dia** e parou de converter | Cada real de mídia rende menos; conversão orgânica passa a valer mais |
| **35 avaliações** no Google | Já existe superfície pública com intenção de compra |
| Incidente registrado: duas pacientes queriam marcar e ela estava na rua, sem agenda | O link público resolve o incidente que gerou a entidade `bookings` |

Um link `agendar/nome-dela` na bio converte tráfego orgânico **sem gasto de mídia**, e é o
item pelo qual Trinks e Avec vendem.

**Reverter agora joga fora trabalho já pago.** O erro a não cometer é o segundo: construir e
não posicionar. Falta documento (`A-03`), falta consentimento (`A-02`), falta saber se alguém
agenda por ali (`A-06`).

### 4.2 O maior diferencial ainda não construído é o mais barato

`grep -rn "simulate" backend/app frontend/src` → **zero**. O simulador de preço
(`V6-01`/`V6-02`) não existe.

| Por que é o próximo | |
|---|---|
| **Custo** | Reusa `calculate_sale()` **puro**, sem persistir nada. Uma rota, uma tela com slider |
| **Valor percebido** | Transforma o motor de lucro de *relatório* em *ferramenta de decisão*: "Se eu cobrar R$ 320 na limpeza, meu lucro vira quanto?" |
| **Lastro na entrevista** | *"Ela nunca calculou ticket médio nem lucro antes"* |
| **Aquisição** | O canal declarado é **boca a boca entre colegas**. Um relatório não se conta numa conversa; *"esse sistema me mostrou que eu tava perdendo dinheiro no peeling"* se conta |

Mesmo raciocínio para `V5-04` (alerta de margem negativa). São os dois itens em que nenhum
concorrente compete, e o custo de construir é uma fração do que já se gastou na agenda pública.

### 4.3 O produto ensina retenção e não retém a própria usuária

`V5-01`/`V5-02` (resumo semanal) continua sem dono. Com **~10 atendimentos/mês**, ela não tem
motivo para abrir o app na maioria dos dias. É o churn que nenhuma feature de dashboard
resolve — só uma mensagem que chega até ela. É a diferença entre R$ 39/mês recorrente e
R$ 39 uma vez.

---

## 5. Épicos

Ordem = prioridade real. IDs `A-*`, sem colidir com `BACK-*`, `FRONT-*`, `TASK-BACK-S2/S3-*`,
`V1-*` a `V8-*`, `B-*`, `S-*`, `G-*`, `F*-*`.

### A1 — Fechar o que a agenda pública abriu 🔴

Nenhum destes é feature nova. São o custo não pago de uma entrega que pulou o processo.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `A-01` | `ruff check . --fix` + confirmar `pytest -q && ruff check .` limpo | `[x]` | — | ✅ **Feito 2026-09-05.** 9 erros corrigidos (I001 em `0017`-`0021`, `public_agenda.py:97`, `users.py:30`; F401 `sqlalchemy` não usado em `0021`). Evidência dos 4 gates: `ruff check .` → *All checks passed* · `pytest -q` → **294 passed** · `npx tsc -b` → exit 0 · `npm run lint` → exit 0, 0 erros. Nenhuma mudança semântica: só ordenação de imports e remoção de import morto |
| `A-02` | Checkbox de consentimento + link para `/privacidade` no formulário público, gravando `consent_whatsapp` no `booking`/`patient` | `[ ]` | — | 🔴 Hoje `public_agenda.py:299` grava nome e telefone da titular sem base legal registrada, e `opportunity_rules.py:145` depois **bloqueia** o contato. **Corrige o gap jurídico e destrava o funil de retenção na mesma linha de código** |
| `A-02a` | Teste provando que booking público sem consentimento não gera oportunidade contatável, e com consentimento gera | `[ ]` | A-02 | O DoD exige teste em rota que toca dado de paciente. Superfície pública tem de provar o comportamento, não assumir |
| `A-03` | Documentar a agenda pública: registrar `V8-04` como entregue antecipadamente no `BACKLOG_VERSAO_COMPLETA.md`, com o motivo e a data | `[ ]` | — | Sem isso o repositório mente pela terceira vez e a próxima auditoria propõe construir o que já existe. **Documentação que omite é o mesmo problema que documentação que mente** |
| `A-04` | Constraint de exclusão de horário no banco (`EXCLUDE USING gist`) ou `SELECT ... FOR UPDATE` no caminho de criação | `[ ]` | — | `public_agenda.py:290-297` checa conflito em Python e cria em seguida; `booking.py` não tem constraint. Dois cliques simultâneos passam. **O link público existe justamente para multiplicar acesso concorrente**, e o custo do erro é ela recebendo duas pacientes no mesmo horário |

### A2 — Destravar a porta de decisão 🔴

Sem este épico a Fase 3 do go-live não pode terminar, e sem ela não se decide sobre cobrança.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `A-05` | Emitir `FIRST_REACTIVATION_CONVERTED` | `[ ]` | — | 🎯 **É a métrica da porta de decisão.** Existe no catálogo `EventName` e não é emitido em lugar nenhum. A porta pergunta "receita atribuível > R$ 39/mês?" e o produto não registra o evento que responde |
| `A-06` | Emitir `FIRST_PROFIT_VIEWED` e `FIRST_REACTIVATION_SENT` | `[ ]` | — | Os 3 eventos instrumentados hoje medem *setup*. Estes medem *valor*. `G-13` está `[x]` com escopo parcial, e o efeito é `L-4` resolvida no papel |
| `A-07` | Redefinir `G-14`: cronometrar **primeiro login → primeiro lucro na tela**, não signup → lucro | `[ ]` | A-06 | 🔴 Desfaz a dependência circular: `G-14` depende de `B-02`, que está na Fase 4, que depende da porta da Fase 3. **A cliente zero não passa por signup** — o número que decide o onboarding é o do login. `SIGNED_UP` fica para quando `B-02` existir |
| `A-08` | `G-15` — onboarding aceitar "não sei agora" em toda pergunta | `[ ]` | — | Já estava aberto no go-live e auditado como não iniciado. `OnboardingChecklist.tsx` é checklist passivo, não wizard tolerante. Salva default e marca como estimativa (I7): **onboarding abandonado é pior que número aproximado** |
| `A-09` | Medir se alguém agenda pelo link público (evento + contador no dashboard da profissional) | `[ ]` | A-03 | Feature entregue sem medição é aposta, não decisão. Se o link converter, ele vira argumento de venda contra o custo de mídia que subiu 4,5×; se não converter, para de receber investimento |

### A3 — Diferencial competitivo barato 🟠

Só depois de `A1` e `A2`. Estes são os itens onde nenhum concorrente compete.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `A-10` | `V6-01`/`V6-02` — simulador de preço | `[ ]` | A1, A2 | Confirmado inexistente (`grep simulate` → zero). Reusa `calculate_sale()` puro, sem persistir. ⚠️ Todo cálculo vem da API — a lição do `prototypeMath.ts` deletado: **nunca calcular lucro no cliente** |
| `A-11` | `V5-04` — alerta de margem negativa por procedimento | `[ ]` | A-10 | *"Peeling está no vermelho: R$ 12 de prejuízo por sessão."* O canal de aquisição declarado é boca a boca; este é o insight que se conta numa conversa entre colegas |
| `A-12` | `V5-01`/`V5-02` — resumo semanal (geração + envio) | `[ ]` | A2 | Com ~10 atendimentos/mês ela não abre o app na maioria dos dias. **O produto ensina retenção e não retém a própria usuária.** Opt-in + descadastro em 1 clique, reusando a disciplina de consentimento existente |
| `A-13` | "Sem fidelidade, cancele quando quiser" na página de preços | `[ ]` | — | Diferenciação de **custo zero**: multa de 50-80% do saldo é a reclamação nº 1 do Trinks no Reclame Aqui (§4.2 do go-live). Registrado como oportunidade lá, nunca virou task de ninguém |

### A4 — Higiene documental 🟢

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `A-14` | Remover o aviso de `@oxlint/binding-win32-x64-msvc` do `CLAUDE.md` | `[ ]` | — | ✅ Auditado: já não está no `package.json`. `V1-03` está resolvida e o `CLAUDE.md` ainda a anuncia como armadilha ativa. **Aviso falso treina o leitor a ignorar avisos** |
| `A-15` | Atualizar contagem de testes nos docs: 294, não 286/264/257 | `[ ]` | — | Três números diferentes circulam em três documentos. Número desatualizado em doc de status é o começo da divergência |
| `A-16` | Adicionar ao DoD: **nenhum `[x]` novo sem ID de task existente em `docs/`** | `[ ]` | A-03 | Ver §7. É a regra que teria pego a agenda pública no primeiro commit |

---

## 6. Roadmap — o que muda no plano do go-live

O [`BACKLOG_GO_LIVE.md`](../pending/BACKLOG_GO_LIVE.md) §7 continua válido. Este documento **insere um
bloco antes da Fase 3** e corrige uma dependência dentro dela.

```text
FASE 0-2  ✅ CONCLUÍDAS (ver BACKLOG_GO_LIVE.md §7)

FASE 2.5 — Pagar o custo da agenda pública   🆕 ESTE DOCUMENTO
├── A-01   ruff limpo                        ✅ FEITO 2026-09-05
├── A-02 → A-02a  consentimento no público   ← jurídico + funil, mesma linha
├── A-03   documentar V8-04 entregue         ← para o repositório parar de mentir
└── A-04   constraint de horário             ← duplo agendamento
   ▸ Porta: `pytest -q && ruff check .` limpo (✅ já) E a agenda pública existe em docs/

FASE 3 — Cliente zero real (30-60 dias)      ⚠️ CORRIGIDA
├── G-09   ✅ já feito (fee do ROI vem de config)
├── G-11   ✅ já feito (no-show evitado medido)
├── G-12   ✅ já feito (import retroativo)
├── A-05 → A-06   eventos de VALOR           ← G-13 era parcial
├── A-07   G-14 redefinido: login → lucro    ← desfaz a circularidade com B-02
├── A-08   G-15 onboarding tolerante
└── A-09   medir o link público
   ▸ 🔴 PORTA DE DECISÃO (inalterada): receita atribuível > R$ 39/mês?
      ├── NÃO → PARE. Reformule. Não construa cobrança
      └── SIM → siga

FASE 3.5 — Diferencial barato                🆕 antes de billing, não depois
├── A-10   simulador de preço
├── A-11   alerta de margem negativa
├── A-12   resumo semanal
└── A-13   "sem fidelidade" na página de preços
   ▸ Racional: são semanas, não meses, e são o argumento de venda que
     torna a Fase 4 vendável. Construir cobrança para um produto sem
     diferencial exposto é cobrar pelo que ninguém percebeu

FASE 4 — Self-serve e cobrança (4-6 semanas)  (inalterada)
FASE 5+ — V5 a V8                             (inalterada)
```

**A única inversão relevante:** a Fase 3.5 entra **antes** da cobrança. O go-live já dizia
"não construa billing antes da porta"; esta auditoria acrescenta que também não se deve
construir billing antes de o diferencial estar **na tela**. R$ 39/mês por um relatório é caro;
R$ 39/mês por uma ferramenta que responde "quanto devo cobrar" é barato. É o mesmo código,
com posicionamento diferente.

---

## 7. O risco de processo que nenhum documento lista

O `BACKLOG_GO_LIVE.md` §8 registra *"dev solo esgota antes de monetizar"* com mitigação
*"roadmap corta escopo, nunca prazo"*. A agenda pública é a evidência de que essa mitigação
**falhou uma vez**: um épico da Fase 5+ foi executado durante a Fase 3, enquanto a porta de
decisão da Fase 3 continua sem poder fechar.

Isso não é preguiça — é o padrão normal de dev solo: **construir a feature interessante em vez
da medição chata.** Emitir `FIRST_REACTIVATION_CONVERTED` não dá tela nova; a agenda pública
dá duas.

A defesa não é disciplina. É a mesma que o projeto já aplicou ao `ENV` em `S-01d`:
**transformar a regra em teste.** Um item no DoD — *"nenhum `[x]` novo sem ID de task
existente em `docs/`"* (`A-16`) — teria pego isso no primeiro commit, do mesmo jeito que
`test_env_production_guard.py` pega um `/dev/*` novo sem guard.

---

## 8. Definition of Done

Herdada do go-live §9, com uma adição que esta auditoria tornou necessária:

- [ ] Teste automatizado cobre o caminho principal
- [ ] Nenhuma invariante de [`ENGENHARIA.md`](../../ENGENHARIA.md) violada
- [ ] Se toca dinheiro: passa na matriz de 5 configurações
- [ ] Se toca dado de paciente: respeita RLS e foi testado cross-tenant
- [ ] Rodou contra a API/banco real, **não mock**
- [ ] Se toca cobrança: webhook idempotente e assinatura do provedor verificada
- [ ] Se toca autenticação ou o guard de `ENV`: existe teste que prova o comportamento em `ENV=production`
- [ ] 🆕 **Se toca superfície pública: existe consentimento registrado e rate limit testado.**
      Adicionado porque a agenda pública nasceu com rate limit e sem base legal — metade da
      disciplina foi aplicada
- [ ] 🆕 **Nenhum `[x]` novo sem ID de task existente em `docs/`.** Adicionado porque a maior
      entrega da semana não tem ID, não tem doc, e quebrou o gate de lint sem ninguém notar

---

## 9. Métricas

| Métrica | Meta | Como medir |
|---|---:|---|
| `pytest -q && ruff check .` limpo | Sim | ✅ `A-01` — 294 passed, All checks passed (2026-09-05) |
| Booking público com consentimento registrado | 100% | `A-02a` |
| Primeiro login → primeiro lucro na tela | **< 10 min** | `A-07` (redefine `G-14`) |
| Receita atribuível/mês (reativação + no-show evitado) | **> R$ 39** | `A-05` + `G-09` ✅ + `G-11` ✅ |
| Agendamentos originados do link público | > 0 em 30 dias | `A-09` — se for 0, o link para de receber investimento |
| Features entregues sem ID de task | **0** | `A-16` |

---

## 10. Princípio de produto (inalterado)

> Isso ajuda a profissional a **ganhar mais dinheiro**, **perder menos dinheiro**,
> **economizar tempo**, ou **reter mais pacientes**? Se não → provavelmente não pertence
> ao produto agora.

**Corolários, com o desta auditoria:**

1. Um número errado é pior que nenhum número. (I7)
2. A regra da primeira cliente não é a regra do produto.
3. Um sistema que não se mede não pode ser melhorado. (`L-4`)
4. Configuração ausente deve negar, não conceder. (`S-01`)
5. Preço se define contra o mercado real, não contra a aspiração de receita.
6. 🆕 **Feature sem ID não existe.** Não porque a burocracia importe, mas porque o que não
   está registrado não é revisado, não é medido, e volta como surpresa — às vezes com um
   gate vermelho e um formulário público sem consentimento junto. (`A-16`)
