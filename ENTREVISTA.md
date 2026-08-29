# Roteiro da Entrevista — Cliente Zero

**Duração:** ~1 hora · **Task:** T-048 · **Destrava:** Fase 2 inteira

> ✅ **T-048 CONCLUÍDA em 2026-08-29.** Todos os eixos bloqueantes (E1-E8) estão resolvidos ou marcados como não-aplicáveis. **A Fase 2 está destravada.**
>
> Três rodadas de respostas (via Thiago, não entrevista formal gravada):
> - [[respostas-parciais-2026-08-29]] — rodada 1: custos, pacotes, LGPD, modelo de aluguel
> - [[respostas-rodada-2-2026-08-29]] — rodada 2: baseline financeiro, custos operacionais, anamnese, no-show
> - [[incidente-agendamento-2026-08-29]] — incidente real de agenda → gerou `bookings` (MVP §16.6)
> - [[respostas-rodada-3-2026-08-29]] — rodada 3: Pix/por sessão → **fecha E7**
>
> **Perguntas menores que seguem abertas** (nenhuma bloqueia código): o que acontece se a paciente somer com sessões de pacote; desconto em pacote de itens diferentes; taxa da maquininha no caso raro de cartão; faturamento bruto exato. Ver §Pacotes e §E4.

---

## Antes de começar

**Leve:** o celular dela, o extrato do último repasse da clínica, e a agenda/caderno onde ela anota hoje.

**Não leve:** protótipo, tela, nada do sistema. Isso enviesa a resposta — ela vai descrever o que cabe na tela em vez do que ela faz.

**A postura:** você não está validando uma ideia, está **coletando a configuração de um caso real**. Se a resposta dela não couber no modelo, o modelo está errado — não ela.

**Grave o áudio** (com permissão). Você vai querer reouvir a parte financeira.

---

## Bloco 1 — Dinheiro (o mais importante)

> Comece pedindo o extrato do último repasse. **Um documento real vale mais que dez respostas de memória** — muita gente nunca fez essa conta e responde o que acha.

### A pergunta que resolve quatro eixos

> **"Quando você passa R$ 1.000 no cartão, quanto cai na sua conta e quando?"**

Deixe ela responder inteiro antes de perguntar mais. Anote o número **e** o prazo.

| Se ela disser | Você descobriu |
|---|---|
| "Cai R$ 950, uns 30 dias" | Taxa ~5% dela (**E1** = PROFESSIONAL), D+30, sem antecipação |
| "A clínica me passa R$ 700" | Split 30%, e precisa cavar se a taxa já saiu antes |
| "Depende de quantas vezes parcelou" | **E4** relevante — pergunte as faixas |
| "Recebo na hora, tem uma taxa a mais" | **E7** = antecipa → **vira P0** |

> ✅ **Já sabemos:** ela não tem split percentual com clínica — paga **aluguel fixo de sala (~R$800/mês)**, o que virou uma categoria nova (despesas fixas, MVP v7 §12.5) em vez de forçar dentro de E1/E2. Ela trabalha muito com Pix (sem taxa de maquininha). O que falta abaixo é sobre quando ela **usa cartão**.

### E1 — Quem paga a taxa da maquininha

> "A taxa da maquininha sai do seu bolso ou a clínica cobre?"

Se ela hesitar: *"No extrato aparece o valor cheio ou já com a taxa descontada?"*

- [ ] Dela (`PROFESSIONAL`)
- [ ] Clínica (`CLINIC`)
- [ ] Dividido (`SPLIT_PRO_RATA`)
- [ ] Não sabe → default `PROFESSIONAL` + badge de estimativa

### E2 — Base do split

> ✅ **Não se aplica no caso dela** — sem split de clínica (aluguel fixo cobre esse papel). Deixar a pergunta no roteiro para outros profissionais que tenham split real.

~~"A clínica calcula a parte dela sobre o valor cheio, ou sobre o que sobra depois da taxa?"~~

- [ ] Valor cheio (`GROSS`)
- [ ] Depois da taxa (`NET_OF_FEE`)
- [ ] Não sabe → `GROSS` + estimativa

### E4 — Parcelamento

