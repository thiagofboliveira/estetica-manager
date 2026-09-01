# Backlog Sprint 2 — Frontend

Sprint focada em **validação de mercado e go-to-market**, derivada da análise de produto PO/PM (2026-08-31).
Todas as features endereçam riscos concretos identificados na entrevista com a Cliente Zero.

## 📊 Progresso Geral

- **Total de Tarefas:** 22 implementadas + 4 ações corretivas pendentes
- **Aprovadas no Code Review:** 18/22 (82%)
- **Ações Corretivas Pendentes:** 4

---

## EPIC-S2-01: Widget de ROI — Receita Recuperada pelo Sistema

*Card proeminente no dashboard mostrando quanto o sistema devolveu em receita. É o que justifica a assinatura.*

### Tarefas

- [x] `[FRONT-S2-01]` **API Layer: `dashboardApi.getRoi()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-02]` **Hook: `useROI()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-03]` **Componente: `<ROICard />`** — 🐛 **BUG — ver AC-03**
- [x] `[FRONT-S2-04]` **Integração no `DashboardPage.tsx`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-05]` **CSS Module: `ROICard.module.css`** — ✅ Aprovado no review.

---

## EPIC-S2-02: Anti-No-Show — Lembretes D-1

*Seção na agenda mostrando sessões de amanhã não confirmadas, com 1-tap para enviar lembrete via WhatsApp.*

### Tarefas

- [x] `[FRONT-S2-06]` **API Layer: `agendaApi.getUnconfirmed()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-07]` **API Layer: `agendaApi.confirmSession()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-08]` **Hooks: `useUnconfirmedSessions()` e `useConfirmSession()`** — ⚠️ **PARCIAL — ver AC-05**
- [x] `[FRONT-S2-09]` **Componente: `<NoShowAlert />`** — ⚠️ **PARCIAL — ver AC-06**
- [x] `[FRONT-S2-10]` **Botão "Marcar como Confirmada"** — ✅ Aprovado no review.
- [x] `[FRONT-S2-11]` **Integração na `AgendaPage.tsx`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-12]` **CSS Module: `NoShowAlert.module.css`** — ✅ Aprovado no review.

---

## EPIC-S2-03: Importação em Lote de Pacientes (Quick Start)

*Interface para a profissional colar uma lista de pacientes (nome + telefone) e popular o sistema em 2 minutos.*

### Tarefas

