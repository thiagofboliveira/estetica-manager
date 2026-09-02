# Revisão de Produto — Escopo, Lacunas e Backlog de Melhorias

**Papel:** PO/PM · **Data:** 2026-09-01 · **Sobre:** MVP v7.1 (`MVP — ... (v6).md`), `BACKLOG.md`, `ENGENHARIA.md`, `ENTREVISTA.md`

> **Objetivo desta revisão:** o projeto foi especificado para *validar uma hipótese com uma cliente zero*. A ambição declarada agora é outra — **revender como SaaS/micro-SaaS**. Este documento avalia o escopo atual contra essa ambição, aponta o que falta e propõe um backlog priorizado.

---

## 1. Veredito em uma página

### O que está muito acima da média

Isto não é um projeto de fim de semana. Alguns pontos são melhores do que o que se vê em produtos já pagos:

| Ponto forte | Por que importa comercialmente |
|---|---|
| **Sete invariantes escritas e testadas** (`ENGENHARIA.md`) | Dinheiro em `Decimal`, snapshot congelado, `TIMESTAMPTZ`. Concorrente que erra centavo perde o cliente; você já não erra |
| **Motor de lucro parametrizado + matriz de 5 configurações** | Isto é o **fosso competitivo real**. Ninguém no segmento SMB calcula lucro por procedimento com taxa/split/custo variável |
| **RLS forçado + role `NOBYPASSRLS` + repo que exige tenant** | Multi-tenancy de verdade na Fase 0. A maioria dos micro-SaaS descobre isso depois do primeiro vazamento |
| **Hipótese de invalidação explícita** (§1) | Raríssimo. Protege contra investir 6 meses em algo que a usuária "gosta" mas não paga |
| **Princípio de produto + regra de fronteira** (§32, §30.1) | Defesa contra scope creep, que é a causa nº 1 de morte de micro-SaaS solo |
| **63% do backend feito, com evidência exigida** | Progresso real, não teatro de progresso |

**Conclusão da engenharia:** o núcleo está certo. **Não mexa nas invariantes.** Elas são o ativo.

### O que está faltando para virar negócio

Aqui está o problema central desta revisão, e ele é grande:

> 🔴 **O produto não sabe cobrar, não sabe se cadastrar, e não sabe quem é o concorrente.**

Busquei no documento de 2.400 linhas por `billing`, `stripe`, `assinatura` (no sentido de subscription), `trial`, `paywall`, `pricing`, `concorrente`. **Zero ocorrências relevantes.** O que existe:

- `R$ 97+` de mensalidade aparece como *métrica de validação* (§28) — nunca como **feature**.
- Não existe `POST /signup`. O `professionals` é criado por seed manual (UUID fixo em `dev_login`).
- Não existe tabela `subscriptions`, `plans`, `invoices`. Não existe integração com Stripe/Pagar.me/Asaas.
- Não existe trial, limite de plano, tela de "sua assinatura", cancelamento, dunning.
- **Não existe uma única linha de análise competitiva.**

Isso é coerente com a v6 (cujo objetivo era *uma* cliente). É **incompatível** com "revender". Do jeito que está, o dia em que a segunda cliente disser "quero pagar", você não tem como receber o dinheiro dela sem trabalho manual — e a terceira, nem cadastrar.

### O risco de produto mais sério (não é técnico)

> ⚠️ **Metade do produto ainda não existe, e é a metade que gera o ROI.**

O produto tem dois pilares (§1): **clareza financeira** e **retenção**. Olhe o estado real:

| Pilar | Backend | Frontend | Estado |
|---|---|---|---|
| Clareza financeira | T-012..T-024 `[x]` | F-013, F-014 `[x]` | ✅ **Funciona ponta a ponta** |
| **Retenção** | T-025..T-031 **`[ ]` todas** | F-015..F-015c **`[ ]` todas** | ❌ **Não existe nada** |

E a validação inteira depende do segundo pilar:

