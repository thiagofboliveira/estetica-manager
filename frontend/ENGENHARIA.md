# Guia de Engenharia — Frontend

Padrões específicos deste produto. Invariantes que atravessam os dois projetos: [../ENGENHARIA.md](../ENGENHARIA.md).

**Stack:** React 18 · TypeScript · Vite · TanStack Query v5 · React Hook Form + Zod

---

## As sete decisões

| # | Decisão | Motivo específico daqui |
|---|---|---|
| 1 | `Money = string & brand`; o front **nunca** recalcula lucro | Backend usa `Decimal` com taxas de 4 casas; o front não tem a fórmula |
| 2 | `Intl.NumberFormat.format(string)`, nunca `Number()` | Único ponto onde a precisão se perde na exibição |
| 3 | Máscara de centavos, `inputMode="numeric"`, `type="text"` | Teclado pt-BR + `type=number` = venda com valor zero |
| 4 | Prefixo `qk.financial()` → um `invalidate` cobre a cascata | Dashboard velho faz ela registrar a venda duas vezes |
| 5 | Idempotency-Key criada ao abrir o form | 4G do salão; `disabled` não sobrevive a isso |
| 6 | Zero optimistic update em valor em R$ | Lucro que muda depois de exibido destrói a confiança |
| 7 | Ação primária no rodapé, alvos ≥48px, inputs ≥16px | Uma mão, em pé, entre atendimentos |

---

## 1. Dinheiro sem float

### Por que `parseFloat` é bug — com número real

```ts
// Comissão de 40% sobre R$ 289,90, somada em 30 atendimentos do mês:
let t = 0; for (let i = 0; i < 30; i++) t += 115.96;
t                    // 3478.7999999999984   (esperado 3478.80)
t.toFixed(2)         // "3478.80"  ← o toFixed ESCONDE o erro
t === 3478.80        // false
```

Para ela isso é: *"meu lucro no app dá R$ 3.478,79 e no extrato dá R$ 3.478,80"*. Produto errado, fim da confiança. E `toFixed` não conserta — só arredonda a exibição enquanto o valor segue drifting.

### O tipo

```ts
// src/lib/money/money.ts
declare const MoneyBrand: unique symbol;
export type Money = string & { readonly [MoneyBrand]: "BRL" };

const MONEY_RE = /^-?\d+(\.\d{1,2})?$/;

/** Única porta de entrada — valida o que o backend promete. */
export function money(raw: string): Money {
  if (!MONEY_RE.test(raw)) throw new TypeError(`Money inválido: ${JSON.stringify(raw)}`);
  return raw as Money;
}

const d = (m: Money) => new Decimal(m);
const out = (x: Decimal): Money => x.toFixed(2) as Money;

export const add = (a: Money, b: Money): Money => out(d(a).plus(d(b)));
export const sum = (xs: readonly Money[]): Money =>
  out(xs.reduce((acc, m) => acc.plus(d(m)), new Decimal(0)));
export const cmp = (a: Money, b: Money): -1 | 0 | 1 => d(a).comparedTo(d(b)) as -1 | 0 | 1;
```

### O furo do branded string — e as duas defesas

```ts
preco * 2;        // ❌ TS bloqueia (não é number)
preco + custo;    // ⚠️ TS PERMITE → "289.90150.00"
```

`string + string` compila. Duas defesas:

```js
// 1) ESLint em src/features/**
"no-restricted-syntax": ["error", {
  selector: "BinaryExpression[operator='+']",
  message: "Use add() de lib/money — nunca + em Money."
}]
```

```ts
// 2) Ordenação — armadilha silenciosa
["9.00", "10.00"].sort();              // ["10.00", "9.00"] ← lexicográfica!
[a, b].sort((x, y) => cmp(x, y));      // ✅
```

> 🔴 **Onde isso morde:** F-015a ordena "Quem devo chamar hoje?" por valor potencial. Com `sort()` padrão, R$ 9,00 aparece acima de R$ 1.200,00 e ela liga para a paciente errada.

### Formatação

`Intl.NumberFormat.format()` aceita **string** e a trata como decimal exato.

