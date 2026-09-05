# Backlog — Go-Live: do MVP pronto ao primeiro uso real

**Produto:** Lumina Estética Manager · **Papel:** PO/PM · **Data:** 2026-09-04
**Branch:** `feature/mvp-release` · **Auditoria:** código e banco reais, não docs

> **O que este documento é.** O caminho mais curto entre "o produto funciona na minha
> máquina" e "uma esteticista usa isto no dia a dia dela". É um documento de **go-live**,
> não o backlog da versão completa — esse é o
> [`BACKLOG_VERSAO_COMPLETA.md`](BACKLOG_VERSAO_COMPLETA.md), que segue válido para depois.
>
> **Por que ele existe separado.** A auditoria desta data encontrou **cinco bloqueadores
> que impedem o primeiro login real** e que não estavam registrados em documento algum —
> incluindo um em que a senha do usuário é coletada pela tela e descartada silenciosamente
> pelo backend. Nenhum item do V1-V8 cobre isso, porque ninguém sabia que existia.

---

## 1. Veredito da auditoria

**O produto está pronto. O acesso ao produto não existe.**

| Camada | Estado | Evidência |
|---|---|---|
| Features do produto | ✅ **Pronto** | 257 testes passando · `tsc -b` limpo · **zero** rotas em placeholder · 20 rotas reais |
| Isolamento multi-tenant (11 tabelas) | ✅ **Sólido** | `FORCE ROW LEVEL SECURITY` confirmado em `pg_class` · `set_config` local + `RESET` no checkin do pool (`db/session.py:39-57`) |
| LGPD do paciente | ✅ **Real** | Anonimização/opt-out/portabilidade implementados e testados · consentimento enforçado no domínio (`opportunity_rules.py:145-148`), não só armazenado |
| **Autenticação** | 🔴 **Quebrada** | Senha descartada · sem cadastro · sem recuperação · Supabase nunca exercitado |
| **Guard de produção** | 🔴 **Fail-open** | `ENV` default `"development"` + segredo hardcoded + `ENV` não definido no deploy |
| **RLS das tabelas de plataforma** | 🔴 **Ausente** | `users`, `clinics`, `professionals` com `relrowsecurity=f` e GRANT total |
| Cobrança | ⚪ **Inexistente** | Zero `stripe|asaas|mercadopago` no backend |
| Observabilidade | 🔴 **Mock** | `logger.ts:2` declara-se *"Mock de telemetria / Sentry"* |

> **A ironia que a auditoria expôs:** o projeto tem disciplina de engenharia acima da média
> (invariantes testadas, RLS em três camadas, `Decimal` em todo caminho monetário, DPA que
> não mente) — e **nenhuma dessas defesas protege a porta de entrada**, que é onde o
> primeiro usuário real vai bater.

### 1.1 Correções ao que os docs afirmam

A skill `po-escopo` manda auditar antes de confiar. Auditei. Desta vez os docs erraram para
o lado **pessimista** — o inverso do histórico do projeto:

| Documento afirma | Realidade no código |
|---|---|
| `docs/README.md`: "L-3 · Nenhum Dockerfile de app, CI ou deploy" | ⚠️ **Parcial.** `backend/Dockerfile` e `backend/railway.json` **existem**. Falta CI e falta infra do frontend |
| `dev-backend/SKILL.md` citava "dívida conhecida: `query()` cru em `return_opportunity.py:82`" | ✅ **Dívida já paga** — o arquivo usa `select`/`aliased`/`_scoped()` do início ao fim. A nota já foi removida da skill nesta data |
| `docs/README.md:73` → `../BACKLOG.md` | ✅ **Corrigido nesta data.** O arquivo havia sido movido para `docs/finished/BACKLOG.md`, deixando o link quebrado |
| Nenhum documento menciona | 🔴 **A senha é descartada.** Ver B-01 |

---

## 2. Os cinco bloqueadores do primeiro login

Estes não são "melhorias". Enquanto qualquer um deles estiver aberto, **nenhuma
esteticista consegue entrar no sistema**, nem a cliente zero.