> 🟡 **Parcialmente respondido (rodada 2).** Ela cobra **por sessão**, não à vista o pacote inteiro — cada sessão é paga separadamente, majoritariamente por **Pix**. Ela tem Mercado Pago disponível, mas evita usar: todas as parcelas têm juros, **exceto o prazo de 30 dias, que não tem juros** — e ela prefere assim deliberadamente, para não movimentar muito a conta e ter noção clara do que recebe por mês. Isso é mais um dado de **comportamento/preferência de fluxo de caixa** do que de configuração de parcelamento clássica (1x/2x/.../12x com taxas crescentes) — ela na prática não parcela no sentido do modelo original.
>
> ❓ **Ainda falta confirmar:** quando ela usa o cartão via Mercado Pago (mesmo que raro), a taxa muda por faixa de parcelas? E qual a taxa mesmo no prazo de 30 dias "sem juros" — normalmente esse prazo ainda tem uma taxa de maquininha embutida (diferente de "juros ao cliente"), vale confirmar se ela recebe o valor cheio ou com desconto.

- [x] Cobra por sessão, não à vista → tabela de faixas de parcelamento **não se aplica** do jeito que estava modelada — ela não parcela uma venda em N vezes, ela fatia a venda em sessões pagas individualmente (isso já é natural do modelo Sale/SaleItem/Session)
- [ ] Taxa de maquininha no caso raro de cartão: ainda não confirmada

### E7 — Antecipação 🔴 → ✅

> ✅ **Resolvido por dedução (rodada 3).** Ela recebe majoritariamente por **Pix, por sessão** — Pix cai na hora, não existe recebível para antecipar. Cartão é raro e ela o evita deliberadamente ("prefere não movimentar muito a conta"). **Antecipação não existe no fluxo dela.**

~~"Você costuma antecipar o dinheiro do cartão para receber antes?"~~

- [x] Não → **E7 segue P1**, como o plano original supunha. Último bloqueio crítico da entrevista removido.

### E6 — Split por procedimento

> ✅ **Não se aplica** — mesmo motivo do E2 (sem split de clínica no caso dela).

~~"A clínica fica com a mesma porcentagem em todo procedimento?"~~

- [ ] Mesma para todos → P1 confirmado
- [ ] Varia → anotar quais: _______________

---

## Bloco 2 — Custos

### E5 — Custo variável

> ✅ **Respondido.** Varia: Botox é por unidade aplicada, ela reaproveita sobra de frasco em outro cliente **se houver alguém na fila dentro do prazo de validade após aberto** — senão perde o excedente. Confirma que `cost_override` por venda é necessário (já é P0 no modelo, §12.1).

~~"Um Botox de 20 unidades e um de 50 custam a mesma coisa pra você?"~~

- [x] Varia → `cost_override` é essencial. Ela sabe medir? **Sim, por unidade aplicada** — mas não anota formalmente (ver Bloco 4).

### Pergunta nova 🆕

> ✅ **Respondido.** Sim, o frasco aberto vence — se não usar em ninguém a tempo, perde a sobra. Confirma que custo real é **por aplicação com risco de perda por vencimento**, não por frasco cheio. Ainda fora do MVP (inventário fracionado é visão Estágio 3), mas o `cost_override` manual por venda no MVP já permite ela registrar o custo real mesmo sem rastrear o frasco formalmente.

~~"Quando você compra um frasco e sobra, essa sobra vence? Você joga fora?"~~

---

## Bloco 3 — Pacotes

### E8 — Validade

> ✅ **Respondido.** Sem prazo para usar — confirma o default do modelo.

- [x] Sem prazo (default)
- [ ] Prazo de ___ meses → status `EXPIRED` precisa de data-limite

### Perguntas que ficaram em aberto 🆕

> ❓ **AINDA EM ABERTO.** "Se a paciente comprou 10 sessões e sumiu na sexta, o que você faz?"

Isso valida a regra de `EXPIRED` liberar o custo provisionado — e revela se ela devolve dinheiro, o que o modelo **não** prevê hoje. Ela confirmou que remarcação é sempre permitida (não expira), mas "sumir de vez" ainda não foi perguntado.

- [ ] Não faz nada, ela perde
- [ ] Devolve proporcional → ⚠️ **não modelado.** Falaria com você antes de codar
- [ ] Deixa em aberto para sempre

> ❓ **AINDA EM ABERTO.** "Pacote de procedimentos diferentes: você dá desconto sobre a soma?"

- [ ] Sim, desconto no total (rateio proporcional — já modelado)
- [ ] Preço fechado, sem referência aos itens → ⚠️ muda `unit_price`

