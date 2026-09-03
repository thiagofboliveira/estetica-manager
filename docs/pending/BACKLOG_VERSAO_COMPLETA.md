# Backlog — Versão Completa do Sistema

**Produto:** Lumina Estética Manager · **Papel:** PO/PM · **Data:** 2026-09-03
**Branch de referência:** `feature/mvp-release` · **Estado auditado:** 173 testes backend, 9 migrations, 24 rotas de frontend

> **O que este documento é.** O backlog da **versão completa** — do estado atual até um SaaS vendável e operável em escala. Não é o backlog do MVP (esse está entregue). É o mapa do que falta para o produto virar negócio.
>
> **O que este documento não é.** Não é lista de desejos. Cada item passou pelo filtro da §32 do MVP: *ganhar mais dinheiro, perder menos, economizar tempo, ou reter mais pacientes.* O que não passou está na §9 (fora de escopo), com o motivo.

---

## 1. Estado atual — o que já está pronto

Auditoria direta do código em 2026-09-03, não cópia dos docs antigos (que estão defasados).

### Entregue e testado

| Módulo | Backend | Frontend | Evidência |
|---|---|---|---|
| **Fundação financeira** | `Decimal`/`NUMERIC(12,2)`, `allocate()` largest-remainder, `TIMESTAMPTZ` UTC | `Money` branded + `decimal.js` | `test_money.py`, property tests |
| **Motor de lucro** | `calculate_sale()` puro, 5 configurações provadas | — | `test_sale_calculator.py` |
| **Snapshot congelado (I3)** | `FROZEN_FIELDS` + listener `before_flush` | — | `test_snapshot_immutability.py` |
| **Multi-tenancy + RLS** | Role `NOBYPASSRLS`, `FORCE RLS`, repo exige tenant | — | `test_isolation_generic.py` |
| **Venda / Item / Sessão** | `POST /sales` avulsa + pacote, idempotência | 2 telas separadas (avulso < 30s) | `test_sales_integration.py` |
| **Correção de venda** | `PATCH /sales/{id}` + `sale_audit` | Tela de edição + histórico | — |
| **Cancelamento/estorno** | — | — | `test_sale_cancel_refund.py` |
| **Dashboard financeiro** | `GET /dashboard`, `has_any_data`, `has_provisional_profit` | Filtros de período, badges de estimativa | `test_dashboard*.py` |
| **Despesas fixas** | CRUD, `MONTHLY\|YEARLY` ratado | Tela em Configurações | `test_fixed_expenses_integration.py` |
| **Ranking de procedimentos** | `GET /reports/procedures` | Tabela ordenada | `test_procedure_ranking.py` |
| **Ponto de equilíbrio** | Motor de breakeven | — | `test_breakeven*.py` |
| **Motor de retenção** | `return_opportunities`, 2 eixos, supressão 14d | "Quem chamar hoje?" agrupado por paciente | `test_retention_*.py` (3 suítes) |
| **Agenda + bookings** | `GET /sessions`, `PATCH` agendar, `/bookings`, conversão em venda | Grade visual + lista, reserva provisória, Modo Ocupado | `test_booking_rules.py`, `test_agenda_settings_integration.py` |
| **Horários livres** | Motor de slots livres + mensagem | — | `test_free_slots*.py` (3 suítes) |
| **Anti-no-show** | `GET /sessions/unconfirmed`, confirmação | `<NoShowAlert />` com 1-tap WhatsApp | `test_no_show.py` |
| **ROI / atribuição** | `attribution.py` conservadora (janela 21d) | `<ROICard />` | `test_attribution.py` |
| **Importação de pacientes** | `POST /patients/import` atômico | Tela com preview | `test_patient_import.py` |
| **Templates de procedimento** | Catálogo de mercado | `<ProcedureTemplateSelector />` | `test_procedure_templates.py` |
| **Split por procedimento (E6)** | `procedures.split_override` | Campo no form | `test_procedure_split_override.py` |
| **Antecipação (E7)** | `anticipates_all`, D+2, congelado no snapshot | Config | `test_anticipation.py` |
| **Projeção de recebíveis** | `GET /dashboard/receivables` | — | `test_receivables.py` |
| **Exportação CSV** | 3 endpoints, `;` + UTF-8 BOM | Download direto | `test_export.py` |
| **LGPD (parcial)** | Consentimento, opt-out, anonimização | Gate de consentimento no WhatsApp | `test_patient_lgpd.py` |
| **Multi-tenant SaaS** | `clinics`, RBAC, super-admin global | Painéis Admin + Super Admin, Setup Wizard | `test_super_admin*.py` |
| **Landing page** | — | Landing + "Como calculamos" | — |
| **PWA** | — | `vite-plugin-pwa`, ícones, SW | — |