| ID | Bloqueador | Evidência | Por que bloqueia |
|---|---|---|---|
| `B-01` | 🔴 **Senha é coletada e descartada** | `SetupWizardPage.tsx:99-108` coleta com `minLength={8}` → `system.py:28` repassa → `system_service.py:29` recebe `password: str \| None` e **nunca usa**. `models/user.py:3` não tem campo de senha | O wizard mostra "Criando conta...", navega para `/login`, e a credencial **não existe**. O usuário não consegue entrar com a senha que acabou de definir |
| `B-02` | 🔴 **Nenhum cadastro público** | Os 3 caminhos exigem privilégio preexistente: `POST /system/setup` falha se `count() > 0` (`system_service.py:31`); `POST /users` exige `AdminUser`; `POST /clinics` exige super-admin | A segunda profissional só entra se alguém rodar SQL ou logar como admin. Não há self-serve |
| `B-03` | 🔴 **Supabase nunca exercitado** | `backend/.env:8` = `https://xxxxx.supabase.co` (placeholder literal) · `frontend/.env.local:2` = `changeme` · **0 dos 257 testes** cobrem o caminho JWKS (`security.py:57-86`) | O único login que funciona hoje é `/dev/login`, que **precisa morrer em produção**. O caminho real de auth nunca rodou uma vez |
| `B-04` | 🔴 **CORS ausente em produção** | `main.py:28` adiciona `CORSMiddleware` **apenas** se `ENV == "development"`. Não existe `ALLOWED_ORIGINS` em `config.py` | Front na Vercel + back no Railway = domínios diferentes = **todas** as chamadas bloqueadas pelo browser. O app não funciona |
| `B-05` | 🔴 **Sem recuperação de senha** | `LoginPage.tsx:183` — `<a href="#recuperar">`, âncora morta sem rota nem handler | Primeira senha esquecida = suporte manual no banco. Insustentável a partir da 2ª cliente |

> **B-01 é o mais grave e o menos visível.** Um erro de tela seria descoberto no primeiro
> teste. Este falha **silenciosamente e com feedback positivo**: a tela diz que deu certo.
> A causa é uma assinatura de método que aceita um parâmetro que o corpo ignora — o tipo de
> defeito que nenhum teste pega porque não há teste do fluxo de setup ponta a ponta.

---

## 3. Os três bloqueadores de segurança

Não impedem o uso — **permitem o uso indevido**. A diferença importa: podem ir para
produção sem ninguém notar, e é exatamente isso que os torna piores.

| ID | Risco | Evidência | Consequência |
|---|---|---|---|
| `S-01` | 🔴 **Fail-open: `ENV` default é `development`** | `config.py:21`: `ENV: str = "development"` · segredo com fallback hardcoded em `main.py:59` **e** `security.py:40` (`"dev-secret-estetica-local-key-superadmin-2026"`) · **`ENV` não é definido no `Dockerfile` nem no `railway.json`** | Variável esquecida no painel de deploy ⇒ app sobe em modo dev ⇒ `POST /dev/login` **público** ⇒ token de 24h para `users[0]`, que num sistema criado via setup é o **superadmin** (`system_service.py:50`). Acesso total, sem senha, a quem adivinhar a URL |
| `S-02` | 🔴 **`users`, `clinics`, `professionals` sem RLS** | `pg_class` no banco real: `relrowsecurity=f` nas três · GRANT `SELECT,INSERT,UPDATE,DELETE` para a role da app · `UserRepository` **não herda** `TenantRepository` (`repositories/user.py:9`) e `list_all()` faz `select(User)` sem escopo | As **três** camadas de defesa ausentes simultaneamente na mesma tabela — exatamente o padrão que `repositories/base.py:9` rejeita por escrito ("RLS cobre o que escapar daqui"). Contido apenas por guard de rota. `test_isolation_generic.py` cobre só `patients` e `procedures` |
| `S-03` | 🟠 **`.gitignore` não ignora `.env`** | `.gitignore` tem 10 linhas, nenhuma cobrindo `.env`/`.env.local`. Os arquivos existem no disco | Estão fora do git **por sorte**. Um `git add -A` os commita. Já rodei `git add -A` nesta sessão — passou limpo porque o `.env` estava fora do padrão dos arquivos alterados, não porque havia proteção |

> `S-01` é o único item cuja falha é **silenciosa e catastrófica**. O default seguro é
> `ENV: str = "production"` — configuração ausente deve **negar**, não conceder. E a
> proteção precisa de **teste**, não de disciplina: hoje **zero dos 42 arquivos de teste**
> exercitam `ENV=production`.

---

## 4. Concorrência — o que a pesquisa mudou

Pesquisa de 2026-09-04 sobre o mercado brasileiro, incluindo o Belasis que você citou.

### 4.1 A faixa de preço real é mais baixa do que assumimos