---

## Bloco 4 — Operação diária

Não são eixos de configuração, mas calibram a UX.

> ✅ **Respondido.** Não atende todos os dias, mas quase toda semana; 2-3 clientes nos dias que atende.

~~"Quantos atendimentos você faz num dia cheio?"~~ → dimensiona listas e paginação. **Confirma: nem lista nem paginação precisam suportar volume alto — 2-3/dia está bem abaixo de qualquer limite que preocupe.**

> ❓ **Ainda não perguntado diretamente**, mas a resposta de LGPD (Bloco 6) sugere que é tudo de cabeça/WhatsApp, não em app ou caderno formal.

~~"Você registra na hora ou no fim do dia?"~~ → se for no fim do dia, a meta dos 30 segundos importa menos que registrar 8 de uma vez

> ✅ **Respondido.** Não anota em nada formal — tudo fica no WhatsApp e na memória. **Sinal importante:** já aconteceu lead do Instagram esperando **mais de uma semana** sem resposta — evidência real (não hipotética) de que coisas se perdem sem sistema.

~~"O que você usa hoje para anotar?"~~ (caderno, Excel, app) → mostra o que ela vai comparar com o produto

> ✅ **Respondido.** Em torno de 10-15 pacientes ativas — confirma que busca simples (sem paginação server-side sofisticada) é suficiente no MVP.

~~"Quantas pacientes ativas você tem, mais ou menos?"~~ → dimensiona a busca

> ❓ **Ainda não perguntado diretamente** — mas o caso do lead do Instagram sem resposta por uma semana já é um sinal forte a favor da hipótese de retenção, mesmo sendo sobre captação de lead novo, não sobre paciente que já é cliente. Vale perguntar o caso específico de paciente-que-já-atendeu-e-sumiu para confirmar 1:1 com a proposta de valor do produto (retorno pós-procedimento).

---

## Bloco 5 — Baseline (T-050)

Sem isso não há contrafactual, e a métrica de receita atribuída não tem com o que comparar.

> ✅ **Respondido em 2026-08-29 (rodada 2).** Ver detalhes abaixo — faltou só confirmar faturamento bruto (temos custo e lucro líquido, falta o bruto exato) e o "quantas voltam sozinhas" ainda não tem número, mas já temos um proxy forte: poucos recorrentes, maioria não volta sem lembrete.

- [x] Custo mensal: **R$ 1.300** (não tínhamos pedido faturamento bruto, só custo+lucro — dá pra inferir bruto ≈ R$ 2.100, a confirmar)
- [x] Lucro líquido que sobra por mês: **R$ 800**
- [x] Nº de atendimentos/mês: **~10** (5 recorrentes + 5 não-recorrentes/mensal)
- [x] Nº de pacientes ativas: ~10-15 (já tínhamos)
- [ ] **Quantas voltam sozinhas, sem você chamar?** — ainda não é um número, mas o relato ("poucos recorrentes", "maioria que faz limpeza não volta") é consistente com **poucas voltam sozinhas**. Confirmado que isso é efeito do **intervalo natural do tratamento** (limpeza de pele tem intervalo maior, não é mensal por natureza), não de esquecimento dela — a hipótese de retenção continua de pé, o produto ataca exatamente "lembrar quando a janela do intervalo abrir".
- [x] **Nº de faltas (no-show) por mês: ~20% dos agendamentos**, sem aviso
- [x] Ticket médio: tratamento de acne R$ 280/sessão (pacote de 6), limpeza de pele geralmente também paga por sessão — **50% acne / 50% limpeza** no mix

> 🟡 **Faturamento bruto mensal ainda não confirmado diretamente** — só custo (R$1.300) e lucro (R$800) foram informados. Vale perguntar o bruto exato para bater a conta, mas não bloqueia mais nada.

---

## Bloco 6 — LGPD (rápido, mas necessário)

> ✅ **Respondido.** Ela manda mensagem, mas **não pede consentimento formal** hoje. Confirma que o checkbox de consentimento no cadastro (F-011b, já implementado no frontend) precisa vir **desmarcado por padrão** — não dá para assumir consentimento retroativo de quem já é paciente. Antes do primeiro envio real pelo produto, ela vai precisar recolher consentimento novo (mesmo que informalmente, por mensagem).