- A hipótese de invalidação (§1) mede "receita atribuível ao sistema". Receita atribuível **só nasce da lista de reativação**.
- A entrevista **confirmou** a hipótese de retenção: *"tem que lembrar o retorno, não voltam se não lembrar"*.
- O sinal amarelo do §33 é literalmente: *"usam o dashboard mas não a lista de retorno — metade do produto não gera valor"*.

Dashboard financeiro é o que **vende a demo**. Reativação é o que **paga a mensalidade**. Hoje só o primeiro existe.

**Isto é a prioridade nº 1 e não deveria disputar espaço com nada.**

---

## 2. Análise competitiva (a lacuna mais grave do documento)

O documento decide o que não construir citando "concorrentes estabelecidos" (§30.7) sem nunca nomeá-los. Sem isso você não sabe se está construindo um diferencial ou reimplementando o Trinks.

### O mapa do mercado brasileiro

| Concorrente | Posicionamento | Preço aprox. | Força | **Fraqueza que você explora** |
|---|---|---|---|---|
| **Trinks** | Agenda + marketplace para salão/estética | ~R$ 90-250/mês | Marketplace traz cliente novo; marca forte | Financeiro é caixa, **não lucro**. Não sabe custo de insumo nem taxa de maquininha por venda |
| **Belle / Belasis** | Gestão de salão | ~R$ 60-150/mês | Barato, completo em agenda/comanda | Financeiro raso; UX pesada, feita para recepcionista, não para autônoma |
| **Avec** | Agenda + pagamento, foco em beleza | ~R$ 0-150/mês | Onboarding fácil, app bom | Foco em agendamento e pagamento. **Zero inteligência de retenção** |
| **Clinicorp / Simples Dental** | Clínica (odonto/estética avançada) | ~R$ 200-600/mês | Prontuário, TISS, robusto | **Caro e complexo demais** para autônoma solo. Onboarding de semanas |
| **Vhita / Feegow** | Clínica multiprofissional | ~R$ 200-500/mês | Prontuário forte | Mesma coisa: sobra produto, falta simplicidade |
| **Caderno + WhatsApp + Excel** | 🔴 **O concorrente real** | R$ 0 | Zero atrito, zero custo, já dominado | **Não responde "quanto sobrou?" nem "quem devo chamar?"** |

> 🔴 **O concorrente a bater não é o Trinks. É o caderno.** A cliente zero opera hoje com caderno + Instagram + Mercado Pago e nunca calculou ticket médio nem lucro (`requisitos.md`). Isso vale para a maioria do mercado de autônomas. Seu inimigo é a inércia, e a arma contra inércia é **tempo até o primeiro valor**, não quantidade de feature.

### Onde você já ganha (e deve gritar isso)

Três coisas que nenhum concorrente do quadro faz bem:

1. **Lucro real por procedimento**, com taxa de cartão, custo variável (`cost_override`), split de clínica e despesa fixa ratada — não faturamento fantasiado de lucro.
2. **Fila de reativação priorizada por valor potencial**, agrupada por paciente com supressão de 14 dias — não um relatório de "clientes inativos" que ninguém abre.
3. **ROI auto-declarado**: "o sistema te devolveu R$ 700 este mês; ele custa R$ 97". Nenhum concorrente prova o próprio valor. Isto é a arma anti-churn mais forte que existe.

### Onde você perde hoje, e o que fazer

| Lacuna vs. concorrente | Gravidade | Decisão recomendada |
|---|---|---|
| Agenda muito inferior (sem grade, recorrência, drag-drop) | Média | **Aceitar e reposicionar.** "Não sou sua agenda, sou seu financeiro." Mas ver A-05 |
| Sem agendamento online pela paciente (link público) | **Alta** | Trinks/Avec vendem por isso. Entra no Estágio 1, mas **priorize** — ver E-04 |
| Sem app mobile / PWA | **Alta** | Ela trabalha em pé com o celular. F-030 é mais crítico do que "polimento" sugere |
| Sem prontuário/anamnese | Média | §30.5 está **certo** em segurar. Mas é o pedido nº 1 que vai aparecer |
| Sem marketplace / aquisição de cliente novo | Baixa (MVP) | Fora do jogo. Você resolve **retenção**, não aquisição. Diga isso na venda |
| **Sem cobrança própria** | 🔴 **Crítica** | Bloqueia o negócio inteiro. Ver §3 |

