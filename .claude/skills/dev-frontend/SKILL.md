---
name: dev-frontend
description: Use when writing or modifying React/TypeScript frontend code in the Estética Manager project — screens, components, forms, TanStack Query hooks, money formatting, CSS Modules, or frontend routing
---

# DEV Frontend — React 19 · TypeScript · Vite · TanStack Query

**Stack:** React 19 · TypeScript · Vite 6 · TanStack Query v5 · React Hook Form + Zod · CSS Modules · PWA

**Referência completa:** [frontend/ENGENHARIA.md](../../../frontend/ENGENHARIA.md) (as sete decisões) e [ENGENHARIA.md](../../../ENGENHARIA.md) (invariantes I1-I7). Esta skill é o resumo operacional.

## A regra nº 1: dinheiro nunca vira `number`

`number` em JS é float64. Se o backend faz tudo certo com `Decimal` e o front faz `parseFloat`, **o erro volta**.

```ts
import { money, add, sum, mulQty, cmp, formatBRL, type Money } from "@/lib/money";

// ✅ Money é branded string; opere com os helpers
const total: Money = sum(itens.map(i => i.subtotal));
const comQtd = mulQty(preco, 4);
const ordenado = [...vendas].sort((a, b) => cmp(b.valor, a.valor));
formatBRL(total);   // "R$ 1.100,00"

// ❌ TODOS estes reintroduzem o bug que o backend evitou
parseFloat(valor)            // float64
Number(valor)                // float64
valorA + valorB              // concatena string ou vira float
[...vendas].sort()           // ordem lexicográfica: "1000" < "200"
valor.toFixed(2)             // já é string, e arredonda em float
```

**Nunca calcule lucro no cliente.** O lucro vem da resposta da API (`net_profit`). Já houve um `prototypeMath.ts` neste projeto calculando lucro no front — foi **deletado** de propósito. Um simulador de preço chama o backend (`POST /simulate/price`), não replica a fórmula.

Helpers disponíveis: `money`, `tryMoney`, `rate`, `ZERO`, `add`, `sub`, `sum`, `mulQty`, `applyRate`, `isNegative`, `isZero`, `cmp`, `moneyToCents`, `centsToMoney`, `formatBRL`, `formatRate`.

## TanStack Query — perfis de cache

```ts
import { CACHE } from "@/lib/query/client";

CACHE.MONEY     // staleTime 0     — dashboard, vendas: sempre fresco
CACHE.CATALOG   // staleTime 5min  — procedimentos
CACHE.SETTINGS  // staleTime 10min — configurações financeiras
CACHE.SEARCH    // staleTime 30s   — busca de paciente
```

Valor em R$ **nunca** vem de cache stale. Número desatualizado com aparência de atual é o mesmo pecado do I7.

### Invalidação em um lugar só

Use os helpers de cascata (`invalidateAfterSale`, `invalidateAfterScheduling`) — não invalide chave por chave espalhado pelos componentes. Venda nova afeta dashboard, ranking, retenção, agenda e pacotes; esquecer um deles é bug silencioso.

### Optimistic update — a regra

```ts
// ✅ permitido: campo não-monetário (status, confirmação)
onMutate: async (id) => {
  await queryClient.cancelQueries({ queryKey: [...qk.sessions(), "unconfirmed"] });
  const previousData = queryClient.getQueryData([...]);
  queryClient.setQueryData([...], old => /* ... */);
  return { previousData };   // rollback no onError
}

// ❌ PROIBIDO: qualquer valor em R$
// Mostrar um lucro otimista que a API contradiz destrói a confiança no número
```

### Idempotency key em venda

`useCreateSale` gera a chave em `useRef` ao montar o form e só troca **após sucesso**. Mesma chave + mesmo corpo → 200 com a venda existente. `disabled` no botão não sobrevive ao 4G do salão.

## Query desabilitada mente sobre loading

Bug real deste projeto, que vai repetir: filtro que desabilita a query condicionalmente deixa a tela presa em "Carregando…" para sempre, porque `enabled: false` nunca resolve `isPending` e o `AsyncBoundary` não distingue os dois casos.