~~"Você manda mensagem para as pacientes hoje? Elas autorizaram?"~~

- [x] Nunca pediu → precisa do texto de consentimento antes do primeiro envio

> ✅ **Respondido (indiretamente).** Ela guarda tudo "de cabeça", sem anotação — não foi mencionado nenhum registro de dado de saúde (alergia, medicamento). Ainda vale confirmar diretamente, mas não há sinal de anamnese informal existente hoje. Segue confirmando que anamnese fica fora do MVP (visão, Estágio 2).

~~"Você guarda alguma informação de saúde delas? Alergia, medicamento?"~~

- [ ] Não — **provável, mas não confirmado explicitamente**
- [ ] Sim, no papel/caderno → confirma que anamnese é demanda real (visão, Estágio 2)

---

## Depois da entrevista

1. **Preencher a matriz de configuração** (T-044) com o caso dela como 6º cenário nomeado
2. **Atualizar os defaults de mercado** (§8.1) se os números dela sugerirem que os seed estão fora da realidade
3. **Reavaliar E7** — se ela antecipa, mover para P0 no backlog
4. **Registrar o que não coube** — toda resposta que não encaixou nos eixos é um achado de produto

### Sinais de alerta

| Se aparecer | Significa |
|---|---|
| Ela vende pacote com devolução proporcional | Modelo de estorno incompleto — falar antes de codar |
| Ela antecipa recebíveis | E7 vira P0 |
| Split varia por procedimento **e** ela usa muito | E6 pode virar P0 |
| Mais de 70% das pacientes voltam sozinhas | Hipótese de retenção fraca — revisar a proposta de valor |
| Ela não sabe responder E1 nem E2 | Normal. Use defaults + badge, e confira no próximo repasse |

---

## O que NÃO perguntar

- ❌ "Você usaria um sistema assim?" — todo mundo diz sim
- ❌ "Quanto você pagaria?" — resposta hipotética não vale nada; o preço se testa cobrando
- ❌ "Que funcionalidades você quer?" — ela vai listar o que já viu em outro app
- ❌ Nada com jargão: `split_base`, `enum`, "configuração de tenant"

Pergunte sobre o que ela **faz**, não sobre o que ela **acha**.

---

## Respostas parciais — 2026-08-29 {#respostas-parciais-2026-08-29}

Recebidas via Thiago, não em entrevista formal gravada com ela. Resumo do que mudou de status:

### Resolvido
- **E5 + pergunta do frasco**: custo varia por aplicação (Botox por unidade), frasco aberto vence — perde a sobra sem cliente na fila a tempo.
- **E8**: pacotes sem prazo de validade, remarcação sempre permitida.
- **Bloco 4 (parcial)**: 2-3 atendimentos/dia, quase toda semana; ~10-15 pacientes ativas; não anota nada formal (tudo WhatsApp/memória); lead do Instagram já ficou > 1 semana sem resposta.
- **Bloco 6**: manda mensagem sem consentimento formal hoje; sem sinal de dado de saúde guardado (não confirmado explicitamente).
- **Modelo de custo da clínica**: não é split percentual — é **aluguel fixo de sala (~R$800/mês)**. Isso não cabia em E1/E2 (que modelam custo *por venda*) e virou uma decisão de produto nova: **EPIC-08a — Despesas Fixas**, adicionada ao MVP v7 (`fixed_expenses`, TASK-018c/018d, ajuste no dashboard TASK-022). E2 e E6 passam a **não se aplicar** ao caso dela (sem split de clínica).

### Ainda em aberto — perguntar direto para ela
- 🔴 **E7 (antecipação)** — se ela antecipa recebíveis do cartão, vira P0 imediatamente. **Único crítico que segue sem resposta.**
- **Pacote com sumiço** — se a paciente compra 10 sessões e desaparece de vez (não é remarcação), o que acontece. Devolução não está modelada hoje.
- **Pacote de itens diferentes** — desconto rateado na soma ou preço fechado sem referência aos itens.
- Taxa de maquininha no caso raro de cartão via Mercado Pago (ver E4 atualizado).
- Faturamento bruto mensal exato (temos custo R$1.300 e lucro R$800, falta o bruto para bater a conta).

---

## Respostas rodada 2 — 2026-08-29 {#respostas-rodada-2-2026-08-29}

Recebidas via Thiago, em texto livre (não roteiro ponto a ponto). Cobriu principalmente Bloco 2 (custos), Bloco 5 (baseline) e comportamento de pagamento.