| Produto | Entrada (1 prof.) | % do lucro da cliente zero | Trial |
|---|---:|---:|---|
| **Agendiva Solo** | R$ 39,90 | 5,0% | 14d, sem cartão |
| **Simples Agenda** | R$ 39,90 | 5,0% | **35 dias** |
| **Iter Clinic Solo** | R$ 69,00 | 8,6% | 14d + garantia |
| **Trinks Standard** | R$ 76,00 | 9,5% | **5 dias** |
| **Avec Começando** | R$ 88,90 | 11,1% | não público |
| **Belasis Lite** | R$ 99,00 | **12,4%** | não público |
| **Belasis Pro** | R$ 189,00 | **23,6%** | não público |
| Clínica nas Nuvens | R$ 499,00 | 62% | só demo |

Fontes: [Agendiva](https://agendiva.com.br/precos) · [Simples Agenda](https://www.simplesagenda.com.br/site/precos.php) · [Iter Clinic](https://www.iterclinic.com/) · [Trinks](https://negocios.trinks.com/planos/) · [Avec](https://negocios.avec.app/avec-planos) · [Belasis](https://www.belasis.com.br/precos) · [Clínica nas Nuvens](https://clinicanasnuvens.com.br/planos-e-precos/)

🔴 **O piso real do mercado para solo é R$ 39,90, não R$ 67.** O
`BACKLOG_VERSAO_COMPLETA.md` §5 propõe Essencial R$ 67 / **âncora R$ 127** / Clínica R$ 247.
O plano-âncora de R$ 127 seria o **2º mais caro** desta tabela para uma profissional que
lucra R$ 800/mês — consumiria **15,9%** do lucro dela. O Belasis, referência que você
trouxe, está no **teto** da faixa (R$ 99), não no meio.

**Custos escondidos do mercado** (oportunidade de contraste): Belle cobra WhatsApp
**R$ 229/mês** por fora, NF-e R$ 70, app R$ 150 ([fonte](https://www.bellesoftware.com.br/precos/)).
No Trinks, lembretes automáticos e fidelidade são add-ons. Se retenção é metade da nossa
proposta de valor, **o canal de retenção não pode ser add-on**.

### 4.2 O gap está confirmado, e é exatamente o nosso eixo

| Gap do mercado | Evidência | Nosso estado |
|---|---|---|
| 🎯 **Ninguém vende "lucro real por procedimento"** | O mercado entrega fluxo de caixa ("entrou R$ 200") e chama de financeiro. Custo de insumo + fixo rateado + margem unitária existe como **planilha e post de blog** — [Clínica nas Nuvens ensina por planilha](https://clinicanasnuvens.com.br/blog/precificacao-de-servicos-de-estetica/) | ✅ **Pronto e testado.** `calculate_sale()` puro, 5 configurações provadas |
| 🎯 **Retenção é lembrete, não fila de trabalho** | Todos fazem "lembrar do agendamento de amanhã". Ninguém responde **"quem devo chamar hoje porque não voltou"** | ✅ **Pronto.** `return_opportunities` + I6 |
| **Trial curto demais** | Trinks dá **5 dias**. Com ~10 atendimentos/mês, a cliente zero não completa um ciclo de uso nisso | ⚪ A definir (recomendação: 30d) |
| **Fidelidade punitiva** | Multa de 50–80% do saldo é o item mais reclamado no [Reclame Aqui do Trinks](https://www.reclameaqui.com.br/empresa/trinks/lista-reclamacoes/) — relato de R$ 360 de multa sobre plano de R$ 72 usado 1 mês. Belasis: 16 reclamações, **18 dias** de tempo médio de resposta | ⚪ Diferenciação de custo zero: "sem fidelidade" na página de preços |
| **Produto de equipe cobrado da solo** | Comissões, multi-unidade, controle de equipe: ela paga por complexidade que não usa | ✅ Nosso escopo já é solo-first |

**Table stakes que temos:** agenda, cadastro, pacotes/sessões, WhatsApp (via `wa.me`), fluxo de caixa.
**Table stakes que faltam:** anamnese/prontuário digital, fotos antes/depois, app mobile nativo (PWA cobre).

> ⚠️ **Não corra atrás das table stakes agora.** Anamnese e fotos são dado de saúde — mudam
> o regime jurídico (V8-06/V8-07 já registram os pré-requisitos). Entrar nessa corrida
> transforma o produto em "mais um sistema de gestão", onde competimos de frente com quem
> tem 5 anos de vantagem, e **apaga o único eixo em que somos únicos**.

### 4.3 Recomendação de preço

| Plano | Preço | Racional |
|---|---:|---|
| **Solo** | **R$ 39/mês** | Empata com o piso do mercado (R$ 39,90). 4,9% do lucro da cliente zero. **1 atendimento recuperado paga 2,7 meses** |
| **Solo anual** | R$ 390/ano (R$ 32,50/mês) | 2 meses grátis. Melhora caixa e reduz churn |
| ~~Âncora R$ 127~~ | — | 🔴 **Rejeitado.** 15,9% do lucro dela; 2º mais caro do mercado |

**Por que empatar com o piso e não cobrar prêmio:** nosso escopo é mais **estreito** que o
deles (sem estoque, sem comissões, sem prontuário). Não sustentamos prêmio por escopo — só
por **profundidade** no financeiro. Prêmio de preço com escopo menor é o caminho mais curto
para o churn.

**O argumento de venda, quantificado:**

| Preço | 1 atend. recuperado (R$ 107 de lucro) paga | Promessa |
|---:|---:|---|
| R$ 39 | **2,7 meses** | "Uma paciente que voltou paga o trimestre" — forte |
| R$ 99 (Belasis) | 1,1 mês | "Paga o mês" — frágil |

> 🔴 **Consequência de código imediata:** `attribution_service.py:16` tem
> `DEFAULT_SUBSCRIPTION_FEE = Decimal("97.00")` **hardcoded**, e esse número é o divisor do
> ROI **exibido à usuária** (`attribution.py:77`). Se o preço real for R$ 39, o produto
> informa um ROI **2,5× menor que o verdadeiro** — subestimando o próprio valor, e
> violando I7 (número exibido tem de ser o número real). Ver `G-09`.

---

## 5. Épicos de go-live

Ordem = prioridade real. IDs `B-*` (bloqueador), `S-*` (segurança), `G-*` (go-live).

### G1 — Destravar o primeiro login 🔴

Sem este épico não existe produto usável. É o caminho crítico inteiro.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `B-01` | Corrigir o fluxo de senha do setup: criar o usuário no Supabase Auth com o mesmo UUID de `users.id`, ou **remover o campo de senha da tela** | `[ ]` | B-03 | 🔴 Hoje `system_service.py:29` recebe `password` e ignora. Escolha de produto embutida: se o Supabase é a fonte de verdade, a tela **não deveria pedir senha** — deveria mandar convite/magic-link. Decidir antes de codar |
| `B-03` | Provisionar projeto Supabase real e exercitar o caminho JWKS ponta a ponta | `[ ]` | — | 🔴 `.env` tem `xxxxx.supabase.co`. **0 dos 257 testes** cobrem `security.py:57-86`. O caminho de auth de produção nunca rodou |
| `B-03a` | Teste de integração do login real (não `/dev/login`) | `[ ]` | B-03 | DoD do projeto exige teste contra API real. O auth é a única área sem isso |
| `B-02` | `POST /signup` — cadastro público numa transação: `clinic` + `user` + `professional` + `financial_settings` (defaults §8.1) | `[ ]` | B-01, B-03 | Reaproveita a lógica de `system_service.setup_root`, sem o guard de `count() > 0`. **Idempotente** — duplo-submit não cria duas clínicas |
| `B-02a` | Tela de cadastro público | `[ ]` | B-02 | Mínimo de campos. Configuração fica no onboarding, não no signup |
| `B-05` | Recuperação de senha (fluxo do Supabase) | `[ ]` | B-03 | `LoginPage.tsx:183` é âncora morta hoje |
| `B-04` | `ALLOWED_ORIGINS` em `config.py` + CORS no caminho de produção | `[ ]` | — | 🔴 Sem isto, front e back em domínios diferentes = app morto no browser. Barato e invisível até o deploy |

### G2 — Fechar o fail-open 🔴

Cada item aqui é uma falha que **não aparece em teste manual** — só em incidente.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `S-01a` | `ENV: str = "production"` como default em `config.py` | `[x]` | — | ✅ **Feito 2026-09-04.** Default agora nega. Provado por `test_env_default_e_production_nao_development` (instancia `Settings(_env_file=None)` — o cenário real de deploy, sem `.env`) |
| `S-01b` | Remover os fallbacks hardcoded do `DEV_AUTH_SECRET` (`main.py`, `security.py`) — falhar ruidosamente se ausente em dev | `[x]` | — | ✅ **Feito 2026-09-04.** `_decode_dev()` levanta 500 e o boot em dev levanta `RuntimeError`. 2 testes, incluindo varredura textual provando que a string do segredo não existe mais em `app/` |
| `S-01c` | `ENV=production` explícito no `Dockerfile` e `railway.json` | `[x]` | — | ✅ **Feito 2026-09-04.** `ENV=production` no bloco `ENV` do Dockerfile. **Bônus:** removido o BOM (`efbbbf`) de `Dockerfile` **e** `railway.json` — confirmado com `xxd`, era risco de parser (o `G-02` previa isso) |
| `S-01d` | ⛔ **Teste provando que `/dev/login` e `/dev/impersonate` retornam 404 com `ENV=production`** | `[x]` | S-01a | ✅ **Feito 2026-09-04.** `tests/test_env_production_guard.py`, 7 testes. Inclui varredura do router inteiro (pega `/dev/*` novo que alguém adicione sem guard) e contraprova de que `/health` continua público — o Railway depende dele |
| `S-02a` | RLS + policy em `users`, `clinics`, `professionals` | `[ ]` | — | 🔴 `relrowsecurity=f` confirmado no banco. ⚠️ Estas tabelas são **cross-tenant por natureza** (super-admin precisa ver todas) — a policy não é a mesma das 11 de tenant. Provável: policy por `clinic_id` + role separada para plataforma. **Decidir o modelo antes de migrar** |
| `S-02b` | `UserRepository`/`ClinicRepository` com escopo de clínica | `[ ]` | S-02a | `repositories/user.py:9` não herda `TenantRepository`; `list_all()` não filtra |
| `S-02c` | Teste de isolamento cross-tenant para `users`/`clinics`/`professionals` | `[ ]` | S-02a | `test_isolation_generic.py` cobre só `patients` e `procedures` |
| `S-03` | `.env`, `.env.*` no `.gitignore` da raiz | `[x]` | — | ✅ **Feito 2026-09-04**, com correção da auditoria: `backend/.gitignore:2` e `frontend/.gitignore:27` **já protegiam** — a auditoria olhou só o da raiz e superestimou o risco. A adição na raiz é defesa em profundidade, com exceção `!.env.example` para não deixar de versionar os templates |
| `S-04` | Rate limit em `/signup`, `/login` e `/system/setup` | `[ ]` | B-02 | `rate_limit.py` **já existe e está wired** (`deps.py:54`), mas só em `/patients/import`. ⚠️ É **in-memory por processo** — documentar que só vale com 1 worker (`railway.json:8` sobe 1, funciona por acidente de config) |

### G3 — Produção mínima 🟠

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `G-01` | Host do frontend + **rewrite de SPA** | `[ ]` | B-04 | ⚠️ `router.tsx:1` usa `createBrowserRouter` (history API): **sem rewrite, F5 em `/dashboard` dá 404**. Nada no repo configura isso |
| `G-02` | Endurecer o `Dockerfile`: `USER` non-root, remover `gcc` do layer final, remover BOM da linha 1 | `[ ]` | — | Roda como root hoje. BOM (`﻿`) pode quebrar parsers estritos |
| `G-03` | CI: `pytest` + `ruff` + `tsc -b` + `lint` em PR | `[ ]` | G-04 | `.github` **não existe**. 257 testes só valem se rodarem sozinhos |
| `G-04` | Corrigir os 7 erros de `ruff` (E402) | `[x]` | — | ✅ **Feito 2026-09-04.** Imports de `main.py` movidos ao topo; `RECENT_TICKET_MONTHS` estava **no meio do bloco de imports** do `dashboard_service.py` e foi movida para depois. **O gate `pytest -q && ruff check .` agora passa limpo: 264 testes, 0 erros de lint** |
| `G-05` | CI: migration nova sem RLS falha o build | `[ ]` | G-03, S-02a | O teste existe (`test_toda_tabela_com_professional_id_tem_rls`); falta rodar sozinho. `S-02` é a prova de que revisão humana não pega |
| `G-06` | `/health` verificar o banco | `[ ]` | — | Hoje responde `ok` com Postgres caído (`main.py:40-44`) — Railway nunca reinicia nem alerta |
| `G-07` | Backup automático **com restore testado** | `[ ]` | — | 🔴 Zero referências a backup no repo. **Dado de saúde.** Exigir evidência de um restore real, não de configuração |
| `G-08` | Sentry (ou equivalente) no backend e frontend | `[ ]` | — | `logger.ts:2` declara-se *"Mock de telemetria"*; erro de produção morre no `console.error` do browser dela. Backend sem request logging |
| `G-08a` | `GlobalErrorBoundary` cobrir as rotas públicas | `[ ]` | — | `router.tsx:36-40` envolve só a árvore autenticada. `/login` e `/setup` — **as telas do primeiro contato** — dão tela branca sem recuperação |
| `G-09` | 🔴 `DEFAULT_SUBSCRIPTION_FEE` vir de configuração, não hardcoded | `[ ]` | §4.3 | `attribution_service.py:16` fixa R$ 97 e isso divide o ROI **exibido à usuária**. Com preço a R$ 39, o produto reporta ROI 2,5× menor que o real — **viola I7** |
| `G-10` | Política de Privacidade e Termos publicados + aceite registrado | `[ ]` | — | `LoginPage.tsx:230` afirma conformidade LGPD **sem documento vinculado nem aceite**. O DPA existe (`docs/LGPD_CONTRATO_OPERADOR.md`) mas é interno. A Controladora precisa aceitar formalmente |

### G4 — Prova de valor antes de cobrar 🟠

O `BACKLOG_VERSAO_COMPLETA.md` acerta ao pôr uma porta de decisão antes do billing. Esta
auditoria **reforça e corrige** essa porta.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `G-11` | 🎯 **Medir no-show evitado na atribuição** | `[ ]` | — | 🔴 **O maior alvo econômico do produto não é medido.** Auditei: `attribution_service.py` só mede receita de reativação via `return_opportunities`; **zero** referência a `NO_SHOW`. Ver §6 — no-show vale R$ 560/mês vs. R$ 280 de 1 reativação |
| `G-12` | Import gerar oportunidades de retorno retroativas | `[ ]` | — | Era `V4-07`. **É isto que dá valor no dia 1** — sem isso a fila nasce vazia e fica ~90 dias sem valor. ⚠️ Marcar `source=IMPORT`: oportunidade importada **não** conta como receita atribuível |
| `G-13` | Tabela `events` append-only + eventos de ativação | `[ ]` | — | Era `V4-01/V4-02`. Sem isto não se sabe onde a cliente nº 3 desistiu |
| `G-14` | Instrumentar time-to-value (signup → 1º lucro na tela) | `[ ]` | G-13, B-02 | Meta: **< 10 min**. Se passar, corrigir onboarding antes de qualquer feature nova |
| `G-15` | Onboarding aceitar "não sei agora" em toda pergunta | `[ ]` | — | Salva default e marca como estimativa (I7). Onboarding abandonado é pior que número aproximado |

> 🔴 **A porta de decisão, corrigida.** O `BACKLOG_VERSAO_COMPLETA.md` §4 Fase C manda medir
> "receita atribuível > mensalidade pretendida". Com `G-09` corrigido e o preço a R$ 39, a
> barra cai de R$ 97 para R$ 39/mês de receita atribuível — **um único atendimento
> recuperado por trimestre já a supera.** A porta continua válida; ela só ficou muito mais
> fácil de passar, e isso é resultado de precificar contra o mercado real em vez de contra
> uma aspiração.

### G5 — Cobrança 🟢 (só depois da porta)

Mantém-se **integralmente** o épico `V2` do
[`BACKLOG_VERSAO_COMPLETA.md`](BACKLOG_VERSAO_COMPLETA.md) (20 tasks, V2-01 a V2-20), com
duas correções desta auditoria:

| Correção | O quê |
|---|---|
| **Preço** | V2-14 usa a tabela §5 do doc antigo (R$ 67/127/247). Substituir pela §4.3 deste documento (R$ 39 solo) |
| **Fee do ROI** | `G-09` é **pré-requisito** de V2: a mensalidade tem de vir da assinatura real, não de constante |

> ⛔ **Não construa cobrança antes da porta do G4.** São 4-6 semanas de trabalho. O produto
> já tem o instrumento para medir disposição a pagar (`<ROICard />` + atribuição
> conservadora) — use-o antes de investir.

---

## 6. Onde está o dinheiro — e o que o produto não vê

Cruzamento da economia real da cliente zero ([`ENTREVISTA.md`](../../ENTREVISTA.md) Bloco 5)
com o que o código mede hoje.

**Base:** bruto ~R$ 2.100/mês · custo R$ 1.300 · **lucro R$ 800** · ~10 atendimentos ·
ticket R$ 280 · no-show ~20% · margem implícita **38%**.

| Fonte de perda | Valor/mês | O produto tem a feature? | **O produto mede?** |
|---|---:|---|---|
| **No-show** (2 atend. × R$ 280) | **R$ 560** | ✅ `GET /sessions/unconfirmed` + `<NoShowAlert />` | 🔴 **NÃO** — `attribution_service.py` não tem nenhuma referência a `NO_SHOW` |
| **Não-retorno** (1 paciente reativada) | R$ 280 | ✅ `return_opportunities` | ✅ Sim — `list_attributed`, janela 21d |

🔴 **O maior alvo econômico do produto é invisível para o próprio produto.** A feature
anti-no-show existe e funciona; a medição dela não. Consequências:

1. **A prova de valor demora mais do que precisa.** O no-show dá evidência em **semanas**
   (ela vê a paciente confirmar). A retenção dá em **meses** — o intervalo natural da
   limpeza de pele é longo, conforme a própria entrevista. Medindo só retenção, a porta do
   G4 leva um ciclo inteiro a mais para fechar.
2. **O ROI exibido subestima o produto duas vezes:** divide por R$ 97 em vez de R$ 39
   (`G-09`) **e** ignora metade da receita recuperada (`G-11`).

> Este é o mesmo padrão que o `BACKLOG_VERSAO_COMPLETA.md` §2 chamou de ironia (L-4: mede o
> ROI dela com rigor, não mede nada de si). A auditoria mostra que é pior: ele mede o ROI
> dela **incompleto**, e o número incompleto aparece na tela — o que I7 proíbe.

---

## 7. Roadmap

Premissa: dev solo, 10-15h/semana. Cada porta é literal: não avance sem passá-la.

```text
FASE 0 — Higiene barata  ✅ CONCLUÍDA em 2026-09-04
├── S-01a  ENV default = production           ✅
├── S-01b  remover fallback do segredo        ✅
├── S-01c  ENV=production no deploy + BOM     ✅
├── S-01d  teste do guard (7 testes)          ✅
├── S-03   .gitignore                         ✅ (já protegido em backend/ e frontend/)
├── G-04   7 erros de ruff                    ✅
└── docs   link ../BACKLOG.md + dívida paga   ✅
   ▸ Porta: ✅ `pytest -q && ruff check .` → 264 passed, All checks passed

FASE 1 — Primeiro login real (1-2 semanas)  🔴 caminho crítico
├── B-03 → B-03a   Supabase provisionado e TESTADO
├── B-01           decidir e corrigir o fluxo de senha
├── B-04           CORS de produção
├── S-01c → S-01d  ENV no deploy + teste do guard
└── B-05           recuperação de senha
   ▸ Porta: você faz logout, esquece a senha, recupera, e entra de novo — em produção

FASE 2 — Produção (1-2 semanas)
├── G-01  host do front + rewrite de SPA
├── G-02  Dockerfile endurecido
├── G-06  /health checando o banco
├── G-08  Sentry (back e front) + G-08a boundary nas rotas públicas
├── G-07  backup COM restore testado
└── G-03 → G-05  CI
   ▸ Porta: a cliente zero usa pelo celular, em produção, e um erro dela te notifica

FASE 3 — Cliente zero real (30-60 dias)
├── G-09  fee do ROI vem de config       ← corrige número exibido (I7)
├── G-11  medir no-show evitado          ← 🎯 o maior alvo, hoje invisível
├── G-12  import retroativo              ← valor no dia 1
├── G-13 → G-14  eventos + time-to-value
└── G-15  onboarding tolerante
   ▸ 🔴 PORTA DE DECISÃO: receita atribuível (reativação + no-show evitado) > R$ 39/mês?
      ├── NÃO → PARE. Reformule a proposta. Não construa cobrança
      └── SIM → siga

FASE 4 — Self-serve e cobrança (4-6 semanas)
├── B-02 → B-02a  signup público
├── S-04          rate limit nas rotas públicas
├── G-10          termos + política + aceite
└── V2 completo (BACKLOG_VERSAO_COMPLETA.md), com preço da §4.3
   ▸ Porta: uma colega dela assina sozinha, paga, e você não toca em nada

FASE 5+ — V5 a V8 do BACKLOG_VERSAO_COMPLETA.md
```

### Por que `B-02` (signup) está na Fase 4 e não na 1

Contra-intuitivo, mas deliberado: **a cliente zero não precisa de signup público.** A conta
dela pode ser criada manualmente, uma vez. Signup só é indispensável quando a **segunda**
profissional entra sozinha — o que só faz sentido depois de a porta da Fase 3 provar que
alguém paga. Construir self-serve antes disso é construir para uma demanda hipotética.

O que a cliente zero precisa da Fase 1 é conseguir **logar e recuperar a senha**. Nada mais.

---

## 8. Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|:--:|:--:|---|
| **`ENV` esquecido em produção** ⇒ `/dev/login` público ⇒ superadmin sem senha | **Média** | 🔴 **Fatal** | `S-01a`+`S-01c`+`S-01d`. Vazamento cross-clínica = fim do produto |
| **B-01 descoberto pela cliente zero** e não por nós | **Alta** | Alto | É o primeiro clique dela. Falha com feedback positivo ("Criando conta...") — o pior tipo |
| `users`/`clinics` sem RLS e sem escopo de repo | Média | 🔴 Alto | `S-02a-c`. Única camada de defesa hoje é guard de rota |
| **Preço a R$ 127 afasta o público real** | **Alta** | Alto | §4.3. 16% do lucro dela; 2º mais caro do mercado |
| ROI exibido menor que o real ⇒ ela não vê valor e cancela | Média | Alto | `G-09`+`G-11`. O produto se subestima em 2 dimensões |
| Backup nunca restaurado | Média | 🔴 Fatal | `G-07` exige evidência de **restore**, não de configuração |
| Perseguir table stakes (anamnese, fotos) e apagar o diferencial | Média | Alto | §4.2. Dado de saúde muda regime jurídico (V8-06/07) |
| Cliente zero é família ⇒ viés de complacência | **Certa** | Alto | Medir uso e receita atribuível, nunca satisfação declarada. Cobrar da 2ª cedo |
| Construir billing antes da porta da Fase 3 | Média | Alto | 4-6 semanas em risco |
| Dev solo esgota antes de monetizar | Média | Alto | Roadmap corta escopo, nunca prazo |

---

## 9. Definition of Done

Herdada do projeto, com uma adição que esta auditoria tornou necessária:

- [ ] Teste automatizado cobre o caminho principal
- [ ] Nenhuma invariante de [`ENGENHARIA.md`](../../ENGENHARIA.md) violada
- [ ] Se toca dinheiro: passa na matriz de 5 configurações
- [ ] Se toca dado de paciente: respeita RLS e foi testado cross-tenant
- [ ] Rodou contra a API/banco real, **não mock**
- [ ] Se toca cobrança: webhook idempotente e assinatura do provedor verificada
- [ ] 🆕 **Se toca autenticação ou o guard de `ENV`: existe teste que prova o comportamento
      em `ENV=production`.** Adicionado porque `B-01` e `S-01` passaram por toda a
      construção do MVP sem que nada os detectasse

---

## 10. Métricas de go-live

| Métrica | Meta | Como medir |
|---|---:|---|
| Signup → primeiro lucro na tela | **< 10 min** | `G-14` |
| Login real (não `/dev/login`) funciona em produção | Sim/Não | Porta da Fase 1 |
| Restore de backup testado | Sim/Não | `G-07` — evidência, não configuração |
| Receita atribuível/mês (reativação **+ no-show evitado**) | **> R$ 39** | `G-11` + `G-09` |
| Erros de produção que chegam a alguém | 100% | `G-08` |
| `pytest -q && ruff check .` limpo | Sim | `G-04` |

---

## 11. Princípio de produto (inalterado)

> Isso ajuda a profissional a **ganhar mais dinheiro**, **perder menos dinheiro**,
> **economizar tempo**, ou **reter mais pacientes**? Se não → provavelmente não pertence
> ao produto agora.

**Corolários, com o desta auditoria:**

1. Um número errado é pior que nenhum número. (I7)
2. A regra da primeira cliente não é a regra do produto.
3. Um sistema que não se mede não pode ser melhorado. (L-4)
4. 🆕 **Configuração ausente deve negar, não conceder.** Um default permissivo é uma falha
   de segurança esperando por um deploy distraído. (`S-01`)
5. 🆕 **Preço se define contra o mercado real, não contra a aspiração de receita.** A faixa
   era R$ 39–99; propusemos R$ 127 sem ter olhado.