### Correções de doc pendentes (achado desta auditoria)

Os arquivos `bugs.md` (raiz, backend, frontend) listam bugs **já corrigidos** no código:

| Bug documentado | Estado real |
|---|---|
| `BUG-BACK-S2-02` telefone em bookings | ✅ Corrigido — `session_service.py` já lê `b.patient.phone` |
| `BUG-FRONT-S2-05` separador `;` no import | ✅ Corrigido — `line.split(/[\t,;]/)` |
| `BUG-FRONT-S3-01` PWA crypto Node 18 | ✅ Corrigido — polyfill presente |
| `BUG-FRONT-S2-03` prefixo `/api/v1` duplo | ✅ Corrigido |
| `BUG-FRONT-S2-02` fuso no NoShowAlert | ✅ Corrigido |

> 🔴 **T-000 (abaixo) é consolidar esses três `bugs.md` em um só, com o estado real.** Documentação que mente é pior que documentação ausente: da próxima vez ninguém vai saber o que é real.

---

## 2. As quatro lacunas que separam "sistema pronto" de "SaaS vendável"

O produto **funciona**. O negócio **não existe ainda**. Esta é a distância:

| # | Lacuna | Evidência | Bloqueia |
|---|---|---|---|
| **L-1** | 🔴 **Não sabe cobrar** | Zero ocorrências de `subscription`/`billing`/`stripe`/`asaas` no backend. `clinics.plan` é uma string livre (`"standard"`) sem nenhuma lógica atrás | Receber dinheiro de qualquer cliente |
| **L-2** | 🔴 **Não tem cadastro público** | `POST /system/setup` só funciona com **zero** usuários no sistema. `POST /users` exige admin logado. Não há signup | A segunda clínica entrar sem você rodar SQL |
| **L-3** | 🟠 **Não tem produção** | Nenhum Dockerfile de app, CI, ou config de deploy. Roda só em localhost | Qualquer cliente real usar |
| **L-4** | 🟠 **Não se mede** | Nenhuma tabela de eventos. Não há funil, nem cohort, nem noção de time-to-value | Saber por que a cliente nº 3 desistiu |

> **A ironia registrada:** o produto já mede o ROI *da profissional* (`<ROICard />`, atribuição conservadora, janela de 21 dias) com rigor maior do que muitos SaaS medem o próprio. Mas não mede **nada** sobre si mesmo. L-4 corrige essa assimetria.

---

## 3. Épicos da versão completa

Ordem = prioridade. IDs novos, sem colidir com os existentes (`BACK-*`, `FRONT-*`, `TASK-BACK-S2/S3-*`).

### V1 — Higiene e verdade documental 🔴