### Baseline financeiro (Bloco 5 — praticamente resolvido)
- Custo mensal estimado: **R$ 1.300**. Lucro líquido: **R$ 800/mês**.
- ~10 atendimentos/mês: 5 recorrentes + 5 não-recorrentes.
- Mix: 50% tratamento de acne (6 sessões, R$280/sessão) / 50% limpeza de pele.
- **No-show: ~20% dos agendamentos faltam sem avisar** — número real, direto para calibrar a feature de lembrete/confirmação (hoje fora do MVP, P1 "confirmação de no-show" F-041 — vale reconsiderar prioridade com esse dado).
- Ela nunca calculou ticket médio nem lucro antes — reforça a proposta de valor central do produto.

### Retenção — hipótese confirmada, não enfraquecida
"Poucos recorrentes" e "maioria da limpeza de pele não volta" **não é sinal de que a hipótese de retenção é fraca** — é efeito do intervalo natural de cada tratamento (limpeza tem janela maior que Botox, e a base de clientes dela é majoritariamente nova, ainda no início do relacionamento). Confirmado diretamente: ela precisa **lembrar** o retorno, e cliente não volta se ela não lembrar. Isso é exatamente a dor que a Fase 3 (retorno/retenção) ataca — a hipótese segue de pé.

### Custos operacionais — mais amplos do que só aluguel
Além do aluguel (~R$800, já mapeado), ela também tem: **descarte de lixo biológico, água, luz, lanche para pacientes (dividido), taxa anual de vigilância sanitária/prefeitura, custo com educação continuada (cursos)**. Confirma que a categoria "despesas fixas" (MVP v7 §12.5) precisa ser mesmo genérica (texto livre), não uma lista fechada pensada só para "aluguel" — já era a decisão tomada, isso só reforça que estava certa. Vale notar que a taxa de vigilância é **anual**, não mensal — o campo `active_from`/`active_to` de vigência já suporta isso, mas o dashboard mensal vai precisar ratear ou destacar separadamente esse tipo de despesa anual (não resolvido ainda, ver nota abaixo).

### Anamnese — já existe informalmente, fora do MVP
Ela já faz **anamnese anual, com alergias e histórico de tratamentos, ~30 minutos, cobrada como consulta separada** antes de aplicar Botox. Para outros procedimentos (revitalização facial), a anamnese acontece dentro da própria sessão, e o **upsell de outros serviços acontece durante o atendimento**, não como venda agendada à parte. Isso é dado real e valioso para a visão de produto (Estágio 2), mas **não muda o MVP** — reforça que anamnese é demanda genuína, não hipótese.

### Botox — regra de conservação
Instrução de bula diz "usar no mesmo dia", mas o curso dela ensinou que dá pra guardar na geladeira por até 30 dias. Detalhe operacional relevante para o "não modelado" do frasco/sobra (§ Bloco 2), mas ainda não muda o MVP — seguiria como está: `cost_override` manual por venda já cobre o caso, o rastreio formal do frasco é Estágio 3.

### Comportamento de pagamento
Cobra **por sessão**, nunca a venda inteira de uma vez; majoritariamente **Pix**; evita Mercado Pago porque as parcelas têm juros (exceto 30 dias) e ela prefere não movimentar muito a conta, para ter noção clara do que recebe por mês. Ver E4 atualizado acima — isso não é "parcelamento" no sentido clássico do modelo, é geração de uma venda por sessão.

### Perfil de aquisição de cliente (contexto, não escopo de produto)
35 avaliações no Google hoje. Ficha da maioria tem telefone, mas os primeiros clientes (boca a boca) não têm registro. Maioria dos clientes são novos, vindos de Instagram/Google — ela relatou que o custo de anúncio no Instagram subiu bastante (de R$11 para R$50/dia) e sente que parou de funcionar tão bem. Poucos vêm de indicação. **Isso não é escopo do produto** (não estamos construindo CRM de marketing/anúncios), mas ajuda a entender por que a base é jovem e por que "poucos recorrentes" é esperado nesse estágio do negócio dela.