---

## 3. As cinco lacunas que bloqueiam "revender"

### L-1 — 🔴 Não existe self-serve: signup, tenant provisioning, billing

**Hoje:** `professionals` nasce de `INSERT` manual com UUID fixo. Não há signup, plano, cobrança, trial ou cancelamento.

**Consequência:** cada cliente novo é trabalho manual seu. Isso não escala para 5, muito menos para 50. E sem cobrança automatizada, você não tem MRR — tem Pix na sua conta e planilha.

**O que precisa existir (mínimo honesto):**
- `POST /signup` → cria `user` + `professional` + `financial_settings` com defaults + trial de 14 dias, numa transação.
- Tabela `subscriptions` (`plan`, `status`, `trial_ends_at`, `current_period_end`, `provider_customer_id`).
- Integração com **um** provedor. Recomendo **Stripe** (assinatura recorrente + Pix + cartão, webhook maduro) ou **Asaas** (mais barato em Pix/boleto no Brasil, API simples). Não construa cobrança na mão.
- Webhook de pagamento → muda `subscription.status`. Idempotente (mesma disciplina do T-015a).
- Middleware de gate: `status IN (TRIALING, ACTIVE)` libera; `PAST_DUE` mostra banner; `CANCELED` deixa **ler e exportar**, nunca escrever.

> ⚠️ **Nunca bloqueie o acesso aos dados dela.** Cliente inadimplente que perde o histórico não volta e reclama publicamente. Read-only + exportação CSV é o comportamento correto (e LGPD Art. 18, V pede portabilidade de qualquer forma).

### L-2 — 🔴 Não existe funil de ativação medido

**Hoje:** T-035/F-021 é um "checklist de primeiro acesso". Não há evento, não há medição, não há noção de time-to-value.

**Consequência:** você não vai saber *onde* a segunda cliente desistiu. Micro-SaaS morre de ativação, não de feature faltando.

**Precisa:** tabela `events` (append-only, `professional_id`, `event`, `payload`, `occurred_at`) e um punhado de eventos nomeados: `signed_up`, `first_procedure_created`, `first_sale_recorded`, `first_profit_viewed`, `first_reactivation_sent`, `first_reactivation_converted`. Com isso você tem funil e cohort sem comprar ferramenta.

**Meta de ativação:** *da criação da conta ao primeiro lucro na tela, em menos de 10 minutos.* Se passar disso, corrija o onboarding antes de construir qualquer feature nova.

### L-3 — 🟠 Não existe caminho de migração do caderno

**Hoje:** a única forma de entrar dado é digitar tela por tela. A cliente zero tem "ficha da maioria com os números" no papel e 35 avaliações no Google.

**Consequência:** a nova usuária abre o sistema, vê tudo vazio, e a lista de reativação — o pilar que gera ROI — **fica vazia por 3 meses**, porque só nasce de vendas registradas no sistema. Ela não vai esperar 3 meses para ver valor.

**Precisa:** importação de pacientes via CSV/planilha **com data do último atendimento e procedimento**. Isso é o que faz a fila de reativação nascer cheia no dia 1 — e é o único jeito de o produto provar valor na primeira semana em vez do primeiro trimestre.

> 💡 Esta é a melhoria com **melhor razão esforço/impacto de todo este documento.** Ela transforma o time-to-value de 90 dias em 1 dia.

### L-4 — 🟠 O produto não sabe se vender nem se provar

**Hoje:** não há landing page, não há tela de preço, e o dashboard de impacto (F-040, T-037/038) está adiado como P1.

**Consequência:** sem página, não há como uma colega da sua mãe descobrir o produto. Sem dashboard de impacto, não há como responder "por que eu pago isso?" no dia da renovação.

**Precisa:** landing page de uma página (proposta de valor, 3 prints, preço, CTA de trial) e o dashboard de impacto **promovido de P1 para P0 comercial** — os dados já são registrados desde o dia 1 por decisão da §19, a tela é barata, e é o ativo anti-churn.

