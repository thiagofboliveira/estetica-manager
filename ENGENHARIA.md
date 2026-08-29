# Guia de Engenharia — Invariantes do Domínio

Regras que atravessam backend e frontend. Cada uma existe porque **algo concreto quebra** se for violada — não por preferência estética.

Guias específicos: [backend/ENGENHARIA.md](backend/ENGENHARIA.md) · [frontend/ENGENHARIA.md](frontend/ENGENHARIA.md)

---

## As sete invariantes

Se você só ler uma seção deste repositório, leia esta.

| # | Invariante | O que quebra se violar |
|---|---|---|
| **I1** | Dinheiro nunca é float | Centavo órfão no fechamento do mês; meta "erros financeiros ~0" falha |
| **I2** | `professional_id` vem só do JWT | Vazamento de dado de saúde entre concorrentes — evento de extinção |
| **I3** | Snapshot congelado é imutável | Mudar taxa hoje altera o lucro de março; histórico irreproduzível |
| **I4** | Toda data é `TIMESTAMPTZ` em UTC | Venda das 21h cai no dia seguinte; erro aparece no fechamento |
| **I5** | Dinheiro vive na `Sale`, nunca na `Session` | Pacote conta receita 10x ou some do faturamento |
| **I6** | Oportunidade de retorno nasce só em `COMPLETED` | Oportunidades órfãs de vendas que não aconteceram |
| **I7** | Número estimado é exibido como estimado | Profissional decide preço com número errado que parecia certo |

---

## I1 — Dinheiro nunca é float

**A regra:** `NUMERIC(12,2)` no banco → `Decimal` no Python → **string** no JSON → `decimal.js`/centavos no TS.

O elo mais frágil é o JSON. `number` em JavaScript é float64: se o backend faz tudo certo com `Decimal` e o front faz `parseFloat`, o erro volta.

```
1000 × 0.30 em float64  →  300.00000000000006
Somado 200 vezes        →  divergência visível de centavos
```

**Por que importa aqui:** o produto vende clareza financeira e mede "erros financeiros ~0". Uma divergência de R$ 0,01 entre o dashboard e a soma das linhas destrói a confiança de forma desproporcional ao dano — e só aparece com volume, ou seja, depois de vendido.

**Onde é fácil errar:** rateio de desconto entre itens de pacote. A soma das partes precisa fechar exatamente com o total; o último item absorve o resto da divisão.

---

## I2 — `professional_id` vem só do JWT validado

**A regra:** o tenant é derivado do claim `sub`. Nunca de query param, header customizado, body ou path.

```
✅  professional_id = claim "sub" do JWT (assinatura verificada)
❌  professional_id = request.query_params["professional_id"]
❌  professional_id = request.headers["X-Professional-Id"]
```

Defesa em profundidade, quatro camadas:

1. **RLS no Postgres** — `SET LOCAL app.professional_id` por transação. Torna o vazamento impossível no banco mesmo com bug na aplicação.
2. **Repository exige tenant** no construtor; nenhum repo expõe query crua.
3. **Teste genérico** que enumera todas as rotas e verifica 404 cross-tenant.
4. **UUID como PK** — um vazamento por ID exige adivinhar um UUID.

**Por que importa aqui:** dados de estética são sensíveis (LGPD Art. 5º, II). O produto é vendido por indicação entre colegas — muitas vezes da mesma clínica. Um vazamento entre duas profissionais concorrentes encerra o produto.

---

## I3 — Snapshot congelado é imutável

**A regra:** ao concluir uma venda, os valores usados no cálculo são copiados para a `Sale` e nunca mais recalculados a partir das configurações atuais.

Congelam: `list_price`, `split_applied`, `split_base_applied`, `fee_payer_applied`, `fee_applied`, `cost_applied`, `return_interval_applied`.

Repare que **a fórmula também congela**, não só os percentuais. Se a profissional mudar de "split sobre bruto" para "split sobre líquido", as vendas antigas precisam continuar reproduzindo o número original.

**Ao editar uma venda histórica:** recalcule com a configuração **do momento original**, não com a de hoje.

**A única exceção:** `cost_realized` muda quando sessões de um pacote são concluídas ou expiram. Isso é por design (§12.1 do MVP) — e por isso vendas com sessões pendentes são exibidas como "lucro provisório".

---

## I4 — Toda data é `TIMESTAMPTZ` em UTC

**A regra:** armazene em UTC, converta para `professionals.timezone` **antes** de agrupar por dia ou mês.