Barato, rápido, e destrava a confiança em tudo o mais.

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V1-01` | Consolidar `bugs.md` (raiz + backend + frontend) em **um** arquivo com estado real | docs | Os 5 bugs listados já estão corrigidos. Manter histórico, marcar resolvido |
| `V1-02` | Consolidar `BACKLOG_SPRINT2/SPRINT3/V2` no `BACKLOG.md` | docs | 6 arquivos de backlog é backlog nenhum |
| `V1-03` | Remover `@oxlint/binding-win32-x64-msvc` do `package.json` | frontend | 🔴 **Quebra `npm install` em Linux/Mac** (`EBADPLATFORM`). O `oxlint` resolve o binário nativo sozinho. Impede onboarding de qualquer dev não-Windows |
| `V1-04` | Alinhar porta do Postgres entre `docker-compose.dev.yml` (5434) e `.env.example` | infra | Achado ao subir o ambiente: `.env` apontava 5435 |
| `V1-05` | Script de bootstrap de ambiente local (`make dev` ou `scripts/dev.sh`) | infra | Hoje exige: compose up → `alembic upgrade` → `ALTER ROLE` senha → seed de clinic+user+professional via SQL manual. Documentar ou automatizar |
| `V1-06` | Seed de dev idempotente (clinic + admin + professional) | backend | Substitui o SQL manual do V1-05 |
| `V1-07` | `ENGENHARIA.md` — atualizar com as invariantes novas | docs | I3 ganhou `snapshot_payload`; I8 (antecipação congelada) merece entrada própria |

### V2 — Monetização e self-serve 🔴 (L-1, L-2)

Sem isto, não há negócio. É o épico mais caro e o mais inevitável.

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V2-01` | ⛔ **Decidir provedor de pagamento** | produto | Stripe (recorrência madura, Pix+cartão, webhook confiável) vs Asaas (mais barato em Pix/boleto BR). **Decisão antes de codar.** Registrar o motivo |
| `V2-02` | Tabela `plans` (`code`, `price_amount NUMERIC(12,2)`, limites, `features` JSONB) | backend | I1 vale aqui também — preço é dinheiro |
| `V2-03` | Tabela `subscriptions` (`clinic_id`, `plan_id`, `status`, `trial_ends_at`, `current_period_end`, `provider_*_id`) | backend | Vincular a `clinic`, não a `professional` — o tenant de cobrança é a clínica |
| `V2-04` | Máquina de estados da assinatura | backend | `TRIALING\|ACTIVE\|PAST_DUE\|CANCELED\|EXPIRED`. Mesmo padrão de `session_state_machine.py` |
| `V2-05` | `POST /signup` — cadastro público de clínica | backend | Numa transação: `clinic` + `user` admin + `professional` + `financial_settings` (defaults §8.1) + `subscription` TRIALING. **Hoje isso é impossível sem SQL manual** |
| `V2-06` | Idempotência do signup | backend | Duplo-submit não pode criar duas clínicas |
| `V2-07` | Integração de cobrança recorrente | backend | Nunca construir cobrança na mão. Valores em `Decimal`, mesmo vindos do SDK |
| `V2-08` | `POST /webhooks/billing` idempotente | backend | Verificar **assinatura** do provedor. Guardar `provider_event_id`, ignorar repetido |
| `V2-09` | Job de expiração de trial | backend | Roda no fuso da clínica (I4). **Alertar se o job falhar** |
| `V2-10` | Middleware de gate por status | backend | `TRIALING\|ACTIVE` libera · `PAST_DUE` libera + aviso · `CANCELED\|EXPIRED` **read-only** (402 na escrita) |
| `V2-11` | Enforcement de limite de plano | backend | Contar pacientes **ativas**. ⚠️ **Nunca limitar registro de venda** — limitar a venda destrói o dado que gera o ROI que justifica a assinatura |
| `V2-12` | `GET/PATCH /subscription` | backend | Estado, plano, dias de trial, próxima cobrança, upgrade/downgrade, cancelamento |
| `V2-13` | Tela de cadastro público | frontend | Mínimo de campos. Configuração fica no onboarding, não no signup |
| `V2-14` | Tela de planos e preço | frontend | 3 degraus (§5). Destacar o plano-âncora |
| `V2-15` | Checkout | frontend | ⛔ Componente **hospedado** do provedor. Nunca trafegar cartão pelo nosso front — PCI é problema que não vale ter |
| `V2-16` | Banner de status da assinatura | frontend | Trial: "faltam N dias". `PAST_DUE`: aviso + link. Persistente, **não modal** |
| `V2-17` | Modo read-only (cancelado) | frontend | 🔴 Leitura e **exportação** continuam. Só escrita bloqueia, com motivo e caminho de reativar |
| `V2-18` | Tela "Minha assinatura" | frontend | Cancelamento self-serve. Cancelamento difícil gera chargeback, não retenção |
| `V2-19` | Aviso de limite de plano | frontend | Avisar **antes** do teto, não no erro |
| `V2-20` | Indicação / cupom | ambos | O canal declarado na entrevista é **boca a boca entre colegas**. É o CAC mais barato que existe |