### L-5 — 🟡 Retenção do produto ≠ retenção da paciente

**Hoje:** o produto ensina a profissional a reter pacientes. Nada retém a **profissional**.

**Precisa (barato, alto retorno):** resumo semanal por WhatsApp/e-mail — *"semana passada: R$ 1.240 faturado, R$ 680 de lucro, 3 pacientes para chamar."* Traz ela de volta sem ela decidir voltar. É o loop de engajamento que o produto não tem.

---

## 4. Ajustes de escopo recomendados no MVP atual

Coisas já especificadas que eu, como PO, mudaria de prioridade ou de forma.

| # | Item | Hoje | Recomendação | Por quê |
|---|---|---|---|---|
| A-01 | **Motor de retenção** (T-025..031, F-015..c) | Fase 3, `[ ]` | 🔴 **Prioridade absoluta, agora** | Sem ele, o produto é meio produto e a hipótese não é testável |
| A-02 | **`PATCH /sales/{id}`** (T-017) | `[ ]` "fora do escopo" | 🔴 **P0, agora** | O front já reportou: "erro de digitação não tem conserto". A §27 lista isso como critério de aceite e como não-cortável. É a primeira coisa que ela vai precisar |
| A-03 | **Responsivo/mobile** (F-030) | Fase 4 "Polimento" | 🔴 **Subir para P0** | Ela trabalha em pé, celular na mão. Se não funciona no celular, não é usado. Não é polimento, é o meio de acesso principal |
| A-04 | **Dashboard de impacto** (F-040, T-037/38) | P1 adiado | 🟠 **P0 comercial** | É a resposta a "por que pago?". Dados já existem |
| A-05 | **Agenda mínima** (T-032..034, F-017..019) | Fase 3 | ✅ Manter, **não expandir** | §16.4 está correta. Resista ao pedido de grade/drag-drop; cada hora ali é uma hora não gasta no diferencial |
| A-06 | **Erro silencioso de parcela fora da faixa** | Bug reportado no front | 🔴 Corrigir | Viola I7 e o corolário "número errado é pior que nenhum número". Venda passa com taxa zerada, silenciosamente |
| A-07 | **`has_provisional_profit` no dashboard** (F-013b) | Bloqueado por contrato | 🟠 Adicionar o campo | Invariante I7 exige. É um booleano no agregado |
| A-08 | **LGPD** (T-059..062) | Fase 4 | 🔴 **Antes da 2ª cliente**, não só da 1ª | Com cliente pagante você é **operador** de dado sensível de terceiros. Sem base legal e contrato, é exposição real |
| A-09 | **`ConfigVersion`** (T-020a) | `[ ]` pendência | ✅ Manter adiado | A justificativa é boa: o snapshot já protege o histórico. Bom exemplo de escopo bem cortado |
| A-10 | **Backup com restore testado** (T-047) | Fase 4 | 🔴 Antes de qualquer cliente pagante | Backup não testado não é backup. Perder dado financeiro de cliente pagante encerra o produto |

---

## 5. Melhorias e features propostas (novas)

Filtradas pelo princípio da §32 — cada uma responde *ganhar mais / perder menos / economizar tempo / reter mais*.

### 5.1 Épico N-1 — Monetização e self-serve 🔴 (bloqueia o negócio)

| Feature | Valor |
|---|---|
| Signup self-serve com provisionamento de tenant | Sem isso, cada cliente é trabalho manual seu |
| Trial de 14 dias sem cartão | Padrão do segmento; reduz atrito de entrada |
| Planos e assinatura recorrente (Stripe ou Asaas) | Transforma Pix na conta em MRR |
| Gate de acesso por status, com read-only no cancelamento | Cobra sem sequestrar o dado dela |
| Tela "Minha assinatura" + cancelamento self-serve | Cancelamento fácil reduz chargeback e reclamação |
| Cupom / indicação | A entrevista disse que o canal é **boca a boca entre colegas**. Indicação é seu CAC mais barato |

### 5.2 Épico N-2 — Ativação e time-to-value 🔴