```ts
const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
export const formatBRL = (m: Money) => BRL.format(m as unknown as string);

// A prova de que a string importa:
// BRL.format("9007199254740993.45")          → exato
// BRL.format(Number("9007199254740993.45"))  → ...992,00  ❌
```

Instancie **uma vez** no módulo — criar `NumberFormat` em render é ~100x mais lento.

### Input de moeda

Padrão de caixa de supermercado: acumula dígitos da direita. Ela digita `2`,`8`,`9`,`9`,`0` e vê `R$ 289,90`. Sem vírgula, sem cursor, sem separador para gerenciar.

```tsx
const digits = raw.replace(/\D/g, "").slice(0, 9);
const cents = Math.min(digits ? parseInt(digits, 10) : 0, MAX_CENTS);
onChange(centsToMoney(cents));   // sai Money, nunca number
```

```tsx
<input
  type="text"           // NÃO type="number": traz spinners e rejeita a máscara
  inputMode="numeric"   // NÃO "decimal": traz vírgula que ela não precisa
  pattern="[0-9]*"
  onFocus={(e) => e.currentTarget.select()}
/>
```

> 🔴 **O bug clássico:** `type="number"` + teclado pt-BR. Ela digita `289,90`, o browser devolve `""` porque vírgula é inválida, e a venda é registrada com **valor zero**.

---

## 2. React Query

### Três perfis de cache

```ts
export const CACHE = {
  MONEY:    { staleTime: 0,           gcTime: 5 * 60_000 },   // dashboard, retenção
  CATALOG:  { staleTime: 5 * 60_000,  gcTime: 30 * 60_000 },  // procedimentos
  SETTINGS: { staleTime: 10 * 60_000, gcTime: 60 * 60_000 },  // taxas
  SEARCH:   { staleTime: 30_000,      gcTime: 60_000 },       // busca de paciente
} as const;
```

`refetchOnWindowFocus: true` é o que faz ela ver o número certo ao voltar do WhatsApp para o app.

> ⚠️ **`financial-settings` parece cacheável mas é input do lucro.** Se ela mudar a taxa em outra aba e o dashboard usar a antiga, o lucro fica errado sem nenhum sinal. Ao salvar settings, invalide tudo sob `qk.financial()`.

> 🔴 **Não use `staleTime` global "para economizar requisição".** Ela registra uma venda, volta ao dashboard, o lucro não subiu, ela registra de novo. Agora há duas vendas.

### Query keys desenhadas para a invalidação

```ts
export const qk = {
  all: ["app"] as const,
  // Tudo que depende de dinheiro sob o mesmo prefixo → um invalidate resolve
  financial: () => [...qk.all, "financial"] as const,
  dashboard: (r: Range) => [...qk.financial(), "dashboard", r] as const,
  retention: () => [...qk.financial(), "retention"] as const,
  packages:  () => [...qk.financial(), "packages"] as const,
  sessions:  () => [...qk.financial(), "sessions"] as const,
  // Cadastros ficam FORA: venda não invalida catálogo
  patients:   () => [...qk.all, "patients"] as const,
  procedures: () => [...qk.all, "procedures"] as const,
} as const;
```

### Cascata em um lugar só

```ts
export async function invalidateAfterSale(patientId: string) {
  await Promise.all([
    // Cobre dashboard + retention + packages + sessions de uma vez
    queryClient.invalidateQueries({ queryKey: qk.financial(), refetchType: "active" }),
    queryClient.invalidateQueries({ queryKey: qk.patientDetail(patientId) }),
  ]);
}

export async function invalidateAfterScheduling() {
  await queryClient.invalidateQueries({ queryKey: qk.packages() });
  await queryClient.invalidateQueries({ queryKey: qk.sessions() });
  // Dashboard NÃO muda: agendar não gera receita.
  // Não invalide o que não mudou — refetch no 4G custa 2s de tela cinza.
}
```

> 🔴 **O sintoma de esquecer:** o card continua dizendo "chamar Maria" depois que Maria já comprou hoje.

### Idempotency key