```sql
-- ✅ converte antes de truncar
date_trunc('day', s.sold_at AT TIME ZONE p.timezone)

-- ❌ trunca em UTC
date_trunc('day', s.sold_at)
```

**Três falhas concretas que isso evita:**
- Venda às 21h em São Paulo vira 00h do dia seguinte em UTC — e o erro aparece no fechamento do dia, exatamente quando ela olha.
- Cron de lembrete dispara com 3h de defasagem, mandando WhatsApp de madrugada.
- Corte de "este mês" erra as vendas do último dia.

**Exceção deliberada:** `return_opportunities.due_date` é `DATE`, não timestamp. Retorno é um dia civil, não um instante — usar `DATE` elimina a classe inteira de bugs.

---

## I5 — Dinheiro vive na `Sale`, nunca na `Session`

**A regra:** `Sale` é a unidade de dinheiro; `Session` é a unidade de serviço. Sessão não tem preço.

```
Sale (R$ 2.000, PACKAGE)
 └── SaleItem (Limpeza ×10, unit_price R$ 200)
      └── Session ×10   ← sem valor financeiro
```

Se você sentir vontade de colocar `price` em `Session`, o modelo está sendo violado.

**Corolário — cada métrica declara sua base:**

| Métrica | Base |
|---|---|
| Faturamento, lucro, margem, ticket médio | **Venda** |
| Nº de atendimentos, ocupação | **Sessão** |
| Ranking de procedimentos | **Item** (com desconto rateado) |

Num mês com um pacote vendido: "3 vendas, 12 atendimentos". Os dois números estão certos — a UI precisa rotular, senão parece bug.

---

## I6 — Oportunidade de retorno nasce só em `COMPLETED`

**A regra:** gere a oportunidade na transição para `COMPLETED` (e `NO_SHOW` — paciente em risco). Nunca em `SCHEDULED`.

E para pacote: a oportunidade nasce quando **o item se esgota**, contando da última sessão. Um pacote de 10 gera **uma** oportunidade, não dez.

**Enquanto houver sessão `PENDING`**, a paciente não aparece na lista de reativação daquele procedimento — ela tem saldo. O que ela precisa é de agendamento, não de reativação. São listas diferentes.

**Fechamento acontece na venda, não na sessão:** o que resolve uma oportunidade é a paciente *comprar de novo*. Se ela comprou 10 limpezas, a reativação teve sucesso hoje — não daqui a 10 sessões.

---

## I7 — Número estimado é exibido como estimado

**A regra:** se um valor foi calculado com default de mercado, custo estimado ou configuração não confirmada, isso aparece na tela.

| Situação | Rótulo |
|---|---|
| Taxa vinda do seed, não confirmada | "taxa estimada" |
| Custo do procedimento, sem `cost_override` | "custo estimado" |
| Pacote com sessões pendentes | "lucro provisório" |
| Parcelamento não modelado ainda | "não considera parcelamento" |

**Por que é invariante e não polimento:** o produto vende confiança em números. Um número errado com aparência de certo é pior que nenhum número — leva a uma decisão de precificação errada tomada com confiança. É o segundo corolário do princípio de produto: *"um número errado é pior que nenhum número"*.

---

## Convenções de projeto

### Nomenclatura

| Camada | Idioma | Exemplo |
|---|---|---|
| Banco, código, API | **Inglês** | `sales`, `return_opportunities`, `net_profit` |
| UI, mensagens ao usuário | **Português** | "Lucro real", "Quem devo chamar hoje?" |

Não misture. `vendas` no banco e `Sale` no código é o começo do caos.

### Commits

```
feat(sales): adiciona rateio de desconto por item
fix(retention): oportunidade duplicada em paciente multi-procedimento
test(financial): matriz de 5 configurações
```

Escopos: `sales`, `retention`, `financial`, `patients`, `procedures`, `auth`, `agenda`, `infra`.

### Definition of Done

Uma task só é `[x]` quando:

- [ ] Teste automatizado cobre o caminho principal
- [ ] Nenhuma invariante acima foi violada
- [ ] Se toca dinheiro: passa na matriz de configuração (T-044)
- [ ] Se toca dado de paciente: respeita RLS e foi testado cross-tenant
- [ ] Rodou contra a API/banco real, não mock

---

## Ordem de leitura para quem chega

1. Este arquivo (invariantes)
2. [MVP v6](MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) §11 (modelo) e §12 (motor de lucro)
3. Guia do seu projeto: [backend](backend/ENGENHARIA.md) ou [frontend](frontend/ENGENHARIA.md)
4. [BACKLOG.md](BACKLOG.md)