### ✅ Resolvido: despesa anual vs. mensal no dashboard
A taxa de vigilância sanitária é anual, não mensal. Decisão tomada: `fixed_expenses` ganhou o campo `periodicity` (MONTHLY | YEARLY, MVP v7.1 §12.5) — despesa anual entra ratada por 12 no cálculo de "Lucro real do mês", nunca pré-rateada manualmente pela profissional. Ver TASK-021a/021b atualizadas no backlog do backend.

---

## Incidente real de agenda — 2026-08-29 {#incidente-agendamento-2026-08-29}

Relatado por ela diretamente (via Thiago), fora do roteiro de perguntas: ela estava na rua, **duas clientes entraram em contato querendo marcar horário**. Ela não tem nenhum registro de agenda — nem caderno, nem app — e precisou parar, descrever de memória os horários já ocupados para o Gemini, pedir para ele montar uma imagem da agenda, e só então conseguiu responder no WhatsApp. Ela disse que um sistema de agenda **"ajudaria muito"**.

### Por que isso importa mais do que parece
Isso não é uma opinião hipotética ("você usaria agenda?") — é um incidente concreto e recente, com fricção mensurável (ela teve que parar o que fazia e recorrer a uma ferramenta de terceiros só para saber o que já estava ocupado). O MVP já previa uma Agenda mínima (EPIC-22, P0) — mas o escopo original (§16.3) assumia que todo horário nasce de uma venda já registrada (pacote ou avulso). O incidente real foi o oposto: **contato novo, sem venda, às vezes sem nem ser paciente cadastrada ainda**, só perguntando se tem horário.

### Decisão tomada
Adicionado o conceito de **agendamento provisório** (`bookings`, MVP v7.1 §16.6) — uma entidade nova e deliberadamente simples, sem preço nem procedimento obrigatório, separada de `Sale`/`Session` (não viola I5/I6 do `ENGENHARIA.md`). Ela pode reservar um horário na hora, mesmo sem cadastro completo da pessoa, e quando o atendimento realmente acontecer, a venda é registrada normalmente e o `booking` vira `CONVERTED` automaticamente — sem passo manual extra para lembrar.

Estados definidos: `SCHEDULED → CONVERTED | CANCELLED | NO_SHOW`.

Novas tasks: backend T-034a/T-034b, frontend F-019/F-019a. Nenhum código foi escrito ainda — só o desenho no MVP e o registro no backlog.

---

## Rodada 3 — pagamento e E7 — 2026-08-29 {#respostas-rodada-3-2026-08-29}

### ✅ E7 (antecipação) — resolvido, e era o último bloqueio crítico

Ela recebe **majoritariamente por Pix, cobrando por sessão** — nunca o pacote completo à vista. Tem Mercado Pago, mas evita: todas as parcelas têm juros (exceto 30 dias) e ela prefere assim **deliberadamente**, "para não movimentar muito na conta, dar mais confiança e ter noção do que está recebendo por mês".

Pix cai na hora → não existe recebível → **não há o que antecipar**. E7 permanece **P1**, como o plano original supunha. **A Fase 2 está destravada.**

### 🔍 A consequência que vale mais que o E7: "Lucro ≠ caixa" não se aplica a ela

A TASK-021 (§12) existe para prevenir um risco real: profissional que fatura no crédito parcelado vê "lucro do mês" e não tem esse dinheiro na conta. Mas no fluxo dela:

| Premissa da TASK-021 | Realidade dela |
|---|---|
| Crédito parcelado, D+30 | Pix, D+0 |
| Pacote cobrado à vista, sessões depois | Cobra por sessão, nunca o pacote completo |
| Recebível acumulado | Nenhum |

Competência e caixa **coincidem sempre**. "A receber" seria R$ 0,00 permanentemente.

**Decisão (MVP v7.1):** manter o cálculo de `expected_receipt_date` (é barato, correto, e o produto é vendido para um mercado — não para uma pessoa), mas **ocultar o widget "A receber" quando o valor for zero**. Uma linha que nunca muda ensina a usuária a ignorar aquela região da tela.

> ⚠️ **Risco de validação registrado:** a distinção competência-vs-caixa **não será exercitada** nos 30 dias de teste com a cliente zero. Se houver bug em `expected_receipt_date` para crédito parcelado, o uso real dela não vai revelar. Por isso esse caminho precisa de **teste automatizado**, não de confiança no uso.

### Preferência de fluxo de caixa é um achado de produto, não só um dado