> 🔴 **Regra de produto que vira regra de código:** cliente cancelado **nunca** perde acesso de leitura nem exportação. Além de correto comercialmente, a LGPD Art. 18 V exige portabilidade independente de status de pagamento.

### V3 — Produção e confiabilidade 🔴 (L-3)

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V3-01` | `Dockerfile` de produção (backend) | infra | Multi-stage, non-root, sem `.venv` do host |
| `V3-02` | Build de produção do frontend + host estático | infra | PWA já gera `sw.js`; falta onde servir |
| `V3-03` | Deploy (Railway/Fly/Render) com env por ambiente | infra | Segredos fora do repo. `DEV_AUTH_SECRET` **jamais** em produção |
| `V3-04` | ⛔ Desativar `/dev/login` e `/dev/impersonate` em produção — **provado por teste** | backend | Hoje só `ENV=development` protege. Um `ENV` errado = qualquer um entra como qualquer clínica. **Teste automatizado, não confiança** |
| `V3-05` | CI: testes + lint + `tsc -b` em PR | infra | 173 testes só valem se rodarem sozinhos |
| `V3-06` | CI: migration nova exige RLS na tabela nova | infra | Pega o esquecimento antes do vazamento |
| `V3-07` | Backup automático **com restore testado** | infra | 🔴 Backup não restaurado não é backup. Exigir evidência de um restore real |
| `V3-08` | Observabilidade: logs estruturados + erro agregado (Sentry) | ambos | `lib/telemetry/logger.ts` já existe no front, sem destino remoto |
| `V3-09` | Healthcheck + alerta de job travado | backend | Retenção e anti-no-show são jobs. Silêncio = pilar parado sem ninguém saber |
| `V3-10` | Rotina de troca da senha do role `estetica_app` | infra | Hoje é placeholder de dev (`estetica_app_dev`) |
| `V3-11` | Rate limiting nas rotas públicas | backend | `/signup`, `/login`, `/webhooks` |

### V4 — Ativação e medição 🟠 (L-4)

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V4-01` | Tabela `events` append-only (`clinic_id`, `event`, `payload`, `occurred_at`) | backend | Sem UPDATE, sem DELETE. Funil sem comprar ferramenta |
| `V4-02` | Emitir eventos de ativação | backend | `signed_up`, `first_procedure_created`, `first_patient_imported`, `first_sale_recorded`, `first_profit_viewed`, `first_reactivation_sent`, `first_reactivation_converted` |
| `V4-03` | `GET /admin/funnel` — funil e cohort | backend | Rota de plataforma, fora do RLS de tenant, **role separada** |
| `V4-04` | Painel de funil no Super Admin | frontend | Onde a cliente nº 3 desistiu |
| `V4-05` | Meta de time-to-value instrumentada | produto | **Signup → primeiro lucro na tela em < 10 min.** Se passar, corrigir onboarding antes de qualquer feature nova |
| `V4-06` | Onboarding: aceitar "não sei agora" em toda pergunta | frontend | Salva default e marca como estimativa (I7). Onboarding abandonado é pior que número aproximado |
| `V4-07` | Import: gerar oportunidades de retorno retroativas | backend | 🔴 **É isto que dá valor no dia 1.** Sem isso a fila nasce vazia e fica ~90 dias sem valor. ⚠️ Marcar `source=IMPORT` — oportunidade importada **não** conta como receita atribuível (§18.1) |