```ts
export function useCreateSale() {
  // Nasce ao ABRIR o form. Sobrevive a re-render, retry e duplo-toque.
  // Só troca depois de sucesso confirmado.
  const idemKey = useRef(crypto.randomUUID());

  return useMutation({
    mutationFn: (input) => api.post("/sales", input, {
      headers: { "Idempotency-Key": idemKey.current },
    }),
    onSuccess: async (_sale, vars) => {
      idemKey.current = crypto.randomUUID();
      await invalidateAfterSale(vars.patientId);
    },
  });
}
```

> 🔴 **Erro que anula a proteção:** gerar o UUID dentro de `mutationFn`. Cada retry cria chave nova — exatamente o cenário do 4G instável que a idempotência deveria cobrir.

**Contrato que o backend precisa honrar (alinhar em T-015):** mesma chave + mesmo corpo → **200 com a venda existente**, não 409, não duplica.

### Optimistic update — a regra

> **Nada que exiba valor em reais recebe optimistic update.**

O front não conhece a fórmula do lucro (depende de E1/E2/E4, ainda abertos). Um "lucro: R$ 231,92" que vira R$ 187,44 quando o servidor responde não é glitch de UI — é o produto mentindo sobre quanto ela ganhou, na tela que é o momento de valor.

| Ação | Optimistic? | Por quê |
|---|---|---|
| `POST /sales` | ❌ Nunca | Lucro vem do servidor |
| Agendar sessão (F-018a) | ✅ Sim | Só muda status, zero dinheiro |
| Marcar contato (F-015c) | ✅ Sim | Booleano local |
| Editar settings | ❌ Não | Muda o lucro de todo o histórico |

No único caso aceitável, `cancelQueries` é obrigatório — senão um refetch em voo sobrescreve o otimismo:

```ts
onMutate: async (v) => {
  await qc.cancelQueries({ queryKey: qk.packagesOpen() });
  const prev = qc.getQueryData(qk.packagesOpen());
  qc.setQueryData(qk.packagesOpen(), (old) => /* ... só status ... */);
  return { prev };   // ⚠️ NÃO toque em campos Money aqui
},
onError: (_e, _v, ctx) => { if (ctx?.prev) qc.setQueryData(qk.packagesOpen(), ctx.prev); },
```

---

## 3. Formulário de venda — os 30 segundos

Orçamento: paciente 8s · procedimento 5s · valor 6s · pagamento 3s · submit 4s · folga 4s. **Cada campo extra custa ~4s** — por isso a tela de pacote (F-014b) é separada.

### Zod validando string, não number

```ts
const moneySchema = z.string()
  .regex(/^\d+\.\d{2}$/, "Valor inválido")
  .refine((s) => new Decimal(s).gt(0), "Informe um valor maior que zero")
  .transform((s): Money => money(s));   // transform aplica o BRAND, não converte
```

> 🔴 **`z.coerce.number()` no valor** passa em todo teste e corrompe centavos em produção. O schema, que deveria ser a barreira, vira a fonte do bug.

### Detalhes que compram segundos

```tsx
useForm({
  mode: "onSubmit",          // NÃO onChange: erro vermelho enquanto digita, em pé, atrapalha
  reValidateMode: "onChange",
  defaultValues: {
    occurredAt: new Date().toISOString(),   // hoje por default
    paymentMethod: "PIX",
  },
});

// Enter em qualquer campo submete — sem isso ela precisa alcançar o rodapé com uma mão
<form onKeyDown={(e) => {
  if (e.key === "Enter" && e.target instanceof HTMLInputElement) {
    e.preventDefault(); onSubmit();
  }
}}>

// Ao escolher a paciente, pula direto para o valor
// (procedimento tem default = o último usado)
<PatientCombobox onSelected={() => valueRef.current?.focus()} />
```

### Duplo-submit — três camadas

```tsx
<button
  disabled={isPending}                                    // 1: UX
  onPointerDown={(e) => { if (isPending) e.preventDefault(); }}  // 2: ghost tap do iOS
  // 3: Idempotency-Key — a única que sobrevive a rede instável
/>
```

`retry: 0` em mutations no `queryClient`. Retry automático em mutation não-idempotente cria vendas duplicadas.

### Combobox

```tsx
const deferred = useDeferredValue(q);   // menos código que useDebounce, input nunca engasga

useQuery({
  queryKey: qk.patientsSearch(deferred),
  enabled: deferred.trim().length >= 2,
  placeholderData: keepPreviousData,    // sem isso a lista pisca vazia a cada letra
  ...CACHE.SEARCH,
});
```