| Feature | Valor |
|---|---|
| **Importação de pacientes por CSV com último atendimento** | Fila de reativação cheia no dia 1 em vez do dia 90 |
| Catálogo de procedimentos pré-carregado (limpeza, peeling, botox, acne…) com preço/custo/intervalo de mercado | Corta 20 minutos do onboarding. Ela ajusta, não cria do zero |
| Eventos de produto + funil de ativação | Sem medição você chuta onde o funil vaza |
| Onboarding em 4 passos com "não sei agora" em toda pergunta | Já previsto (F-021a) — manter a disciplina |

### 5.3 Épico N-3 — Retenção do produto e prova de valor 🟠

| Feature | Valor |
|---|---|
| Resumo semanal (WhatsApp/e-mail) | Traz ela de volta sem depender de disciplina |
| Dashboard de impacto / ROI | Responde "por que pago?" na renovação |
| Alerta de margem negativa por procedimento | *"Peeling está no vermelho: R$ 12 de prejuízo por sessão."* Este é o insight que faz ela contar para as amigas |
| Comparativo mês vs. mês anterior | Contexto: R$ 800 de lucro é bom ou ruim? |

### 5.4 Épico N-4 — Diferenciais competitivos 🟢

| Feature | Valor |
|---|---|
| **Simulador de preço** ("se eu cobrar R$ 320 na limpeza, meu lucro vira quanto?") | Nenhum concorrente tem. Vira o motor de lucro em ferramenta de decisão, não só relatório |
| Sugestão de preço mínimo por procedimento (para margem-alvo) | Ataca o problema real: ela não sabe precificar |
| Insight de no-show por paciente | Entrevista: 20% faltam. *"Esta paciente faltou 3 de 5 vezes — peça sinal"* |
| Custo de aquisição por canal (Instagram/Google/indicação) | Entrevista: ela reclama que o impulsionamento subiu de R$ 11 para R$ 50 e não converte mais. Ninguém no mercado ajuda com isso |
| Templates de mensagem de reativação editáveis | Mensagem boa converte mais; mensagem robótica queima o canal |

### 5.5 Épico N-5 — Aquisição 🟠

| Feature | Valor |
|---|---|
| Landing page com preço e trial | Porta de entrada. Não existe hoje |
| Página pública de indicação | O canal declarado é colega→colega |
| Exportação CSV | LGPD Art. 18 V + tira o medo de "ficar preso" |

---

## 6. Estratégia de precificação

O documento fixa R$ 97 sem estrutura. Recomendo três degraus:

| Plano | Preço | Limite | Alvo |
|---|---:|---|---|
| **Essencial** | R$ 67/mês | 1 profissional, 100 pacientes ativas | Autônoma iniciante (a maior fatia do mercado) |
| **Profissional** | R$ 127/mês | 1 profissional, ilimitado, impacto+ROI, resumo semanal | O caso da sua mãe. **Plano-âncora** |
| **Clínica** | R$ 247/mês | Até 5 profissionais | Estágio 3 — só quando `account_id` for decidido (§21.2) |

**Razões:**
- R$ 97 único deixa dinheiro na mesa em cima e assusta a iniciante embaixo.
- Anual com 2 meses grátis melhora caixa e reduz churn.
- **Não limite por número de vendas registradas.** Limitar o registro de venda destrói o dado que gera o ROI que justifica a assinatura. Limite por paciente ativa, que é proxy de tamanho do negócio dela.

---

## 7. Roadmap revisado

Premissa: dev solo, 10-15h/semana. Estado atual: backend 63%, frontend 47%.