### V5 — Retenção do produto e prova de valor 🟠

O produto ensina a profissional a reter pacientes. Nada retém a **profissional**.

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V5-01` | Resumo semanal — geração | backend | "Semana passada: R$ 1.240 faturado, R$ 680 de lucro, 3 pacientes para chamar." Job no fuso dela |
| `V5-02` | Envio do resumo (WhatsApp/e-mail) | backend | Opt-in + descadastro em 1 clique. Reusa a disciplina de consentimento existente |
| `V5-03` | Preferências do resumo | frontend | Canal, dia da semana |
| `V5-04` | Alerta de margem negativa por procedimento | ambos | "Peeling está no vermelho: R$ 12 de prejuízo por sessão." **É o insight que ela conta para as colegas** — aquisição disfarçada de feature |
| `V5-05` | Comparativo mês vs. mês anterior | ambos | R$ 800 é bom ou ruim? Sem contexto não vira decisão |
| `V5-06` | Dashboard de impacto acumulado | frontend | `<ROICard />` já existe por período. Falta o acumulado — o argumento da renovação |

### V6 — Diferenciais competitivos 🟢

Nenhum concorrente (Trinks, Belle, Avec, Clinicorp, Feegow) faz isto. É onde o motor de lucro deixa de ser relatório e vira ferramenta de decisão.

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V6-01` | `POST /simulate/price` — simulador | backend | "Se eu cobrar R$ 320 na limpeza, meu lucro vira quanto?" Reusa `calculate_sale()` **puro**, sem persistir. Barato, alto valor percebido |
| `V6-02` | Tela do simulador (slider → lucro ao vivo) | frontend | ⚠️ Todo cálculo vem da API. A lição do `prototypeMath.ts` deletado: nunca calcular lucro no cliente |
| `V6-03` | Sugestão de preço mínimo para margem-alvo | ambos | Inverte o cálculo. Ataca o problema real: ela nunca calculou preço |
| `V6-04` | Histórico de no-show por paciente | ambos | Entrevista: ~20% faltam. "Faltou 3 de 5 vezes — considere pedir sinal". ⚠️ Tom de apoio à decisão, nunca de julgamento |
| `V6-05` | Canal de aquisição por paciente + custo por canal | ambos | Entrevista: impulsionamento subiu de R$ 11 → R$ 50 e parou de converter. **Ninguém no mercado ajuda com isso** |
| `V6-06` | Templates de mensagem editáveis pela profissional | ambos | `lib/constants/messages.ts` já centraliza. Falta a profissional editar. Mensagem robótica queima o canal |
| `V6-07` | Metas mensais (faturamento/lucro) com progresso | ambos | Conecta ao breakeven que já existe |

### V7 — LGPD e maturidade jurídica 🟠