```tsx
// onPointerDown, NÃO onClick: no mobile o blur fecha a lista antes do click resolver
<li onPointerDown={(e) => { e.preventDefault(); commit(p); }}>
  <strong>{p.name}</strong>
  <span>{p.phone?.slice(-4)}</span>   {/* desambigua duas "Maria Silva" */}
</li>

// Enter escolhe a paciente e NÃO submete o form
if (e.key === "Enter" && results[active]) { e.preventDefault(); e.stopPropagation(); }
```

Empty state acionável: `Cadastrar "{q}"` sem sair da tela — senão ela perde os 30s navegando.

---

## 4. Auth

O SDK do Supabase guarda a sessão em `localStorage`. **Refresh token ali é a exposição real** — um XSS rouba um token que renova sozinho.

Para o MVP: manter o SDK padrão, com mitigação séria. O que protege de verdade:

- **CSP estrita** — `script-src 'self'`, sem `unsafe-inline`, sem CDN de terceiro
- **Zero `dangerouslySetInnerHTML`** — nome de paciente é input não confiável
- **`flowType: "pkce"`** — nunca implicit (não põe token na URL)
- **RLS no Postgres** (T-058) é a defesa final

```ts
// Deduplica refresh concorrentes: 5 queries paralelas = 1 refresh, não 5
let refreshing: Promise<string | null> | null = null;

if (res.status === 401 && !isRetry) {
  const renewed = await freshToken(true);
  if (renewed) return request<T>(path, opts, true);   // isRetry corta o loop
  await supabase.auth.signOut();
  // Guarda o destino: perder o form de venda meio preenchido mata os 30 segundos
  sessionStorage.setItem("returnTo", location.pathname);
  location.assign("/login");
}
```

> ⚠️ **Nunca guarde o JWT manualmente em paralelo ao SDK.** As duas cópias divergem no refresh e a requisição sai com token expirado enquanto o SDK acha que está logado.

Fetch nativo em vez de axios: 13 kB a menos, `AbortSignal` do React Query funciona direto.

---

## 5. Estrutura

Feature-first. Layer-first obriga a tocar 4 pastas para uma mudança.

```
src/
├─ app/          router, providers, layout
├─ features/     sales, dashboard, retention, patients,
│                procedures, packages, schedule, settings, onboarding
├─ lib/          money, query, http, auth   ← zero import de features
├─ ui/           primitivos: Button, Chip, AsyncBoundary, EmptyState
└─ types/        api.gen.ts + api.ts
```

Regra de dependência (vale um lint): `features/*` importa de `lib/` e `ui/`, **nunca** de outra feature. Se `retention` precisa do card de paciente, ele sobe para `ui/`.

`lib/money/` não importa React — é o que a torna testável e faz a regra da string ter um lugar único onde é obrigada.

### Tipos do backend

FastAPI expõe `/openapi.json`. Gere, mas com um ajuste: o Pydantic serializa `Decimal` como string, e o gerador produz `string` — você perde o brand.

```ts
type WithMoney<T, K extends keyof T> = Omit<T, K> & { [P in K]: Money };
export type Sale = WithMoney<RawSale, "grossAmount" | "netAmount" | "profit">;
```

Teste de contrato no CI:

```ts
it("campos monetários seguem como string", async () => {
  const spec = await fetch(`${API}/openapi.json`).then(r => r.json());
  for (const f of ["grossAmount", "netAmount", "profit"]) {
    expect(spec.components.schemas.SaleResponse.properties[f].type).toBe("string");
  }
});
```

> 🔴 **O que isso pega:** o backend trocar `Decimal` por `float` num refactor. Sem o teste, o desvio aparece meses depois no fechamento, sem sinal de onde veio.

---

## 6. Estados de UI

### Empty state importa desproporcionalmente aqui

A primeira sessão dela é **100% tela vazia** — zero pacientes, zero vendas, dashboard zerado. Ela é não-técnica e não tem a quem pedir ajuda. "Nenhum resultado encontrado" lê como **produto quebrado**.

Três variantes, e a diferença entre elas é o produto:

| Tom | Quando | Exemplo |
|---|---|---|
| `first-run` | Nunca houve dado | "Registre sua primeira venda e eu mostro quanto sobrou pra você." + CTA |
| `good` | Vazio é boa notícia | "Ninguém para chamar hoje." — sem CTA |
| `filtered` | Há dados, o filtro escondeu | "Nenhuma venda em agosto." + [Ver julho] |

> 📌 **Peça `hasAnyData` no `GET /dashboard` (T-022).** É 1 booleano que distingue "primeira vez" de "mês sem venda" — e muda a primeira impressão do produto inteiro.

### Skeleton, não spinner

```tsx
// Rótulo REAL, só o número carregando. Altura FIXA = zero layout shift.
<span className="card__label">Faturamento</span>
<div className="skeleton" style={{ height: "2rem", width: "7ch" }} />
```

> 🔴 **Por que layout shift importa aqui:** se o número aparece e empurra os cards, o polegar dela — que já ia em direção a "Registrar venda" — acerta outro botão. Em pé, com uma mão, isso acontece.

Refetch com dado em cache: **mantenha os números na tela**, barra fina no topo. Ela não quer ver a tela desmontar ao voltar do WhatsApp.

```css
@media (prefers-reduced-motion: reduce) { .skeleton { animation: none; } }
```

---

## 7. Mobile — uma mão, em pé

```
┌─────────────────┐
│  ✗ inalcançável │  ← título, valor total (LER, não tocar)
│  ~ esticando    │  ← campos do formulário
│  ✓ ZONA FÁCIL   │  ← TODA ação primária mora aqui
└─────────────────┘
```

```css
:root {
  --tap: 48px;           /* WCAG pede 24px; mobile real pede 48 */
  --tap-primary: 56px;   /* ações de dinheiro: maiores */
}

.action-bar {            /* ancorada no rodapé, acima do gesture bar */
  position: sticky; bottom: 0;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
}

.danger { margin-top: 32px; }   /* longe da primária: excluir venda por engano
                                   com o polegar é perda de dado financeiro */

input, select, textarea { font-size: 16px; }   /* NUNCA menos */
```

> 🔴 **16px é regra, não sugestão.** Abaixo disso o Safari iOS dá zoom ao focar, e ela precisa fazer pinch para voltar — mata os 30 segundos no meio do atendimento.

Chips em vez de `<select>`: picker nativo custa 3 toques, chip custa 1.

```tsx
<input inputMode="numeric" pattern="[0-9]*" />       {/* valor */}
<input inputMode="text" autoCapitalize="words" spellCheck={false} />  {/* nome */}
<input type="tel" inputMode="tel" autoComplete="tel-national" />      {/* telefone */}
```

`spellCheck={false}` no nome: sublinhado vermelho em nome próprio parece erro dela.

```ts
// Feedback háptico na confirmação — ela olha para a paciente, não para a tela
if ("vibrate" in navigator) navigator.vibrate(30);
```

```css
/* Teclado virtual cobrindo o submit é a falha #1 em form mobile */
@viewport { interactive-widget: resizes-content; }
.form-page { min-height: 100dvh; display: flex; flex-direction: column; }
```

---

## Dois pedidos ao backend

Vieram desta análise e precisam entrar no contrato:

1. **Idempotência do `POST /sales`** (T-015) — mesma chave + mesmo corpo → 200 com a venda existente. Sem isso, F-014a tem só o `disabled`, que não sobrevive ao 4G.
2. **`hasAnyData` no `GET /dashboard`** (T-022) — 1 booleano, muda a primeira impressão do produto.

---

## Checklist de PR

- [ ] Nenhum `parseFloat`/`Number()` em valor monetário
- [ ] Nenhum `+` entre `Money` (use `add`)
- [ ] Ordenação de valores usa `cmp`, não `sort()` padrão
- [ ] Mutation que cria venda tem Idempotency-Key
- [ ] Invalidação cobre todas as telas afetadas
- [ ] Sem optimistic update em valor em R$
- [ ] Empty state distingue first-run de filtered
- [ ] Inputs com `font-size: 16px`, alvos ≥48px
- [ ] Testado contra a API real, não mock