```text
AGORA (4-6 sem) — Completar o produto
├── Motor de retenção completo (T-025..031 + F-015..c)   ← metade do produto
├── PATCH /sales (T-017)                                  ← corrigir erro de digitação
├── Agenda mínima (T-032..034b + F-017..019a)
├── Mobile/responsivo (F-030) + estados vazios (F-031)
└── LGPD (T-059..062) + deploy com restore testado (T-047)
   ▸ Porta de saída: fluxo completo funcionando no celular da sua mãe

VALIDAÇÃO (30-60 dias) — Cliente zero
├── Importação CSV  ← para a fila de reativação nascer cheia
├── Eventos de produto + baseline (T-050)
├── Dashboard de impacto (F-040)
└── 30 dias de uso real (T-051)
   ▸ Porta de saída: receita atribuível > R$ 97/mês. Se não, PARE e reformule (§33)

COMERCIAL (4-6 sem) — Só depois do sinal verde
├── Signup self-serve + trial
├── Billing (Stripe/Asaas) + gate + tela de assinatura
├── Landing page + preço
└── Catálogo de procedimentos pré-carregado
   ▸ Porta de saída: uma colega da sua mãe assina sozinha, sem você tocar em nada

ESCALA (contínuo) — 5 pagantes em diante
├── Simulador de preço + sugestão de preço mínimo
├── Resumo semanal + alerta de margem negativa
├── Anti-no-show (T-052..054) + n8n
└── Insight de canal de aquisição
```

> 🔴 **A porta de saída da fase VALIDAÇÃO é literal.** Não construa billing antes de saber que alguém paga. O único jeito de descobrir isso é o pilar de retenção funcionando por 30 dias. É por isso que ele vem primeiro, sozinho.

---

## 8. Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|:--:|:--:|---|
| **Retenção não é construída e a hipótese nunca é testada** | Alta | Fatal | Congelar features novas até T-025..031 e F-015 estarem `[x]` |
| Time-to-value longo (fila vazia por 90 dias) | Alta | Alto | Importação CSV com data do último atendimento |
| Escopo escorrega para agenda/prontuário | Alta | Alto | §16.4 e §30.5 existem para isso. Cite-as em voz alta |
| Cliente zero é sua mãe → viés de complacência | **Certa** | Alto | Medir uso e receita atribuível, nunca satisfação declarada. A hipótese de invalidação da §1 é sua defesa — respeite-a |
| Amostra de N=1 vira "a regra do produto" | Alta | Médio | §32 segundo corolário. Cobrar a 2ª e a 3ª cliente cedo (mesmo com desconto) |
| Vazamento entre profissionais | Baixa | Fatal | RLS já forçado; **fechar T-046/046a/046b** |
| WhatsApp banido por spam de reativação | Média | Alto | Consentimento (T-060) + supressão 14d + templates humanos |
| Dev solo esgota antes de validar | Média | Alto | Roadmap acima corta escopo, não prazo |
| Concorrente adiciona "lucro real" | Baixa | Médio | Improvável: exige remodelar o núcleo deles. É seu fosso |

---

## 9. As cinco decisões que eu levaria para você hoje

1. **Congelar tudo e terminar o pilar de retenção.** É a única coisa que torna a hipótese testável. 4-6 semanas.
2. **Fazer a importação CSV.** Transforma time-to-value de 90 dias em 1 dia. Provavelmente 2-3 dias de trabalho.
3. **Promover mobile de "polimento" para P0.** Ela trabalha em pé, com o celular. Isso não é opcional.
4. **Não construir billing ainda** — mas parar de tratá-lo como inexistente. Ele é um épico real que entra na fase COMERCIAL.
5. **Cobrar da segunda cliente cedo, mesmo barato.** Sua mãe vai dizer sim por amor. A segunda cliente diz sim por valor — e é o único "sim" que valida o negócio.

---

## 10. Onde as tarefas vivem

Este documento é **análise e priorização**. As tarefas derivadas dele foram quebradas nos backlogs de execução:

- **Backend:** [backend/BACKLOG.md](backend/BACKLOG.md) — seção "FASE 5+ — Negócio (derivado de REVISAO-PRODUTO.md)"
- **Frontend:** [frontend/BACKLOG.md](frontend/BACKLOG.md) — seção "FASE 5+ — Negócio (derivado de REVISAO-PRODUTO.md)"
- **Coordenação:** [BACKLOG.md](BACKLOG.md)

Mudança de escopo continua entrando primeiro no MVP v7.1 (§ correspondente), depois nos backlogs — a regra atual do projeto se mantém.