Parte existe (consentimento, opt-out, anonimização, export). Falta o que muda com **cliente pagante**.

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V7-01` | Base legal documentada + contrato de operador | jurídico | 🔴 Com cliente pagante você deixa de ser controlador dos seus dados e passa a ser **operador** de dado sensível de terceiros. Não é formalidade |
| `V7-02` | Política de privacidade e Termos de Uso publicados | produto | Rotas já linkadas no footer da landing — hoje sem destino |
| `V7-03` | Política de retenção (5 anos fiscal) automatizada | backend | Art. 16, II |
| `V7-04` | Canal do titular (solicitação de acesso/exclusão) | ambos | Art. 18 |
| `V7-05` | Trilha de auditoria de acesso a dado de paciente | backend | Precondição para o Estágio "registro clínico" (§30.5 do MVP) |
| `V7-06` | Criptografia em repouso dos campos sensíveis | backend | Idem — o MVP dispensava, o produto pago não |

### V8 — Escala e operação 🟢

*Entra quando:* 5+ clínicas pagando, churn < 5%.

| ID | Task | Onde | Nota |
|---|---|---|---|
| `V8-01` | Múltiplos profissionais por clínica (agenda e lucro por profissional) | ambos | `clinics` já existe; falta o modelo financeiro por profissional |
| `V8-02` | Permissões finas (recepcionista vs. profissional) | ambos | RBAC já tem `admin\|user`; falta granularidade |
| `V8-03` | Agenda: recorrência, bloqueio de horário | ambos | §16.4 do MVP mantinha fora. Entra aqui, com base instalada pedindo |
| `V8-04` | Agendamento online pela paciente (link público) | ambos | 🟠 Trinks/Avec vendem por isso. Superfície pública = LGPD própria |
| `V8-05` | Sync Google Calendar | backend | Só com base instalada que já peça |
| `V8-06` | Anamnese / registro clínico | ambos | ⚠️ **Muda o regime jurídico** (§30.5). Depende de V7-05 e V7-06. Resolve E5 de forma definitiva (unidades consumidas) |
| `V8-07` | Fotos antes/depois | ambos | Armazenamento de imagem de saúde. Depende de V8-06 |
| `V8-08` | Estoque / insumos fracionados | ambos | Depende de V8-06 (unidades consumidas) |
| `V8-09` | Automação n8n (webhooks) | backend | Já era P1 do MVP |
| `V8-10` | Benchmark anonimizado entre clínicas | backend | "Sua margem em limpeza está 12% abaixo da média." Só com base instalada |

---

## 4. Roadmap

Premissa: dev solo, 10-15h/semana.

```text
FASE A — Higiene (1 semana)
└── V1 completo
   ▸ Porta: qualquer dev clona, roda um comando, e o app sobe

FASE B — Produção (2-3 semanas)
└── V3-01..V3-09
   ▸ Porta: sua mãe usa o sistema pelo celular, em produção, com backup restaurável

FASE C — Cliente zero real (30-60 dias, em paralelo)
├── V4-07 (import retroativo) ← valor no dia 1
├── V4-01..V4-05 (medição)
└── V5-06 (impacto acumulado)
   ▸ 🔴 PORTA DE DECISÃO: receita atribuível > mensalidade pretendida?
      ├── NÃO → PARE. Reformule proposta de valor. Não construa cobrança
      └── SIM → siga

FASE D — Monetização (4-6 semanas)
└── V2 completo + V7-01, V7-02
   ▸ Porta: uma colega da sua mãe assina sozinha, paga, e você não toca em nada

FASE E — Crescimento (contínuo)
├── V5 (retenção do produto)
├── V6 (diferenciais)
└── V7 (maturidade jurídica)
   ▸ Porta: 5 clínicas pagando, churn < 5%