"Prefere não movimentar muito na conta e **ter noção do que está recebendo por mês**" — ela escolhe o meio de pagamento em parte para conseguir *entender* o próprio faturamento. É a mesma dor que o produto ataca, resolvida hoje por ela com uma limitação auto-imposta no meio de pagamento. Vale lembrar disso ao escrever a landing/onboarding.

### Outros dados desta rodada
- **No-show ~20%, sem aviso** (confirma o número da rodada 2).
- **"Alguns pedem informações e não avançam"** — lead que não converte. Combinado com o incidente do Instagram (rodada 1: > 1 semana sem responder) e o incidente da agenda (rodada 3), sugere que responder rápido é um gargalo real. **Fora do escopo do MVP** (não é CRM de lead), mas é o segundo relato independente na mesma direção — anotar para o pós-validação.
- ✅ **Consulta online** — ela também atende online. **Financeiramente não exige nada:** é um `Procedure` do tipo `SERVICE` com custo estimado ~zero.
  - 🔧 **Revisto na mesma sessão:** o campo `modality` (IN_PERSON | REMOTE) **entrou** no modelo — não por razão financeira, mas operacional: a lista do dia precisa responder *"onde eu preciso estar"*. Default no `Procedure`, valor efetivo na `Session`/`booking` (um mesmo procedimento pode ser feito nos dois formatos). Ver MVP v7.1 §9 e §11.
  - 🚫 **O produto não gera link de videochamada.** Meet exigiria OAuth + Google Calendar API, já excluído em §16.4. O canal é combinado por ela na conversa que já existe com a paciente — WhatsApp, que ela já usa. Registrado com o alerta de posicionamento do §16.5: gerar sala de vídeo desliza o produto para "agendamento com telemedicina" e apaga o diferencial.

---

## ✅ Auditoria de cobertura — todas as respostas processadas

Conferência item a item contra o texto integral recebido, para garantir que nada ficou sem destino:

| Resposta dela | Onde foi parar |
|---|---|
| Aluguel, lixo biológico, água, luz, lanche | `fixed_expenses` MENSAL (MVP §12.5) |
| Taxa vigilância/prefeitura (anual) | `fixed_expenses` + campo `periodicity=YEARLY` (v7.1) |
| Custo com educação/cursos | `fixed_expenses` (categoria livre) |
| Anamnese anual, 30min, consulta separada p/ Botox | Visão Estágio 2 — **fora do MVP**, mas confirmada como demanda real |
| Venda de outros serviços durante o procedimento | Já suportado: é uma `Sale` avulsa registrada no atendimento |
| Botox: 30 dias na geladeira vs. bula | Contexto do `cost_override`; inventário fracionado é Estágio 3 |
| 35 avaliações Google, origem dos clientes, custo de anúncio | **Contexto de negócio, fora do escopo** — não é CRM de marketing |
| Fichas com telefone; primeiros clientes sem registro | Suportado: `patient.phone` é nullable |
| Poucos recorrentes / intervalo maior (3 mensal, 1 a cada 6 meses) | Confirma `return_interval_days` **por procedimento** |
| "Tem que lembrar o retorno, não voltam se não lembrar" | 🎯 **Valida a hipótese central** do motor de retorno (EPIC-10) |
| "Nunca fez o cálculo de ticket médio e lucro" | 🎯 **Valida a proposta de valor** do dashboard (EPIC-09) |
| Custo R$1.300/mês · lucro R$800/mês | Baseline T-050 (Bloco 5) |
| Acne 6 sessões × R$280 · pago por sessão | Modelo Sale/Session — cada sessão é uma venda |
| 5 recorrentes + 5 não-recorrentes · 50/50 acne/limpeza | Baseline T-050 |
| Consultas online | `Procedure` tipo SERVICE (MVP §9, v7.1) |
| Pix, por sessão, nunca o pacote completo | ✅ **Fecha E7** · oculta "A receber" quando zero (v7.1) |
| Mercado Pago com juros, prefere não usar | Contexto de E1/E4 — cartão é caminho raro |
| "Ter noção do que está recebendo por mês" | 🎯 Achado de posicionamento — landing/onboarding |
| ~20% de no-show sem aviso | Baseline · reforça F-041 (P1) |
| "Alguns pedem informações e não avançam" | Fora do escopo · 2º sinal de gargalo de resposta |

**Nenhum item ficou sem destino.** Os marcados 🎯 são os que reforçam decisões centrais do produto, não apenas configuração.