```tsx
// ✅ trate o caso "desabilitada" ANTES do boundary
{period === "custom" && !(dateFrom && dateTo) ? (
  <p>Escolha as duas datas para ver o período.</p>
) : (
  <AsyncBoundary query={query}>{/* ... */}</AsyncBoundary>
)}
```

## Erros da API

Todo endpoint do backend devolve `{"detail": "mensagem"}` (`HTTPException` do FastAPI). O `client.ts` lê `body.detail`. Se você criar outro caminho de erro, respeite esse contrato — já houve um bug onde toda tela mostrava só o fallback genérico.

## Estados de UI

**Empty state distingue first-run de filtrado.** Use `has_any_data` do `GET /dashboard` (contrato C-2):

| `has_any_data` | Período vazio | Mensagem |
|---|---|---|
| `false` | — | "Registre a primeira venda para ver o dashboard" |
| `true` | sim | "Nenhuma venda neste período" + métricas zeradas |

A primeira sessão é **toda** tela vazia — é onde a ativação é ganha ou perdida.

**Rótulo de estimativa é obrigatório (I7).** Taxa não confirmada → "taxa estimada". Pacote com sessões pendentes → "lucro provisório" (`has_provisional_profit`). Custo sem override → "custo estimado".

**Métrica declara a base.** "3 vendas, 12 atendimentos" não é bug — venda e sessão são unidades diferentes. Rotule, ou parece inconsistência.

## Mobile — uma mão, em pé

Ela trabalha em pé com o celular. **Não é polimento, é o meio de acesso principal.**

- `font-size: 16px` em inputs (menos que isso, iOS dá zoom)
- Alvos de toque ≥ 48px (`.tap-target`)
- Testar em viewport real de 360-390px
- Ícone **+ texto**, nunca só cor (modalidade presencial vs. remoto)

## Estrutura e estilo

```
src/features/<dominio>/
  api.ts        # chamadas HTTP
  hooks.ts      # useQuery/useMutation
  <X>Page.tsx   # rota
  <X>Form.tsx   # formulário
  <X>.module.css
```

**Componente novo usa CSS Modules** (`.module.css`), não CSS global. O `index.css` guarda só tokens e utilities base.

Zod valida **string**, não `number`, em campo monetário.

## Verificação

```bash
npx tsc -b            # tipos
npm run lint          # oxlint
npm run dev           # localhost:5173 (backend em 8010)
```

**`[x]` exige teste contra a API real**, não mock. Clique na tela, depois confirme no Postgres:

```bash
docker exec estetica-postgres-dev psql -U postgres -d estetica -c "SELECT * FROM sales ORDER BY created_at DESC LIMIT 3;"
```

Dev sem Supabase: `VITE_DEV_AUTH=true` no `.env.local` → botão "Entrar com Conta de Teste".

## Checklist de PR

- [ ] Nenhum `parseFloat`/`Number()`/`toFixed()` em valor monetário
- [ ] Nenhum `+` entre `Money` (use `add`/`sum`)
- [ ] Ordenação de valores usa `cmp`, não `sort()` padrão
- [ ] Nenhum lucro calculado no cliente
- [ ] Mutation que cria venda tem Idempotency-Key
- [ ] Invalidação cobre todas as telas afetadas
- [ ] Sem optimistic update em valor em R$
- [ ] Query condicional trata o caso "desabilitada" antes do boundary
- [ ] Empty state distingue first-run de filtrado
- [ ] Número estimado tem rótulo (I7)
- [ ] Inputs com `font-size: 16px`, alvos ≥48px
- [ ] CSS Modules em componente novo
- [ ] `tsc -b` limpo e testado contra API real

## Red Flags — pare

- "É só para exibir, `Number()` resolve" → **não. `formatBRL(money(x))`**
- "Calculo o total no front para o preview" → **soma com `sum()`; lucro só da API**
- "Optimistic update deixa o lucro instantâneo" → **proibido em R$**
- "`sort()` já ordena" → **lexicográfico: "1000" < "200"**
- "O empty state é igual nos dois casos" → **use `has_any_data`**
- "Mobile depois, é polimento" → **é o meio de acesso principal**
- "Testei com mock, funciona" → **`[x]` exige API real**
- Tela nova em `PlaceholderPage` marcada como pronta → **não está pronta**