FASE F — Escala
└── V8, na ordem que os clientes pedirem
```

> 🔴 **A porta da Fase C é literal.** Não construa cobrança antes de saber que alguém paga. O sistema já tem o instrumento para medir isso (`<ROICard />` + atribuição conservadora) — use-o antes de investir 6 semanas em billing.

---

## 5. Precificação proposta

| Plano | Preço | Limite | Alvo |
|---|---:|---|---|
| **Essencial** | R$ 67/mês | 1 profissional, 100 pacientes ativas | Autônoma iniciante — a maior fatia do mercado |
| **Profissional** | R$ 127/mês | 1 profissional, ilimitado, ROI + resumo semanal | **Plano-âncora.** O caso da sua mãe |
| **Clínica** | R$ 247/mês | Até 5 profissionais, permissões | Depende de V8-01/V8-02 |

**Regras que viram código (V2-11):**
- Limite por **paciente ativa** — proxy do tamanho do negócio dela.
- ⛔ **Nunca** limitar registro de venda. Limitar a venda destrói o dado que gera o ROI que justifica a assinatura.
- Anual com 2 meses grátis: melhora caixa e reduz churn.

---

## 6. Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|:--:|:--:|---|
| **`/dev/login` exposto em produção** | Média | 🔴 Fatal | `V3-04` com teste automatizado. Vazamento entre clínicas = fim do produto |
| Construir billing antes de validar disposição a pagar | Alta | Alto | Porta da Fase C. 6 semanas em risco |
| Cliente zero é sua mãe → viés de complacência | **Certa** | Alto | Medir uso e receita atribuível, nunca satisfação declarada. Cobrar da 2ª cliente cedo |
| Docs defasados levam a retrabalho | **Já acontecendo** | Médio | `V1-01`, `V1-02`. Esta auditoria achou 5 bugs "abertos" já corrigidos |
| Backup nunca restaurado | Média | 🔴 Fatal | `V3-07` exige evidência de restore, não de configuração |
| Escopo escorrega para prontuário/agenda completa | Alta | Alto | §16.4 e §30.5 do MVP. V8-06 tem pré-requisitos jurídicos explícitos |
| Job de retenção falha em silêncio | Média | Alto | `V3-09`. Metade do produto para sem ninguém saber |
| WhatsApp banido por spam | Média | Alto | Consentimento + supressão 14d (já existem) + `V6-06` templates humanos |
| Dev solo esgota antes de monetizar | Média | Alto | Roadmap corta escopo, nunca prazo |

---

## 7. Definition of Done (mantida do MVP)

Uma task só é `[x]` quando:

- [ ] Teste automatizado cobre o caminho principal
- [ ] Nenhuma das invariantes (`ENGENHARIA.md`) foi violada
- [ ] Se toca dinheiro: passa na matriz de configuração
- [ ] Se toca dado de paciente: respeita RLS e foi testado cross-tenant
- [ ] Rodou contra a API/banco real, não mock
- [ ] **Novo:** se toca cobrança, o webhook é idempotente e a assinatura do provedor é verificada

---

## 8. Métricas de sucesso da versão completa

### Produto
| Métrica | Meta |
|---|---:|
| Time-to-value (signup → primeiro lucro na tela) | < 10 min |
| Ativação (registrou 1ª venda em 7 dias) | > 70% |
| Uso semanal | > 80% |
| Divergência vs. extrato da clínica | R$ 0,00 |
| Taxa de retorno vs. baseline | Aumentar |

### Negócio
| Métrica | Meta |
|---|---:|
| Clínicas pagantes | 5 → 25 |
| MRR | R$ 485 → R$ 2.500 |
| Churn mensal | < 5% |
| ARPU | R$ 97+ |
| Lucro recuperado / cliente | > mensalidade (idealmente 5x) |
| CAC via indicação | < 1 mensalidade |

---

## 9. Fora de escopo (o "não" registrado)

Registrar o não é tão útil quanto registrar o depois.

| Item | Por quê |
|---|---|
| TISS / convênios | Estética é predominantemente particular |
| ERP / contabilidade completa | Categoria diferente, concorrentes estabelecidos |
| Marketplace de profissionais | Modelo de negócio distinto, exige os dois lados |
| Gestão de equipe / RH | Periférico mesmo no plano Clínica |
| App mobile nativo | PWA já cobre. Nativo só com demanda comprovada |
| IA | ⛔ Só entra com **um problema nomeado** que ela resolva. "IA" como item de backlog é tecnologia como objetivo |

---

## 10. Princípio de produto (inalterado)

> **Não construir funcionalidades porque são interessantes. Construir porque aumentam receita, protegem margem ou aumentam retenção.**

```text
Isso ajuda a profissional a:
[ ] Ganhar mais dinheiro?   [ ] Perder menos dinheiro?
[ ] Economizar tempo?       [ ] Reter mais pacientes?
Se não: → provavelmente não pertence ao produto agora.
```

**Corolários:**
1. Um número errado é pior que nenhum número. (I7)
2. A regra da primeira cliente não é a regra do produto.
3. 🆕 **Um sistema que não se mede não pode ser melhorado.** (L-4)