- [x] `[FRONT-S2-13]` **API Layer: `patientApi.batchImport()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-14]` **Página: `PatientImportPage.tsx`** — ⚠️ **PARCIAL — ver AC-04**
- [x] `[FRONT-S2-15]` **Hook: `usePatientImport()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-16]` **Roteamento: `/pacientes/importar`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-17]` **CSS Module: `PatientImport.module.css`** — ✅ Aprovado no review.

---

## EPIC-S2-04: Templates de Procedimentos

*Na tela de novo procedimento, oferecer templates pré-preenchidos do mercado de estética.*

### Tarefas

- [x] `[FRONT-S2-18]` **API Layer: `procedureApi.getTemplates()` e `createFromTemplate()`** — ✅ Aprovado no review.
- [x] `[FRONT-S2-19]` **Componente: `<ProcedureTemplateSelector />`** — 🐛 **BUG — ver AC-03**
- [x] `[FRONT-S2-20]` **Integração: Fluxo "Novo Procedimento"** — ✅ Aprovado no review.
- [x] `[FRONT-S2-21]` **CSS Module: `ProcedureTemplateSelector.module.css`** — ✅ Aprovado no review.

---

## EPIC-S2-05: PWA Mínimo (Add to Home Screen)

### Tarefas

- [x] `[FRONT-S2-22]` **PWA Manifest + Service Worker** — ✅ Aprovado no review. Implementação com `vite-plugin-pwa`, `NetworkFirst`, ícones e meta tags.

---

## 🔧 AÇÕES CORRETIVAS (Code Review — 2026-08-31)

*Itens identificados na revisão de código que devem ser corrigidos antes do deploy em produção.*

### 🟡 AC-03: Formatação monetária usando `Number()` (SEVERIDADE MÉDIA)
**Origem:** `FRONT-S2-03` e `FRONT-S2-19`
**Arquivos:**
- `src/features/dashboard/ROICard.tsx` (linha 26-28)
- `src/features/procedures/ProcedureTemplateSelector.tsx` (linha 42-44)

**Problema:** Ambos os componentes definem uma função local `formatPrice()` que faz:
```ts
const formatPrice = (val: string) => {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(val));
};
```

Isso viola a **Decisão F-02** de duas formas:
1. `Number(val)` converte a string para float IEEE 754, reintroduzindo erro de centavos que todo o pipeline `NUMERIC → Decimal → string → decimal.js` foi desenhado para evitar.
2. `new Intl.NumberFormat(...)` é instanciado **a cada render**, o que é ~100x mais lento que usar uma instância reutilizável.

**Fix requerido:**
- [x] Em `ROICard.tsx`: remover a função `formatPrice` local. Importar `formatBRL` de `@/lib/money/format`.
  ```ts
  import { formatBRL } from "@/lib/money/format";
  import type { Money } from "@/lib/money/money";

  // No JSX:
  {formatBRL(roi.attributed_revenue as Money)}
  ```
- [x] Em `ProcedureTemplateSelector.tsx`: mesma correção. Importar `formatBRL` ao invés de definir `formatPrice` local.
  ```ts
  import { formatBRL } from "@/lib/money/format";
  import type { Money } from "@/lib/money/money";

  // No JSX:
  ~{formatBRL(t.suggested_price as Money)}
  ```

**Nota:** O utilitário `formatBRL()` em `lib/money/format.ts` já existe, foi criado exatamente para isso, e usa `asStringFormatter()` que passa a string diretamente para o `Intl.NumberFormat` sem conversão para float. Consultem o arquivo `src/lib/money/format.ts` para referência.

**Teste de validação:** Verificar visualmente que valores como `R$ 1.234,56` continuam exibidos corretamente no ROICard e no seletor de templates.

---

### 🟡 AC-04: Etapa de confirmação ausente na importação de pacientes (SEVERIDADE MÉDIA)
**Origem:** `FRONT-S2-14`
**Arquivo:** `src/features/patients/PatientImportPage.tsx` (linhas 42-58)

**Problema:** O fluxo deveria ter 3 etapas:
1. **Entrada** → textarea com preview
2. **Confirmação** → resumo "X pacientes serão importados" + botão "Confirmar Importação"
3. **Resultado** → contagem de criados/skipped/erros

Atualmente, ao clicar "Prosseguir →", o código pula direto para a chamada da API (step 2 é apenas uma tela de "Importando..."). **O usuário não tem chance de revisar** antes de confirmar.

**Fix requerido:**
- [x] Separar o step 2 em dois momentos:
  ```
  Step 1: Textarea + Preview (já existe ✅)
  Step 2: Resumo de confirmação (NOVO)
     → Exibir: "{parsedData.length} pacientes serão importados"
     → Exibir: "{warningCount} sem telefone"
     → Botão "← Voltar" (setStep(1))
     → Botão "Confirmar Importação" (dispara a mutation)
  Step 3: Loading "Importando..." (renumerar)
  Step 4: Resultado final (renumerar, já existe ✅)
  ```
- Atualizar o type `Step = 1 | 2 | 3 | 4`.
- O botão "Prosseguir →" no step 1 deve ir para step 2 (resumo), não para a API.

---

### 🟢 AC-05: Falta optimistic update na confirmação de sessão (SEVERIDADE BAIXA)
**Origem:** `FRONT-S2-08`
**Arquivo:** `src/features/agenda/hooks.ts` (linhas 68-75)

**Problema:** O hook `useConfirmSession()` faz apenas invalidação padrão (`invalidateAfterScheduling`) ao confirmar uma sessão. A **Decisão F-06** permite optimistic update em campos não-monetários como `confirmed_at`, o que daria feedback instantâneo ao clicar no botão ✓.

**Fix requerido:**
- [x] Adicionar `onMutate` ao `useConfirmSession()`:
  ```ts
  export function useConfirmSession() {
    return useMutation({
      mutationFn: (id: string) => sessionsApi.confirmSession(id),
      onMutate: async (id) => {
        // Cancelar queries em andamento para evitar race condition
        await queryClient.cancelQueries({ queryKey: [...qk.sessions(), "unconfirmed"] });

        // Snapshot anterior
        const previousData = queryClient.getQueryData([...qk.sessions(), "unconfirmed"]);

        // Optimistic update: marcar confirmed_at localmente
        queryClient.setQueryData(
          [...qk.sessions(), "unconfirmed"],
          (old: UnconfirmedSession[] | undefined) =>
            old?.map(s =>
              s.session_id === id
                ? { ...s, confirmed_at: new Date().toISOString() }
                : s
            )
        );

        return { previousData };
      },
      onError: (_err, _id, context) => {
        // Rollback em caso de erro
        if (context?.previousData) {
          queryClient.setQueryData([...qk.sessions(), "unconfirmed"], context.previousData);
        }
      },
      onSettled: async () => {
        await invalidateAfterScheduling();
      },
    });
  }
  ```
- Importar `queryClient` de `@/lib/query/client` e `qk` de `@/lib/query/keys`.

---

### 🟢 AC-06: Badge de confirmação sem horário (SEVERIDADE BAIXA)
**Origem:** `FRONT-S2-09`
**Arquivo:** `src/features/agenda/NoShowAlert.tsx` (linha 63)

**Problema:** O badge de sessão confirmada exibe apenas `"✓ Confirmada"`, mas a especificação pedia `"✅ Confirmada às HH:MM"` com o horário da confirmação.

**Estado atual:**
```tsx
<div className={styles.confirmedBadge}>✓ Confirmada</div>
```

**Fix requerido:**
- [x] Formatar o `confirmed_at` e incluir no badge:
  ```tsx
  <div className={styles.confirmedBadge}>
    ✅ Confirmada às {new Date(session.confirmed_at!).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
  </div>
  ```

---

## Referência Cruzada: Riscos Endereçados

| Risco (Análise PO/PM) | EPIC que endereça | Status |
|---|---|---|
| R1 — Unit Economics Apertada | EPIC-S2-01 (Widget ROI) | ✅ (1 fix: AC-03) |
| R2 — Cold Start / Dia Zero | EPIC-S2-03 + EPIC-S2-04 | ✅ (2 fixes: AC-03, AC-04) |
| R4 — Agenda vs. Necessidade Real | EPIC-S2-05 (PWA) | ✅ Completo |
| R5 — Anti-No-Show Ausente | EPIC-S2-02 (Lembretes D-1) | ✅ (2 fixes: AC-05, AC-06) |
| R6 — Experiência Mobile | EPIC-S2-05 (PWA) | ✅ Completo |

---

## Critérios de Aceite Globais (aplicam a todas as tasks)

1. **Decisão F-01:** Front NUNCA calcula lucro ou valores financeiros. Apenas exibe o que a API retorna.
2. **Decisão F-02:** Formatação monetária via `formatBRL()` de `lib/money/format.ts`. **NUNCA usar `Number()` em strings monetárias.**
3. **Decisão F-03:** Inputs de dinheiro: `inputMode="numeric"`, `type="text"`, acúmulo de centavos da direita para esquerda.
4. **Decisão F-05:** `Idempotency-Key` em `useRef` ao abrir formulários com mutação.
5. **Decisão F-06:** Optimistic update APENAS em campos não-monetários (status, confirmação).
6. **Decisão F-07:** Mobile-first. Botões ≥ 48px. Inputs com `font-size: 16px`. Skeletons com altura fixa.
7. **CSS Modules:** Todo componente novo deve usar CSS Modules (`.module.css`), não CSS global.
8. **React Query Keys:** Usar prefixos centralizados do `lib/query/keys.ts`. Invalidações em cascata via `invalidateAfterSale`.
9. **Error Boundaries:** Componentes novos devem ser tolerantes a falhas (não quebrar a página inteira).
10. **Acessibilidade:** `aria-label` em botões de ícone, labels em inputs, contraste WCAG AA.

---

## Ordem de Implementação das Correções

```
Prioridade 1 (ANTES do deploy):
  AC-03 (formatBRL)       → 30min — trocar 2 funções locais por import existente
  AC-04 (etapa confirmação) → 1h — adicionar step intermediário no import

Prioridade 2 (pode ir no primeiro patch pós-deploy):
  AC-05 (optimistic update) → 30min — adicionar onMutate no hook
  AC-06 (horário no badge)  → 15min — 1 linha de código
```
