# 💳 Backlog — Módulo de Assinaturas, Cobrança (Asaas) e Promoção de Inauguração

**Documento de Especificação Funcional e Arquitetura**  
**Escopo:** Faturamento SaaS (Billing), Gestão de Assinaturas, Trial de 14 Dias, Tabela Centralizada de Preços, Cupons de Desconto e Integração com Gateway Asaas.  
**Data:** 10/09/2026  
**Status:** `completed` (Implementado e Testado)

---

## 🎯 Visão Executiva do Produto

Implementar o módulo oficial de monetização do **Lumina**, permitindo que esteticistas e clínicas assinem a plataforma de forma transparente, automatizada e com baixo atrito:
1. **2 Semanas Grátis (Trial de 14 Dias):** Toda nova clínica tem acesso irrestrito às funcionalidades por 14 dias sem cobrança inicial.
2. **Preços Promocionais de Inauguração:**
   * **Plano Mensal:** R$ 80,00 / mês (cobrança mensal de R$ 80,00).
   * **Plano Trimestral:** R$ 65,00 / mês (cobrança trimestral de R$ 195,00 — economia de ~19%).
   * **Plano Anual:** R$ 50,00 / mês (cobrança anual de R$ 600,00 — economia de 37,5%).
3. **Módulo de Preços Centralizado (Single Source of Truth):** Todas as regras de planos, ciclos, descontos e vigências residem em um único ponto no backend, expostas via API para o frontend.
4. **Motor de Cupons de Desconto:** Validação e aplicação de cupons promocionais (fixos em R$ ou percentuais) no checkout.
5. **Gateway Asaas (API v3):** Emissão de cobranças recorrentes com suporte a **Pix**, **Cartão de Crédito** e **Boleto**, com webhook para atualização de status em tempo real.

---

## 🏗️ Arquitetura e Invariantes de Engenharia

O módulo deve seguir estritamente as diretrizes do `ENGENHARIA.md`:
* **Invariante I1 (Dinheiro nunca é float):** Todos os valores monetários (`price`, `discount`, `final_value`) utilizam `NUMERIC(12,2)` no banco, `Decimal` no Python e `string` no JSON da API.
* **Invariante I2 (Multi-Tenancy por Clínica):** A assinatura pertence à entidade `Clinic` (todas as profissionais da mesma clínica compartilham o plano contratado).
* **Defesa em Profundidade:** Webhooks do Asaas protegidos por token de autenticação via header (`asaas-access-token`).
* **Trial Grace Period:** Período de cortesia de 2 dias após vencimento de fatura antes do bloqueio total de tela.

---

## 📦 Épicos e Tarefas

### EPIC-BILL-01: Módulo Centralizado de Preços e Regras de Negócio (Backend)
> **Objetivo:** Isolar a regra de precificação em módulo puro de domínio para fácil alteração de valores futuros sem tocar no banco de dados ou no frontend.

- [x] `[TASK-BILL-01]` Criar `app/domain/billing/pricing.py` definindo enums `BillingCycle` (`MONTHLY`, `QUARTERLY`, `YEARLY`) e dataclasses tipadas `PlanDefinition`, `PlanPricing`:
  - Mensal: `R$ 80.00`/mês, ciclo `MONTHLY`, valor ciclo `R$ 80.00`.
  - Trimestral: `R$ 65.00`/mês, ciclo `QUARTERLY`, valor ciclo `R$ 195.00`, badge "Mais Escolhido".
  - Anual: `R$ 50.00`/mês, ciclo `YEARLY`, valor ciclo `R$ 600.00`, badge "Maior Economia 37% OFF".
  - Metadados de Inauguração: `is_launch_promo=True`, label `Promoção de Inauguração — Preço Travado`.
- [x] `[TASK-BILL-02]` Implementar função de cálculo de economia relativa (`calculate_savings`) comparando ciclos trimestral e anual em relação ao mensal.
- [x] `[TASK-BILL-03]` Criar endpoint `GET /api/v1/billing/plans` que expõe a lista consolidada de planos e regras para o frontend.
- [x] `[TASK-BILL-04]` Criar suíte de testes unitários `tests/test_billing_pricing.py` garantindo que os cálculos de ciclo e arredondamento fechem no centavo exato.

---

### EPIC-BILL-02: Motor de Cupons de Desconto (Backend)
> **Objetivo:** Permitir criação e validação de cupons promocionais para campanhas de marketing e parcerias.

- [x] `[TASK-BILL-05]` Criar migration Alembic para tabela `coupons`:
  ```text
  id UUID PK
  code VARCHAR(50) UNIQUE (case-insensitive)
  discount_type VARCHAR(20) (PERCENTAGE | FIXED)
  discount_value NUMERIC(12,2)
  is_active BOOLEAN
  valid_from TIMESTAMPTZ
  valid_until TIMESTAMPTZ (nullable)
  max_redemptions INT (nullable)
  times_redeemed INT DEFAULT 0
  allowed_cycles VARCHAR[] (nullable — ex: apenas YEARLY)
  created_at, updated_at
  ```
- [x] `[TASK-BILL-06]` Implementar modelo SQLAlchemy `Coupon` e repositório `CouponRepository`.
- [x] `[TASK-BILL-07]` Criar domínio `app/domain/billing/coupons.py` com validador de vigência, limite de uso e aplicador de desconto (com Largest Remainder se percentual).
- [x] `[TASK-BILL-08]` Criar endpoint `POST /api/v1/billing/coupons/validate` recebendo `code` e `cycle`, retornando: `original_amount`, `discount_amount`, `final_amount` e `is_valid`.
- [x] `[TASK-BILL-09]` Criar migration de seed inicial com cupons padrão: `INAUGURACAO` (10% extra) e `PRIMEIRAS10` (R$ 30 fixo).
- [x] `[TASK-BILL-10]` Criar testes unitários `tests/test_coupons.py` validando cupons vencidos, esgotados e restrição de ciclos.

---

### EPIC-BILL-03: Modelo de Assinaturas e Controle de Trial (Backend)
> **Objetivo:** Controlar o ciclo de vida da conta (Trial de 14 dias, Ativa, Inadimplente, Cancelada).

- [x] `[TASK-BILL-11]` Criar migration Alembic para tabela `subscriptions`:
  ```text
  id UUID PK
  clinic_id UUID FK -> clinics UNIQUE
  plan_id VARCHAR(50) DEFAULT 'pro'
  cycle VARCHAR(20) (MONTHLY, QUARTERLY, YEARLY)
  status VARCHAR(20) (TRIALING, ACTIVE, PAST_DUE, CANCELED)
  trial_started_at TIMESTAMPTZ
  trial_ends_at TIMESTAMPTZ
  current_period_start TIMESTAMPTZ
  current_period_end TIMESTAMPTZ
  asaas_customer_id VARCHAR(100)
  asaas_subscription_id VARCHAR(100)
  coupon_id UUID FK -> coupons (nullable)
  created_at, updated_at
  ```
- [x] `[TASK-BILL-12]` Ao criar uma nova clínica (`system_service.py` ou registro), instanciar automaticamente a `Subscription` com `status=TRIALING` e `trial_ends_at = now() + 14 days`.
- [x] `[TASK-BILL-13]` Criar lógica e controle de assinatura ativa com cálculo de status em `billing_service.py`.
- [x] `[TASK-BILL-14]` Criar endpoint `GET /api/v1/billing/status` retornando dados atuais da assinatura, dias restantes de trial e status de pagamento.

---

### EPIC-BILL-04: Integração com Gateway Asaas v3 (Backend)
> **Objetivo:** Comunicação direta com a API do Asaas para cobrança via Pix, Cartão e Boleto.

- [x] `[TASK-BILL-15]` Adicionar variáveis de ambiente em `app/core/config.py`:
  - `ASAAS_API_KEY: str`
  - `ASAAS_API_URL: str` (default `https://sandbox.asaas.com/api/v3` em dev; `https://api.asaas.com/v3` em prod)
  - `ASAAS_WEBHOOK_SECRET: str`
- [x] `[TASK-BILL-16]` Implementar cliente HTTP leve `app/core/asaas.py` utilizando `httpx`:
  - `create_or_get_customer(name, email, document, phone)`
  - `create_subscription(customer_id, value, cycle, next_due_date, billing_type, description)`
  - `get_subscription_invoice(subscription_id)` (busca QR code Pix e link de pagamento)
- [x] `[TASK-BILL-17]` Implementar endpoint de checkout `POST /api/v1/billing/checkout`:
  - Recebe `cycle`, `coupon_code` (opcional) e `billing_type` (`UNDEFINED`, `PIX`, `CREDIT_CARD`, `BOLETO`).
  - Calcula valor com módulo de precificação centralizado.
  - Define `next_due_date`: se estiver no trial, a primeira cobrança é agendada para `trial_ends_at` (garantindo as 2 semanas grátis!).
  - Cria ou atualiza a assinatura no Asaas e vincula ao banco local.
  - Retorna link da fatura / invoice URL para pagamento.
- [x] `[TASK-BILL-18]` Implementar webhook `POST /api/v1/billing/webhooks/asaas`:
  - Validação estrita do header `asaas-access-token`.
  - Processa eventos:
    - `PAYMENT_RECEIVED` / `PAYMENT_CONFIRMED` ➔ Atualiza status para `ACTIVE` e estende `current_period_end`.
    - `PAYMENT_OVERDUE` ➔ Atualiza status para `PAST_DUE`.
    - `SUBSCRIPTION_DELETED` ➔ Atualiza status para `CANCELED`.
- [x] `[TASK-BILL-19]` Criar suíte de testes de webhook e checkout `tests/test_billing_api.py`.

---

### EPIC-BILL-05: Frontend — Telas de Planos, Checkout e Promoção de Inauguração
> **Objetivo:** Interface amigável, clara e de alta conversão, evidenciando o desconto de inauguração e os 14 dias de teste.

- [x] `[TASK-BILL-20]` Criar módulo de API no frontend `src/features/billing/billingApi.ts` (`getPlans()`, `getStatus()`, `validateCoupon()`, `createCheckout()`).
- [x] `[TASK-BILL-21]` Criar página de planos `src/features/billing/PlansPage.tsx`:
  - Header em destaque: *"Promoção Especial de Inauguração — Garanta sua vaga com preço travado"*.
  - Badge informativa: *"2 semanas (14 dias) grátis no primeiro mês sem cobrança imediata"*.
  - Cards comparativos dos 3 ciclos:
    - **Mensal:** R$ 80,00/mês.
    - **Trimestral:** R$ 65,00/mês *(Cobrado R$ 195 a cada 3 meses — destaque "Mais Escolhido")*.
    - **Anual:** R$ 50,00/mês *(Cobrado R$ 600/ano — destaque "Maior Economia 37% OFF")*.
  - Tabela comparativa de recursos (tudo liberado em todos os planos).
- [x] `[TASK-BILL-22]` Criar componente interativo de Cupom de Desconto `src/features/billing/CouponInput.tsx`:
  - Input para digitar código (ex: `INAUGURACAO`).
  - Validação em tempo real com feedback de sucesso/erro e linha de desconto visível no resumo.
- [x] `[TASK-BILL-23]` Banner / Contador de Trial no Topo da Aplicação (`TrialCountdownBanner.tsx`):
  - Exibe no topo da aplicação: *"Você está no período de teste: restam X dias gratuitos."* + Botão *"Garantir Preço Travado"*.
- [x] `[TASK-BILL-24]` Rotas e navegação integradas em `AppLayout.tsx`, `Sidebar.tsx` e `router.tsx` (`/assinatura` e `/planos`).

---

## 🧪 Matriz de Testes e Critérios de Aceite

| ID | Cenário de Teste | Critério de Aceite |
|---|---|---|
| **TC-01** | Nova clínica criada no sistema | Assinatura criada com status `TRIALING` e data de expiração exatamente em D+14. |
| **TC-02** | Consulta de planos via API | Endpoint `/billing/plans` retorna os 3 ciclos (80/65/50) com strings monetárias exatas e badges de inauguração. |
| **TC-03** | Aplicação de cupom percentual | Cupom de 10% no plano anual (R$ 600,00) reduz o valor final para R$ 540,00 no centavo exato. |
| **TC-04** | Checkout durante o período de trial | Assinatura no Asaas criada com `nextDueDate` igual a `trial_ends_at`, sem cobrança antecipada. |
| **TC-05** | Webhook de pagamento confirmado | Evento `PAYMENT_CONFIRMED` altera status da clínica de `TRIALING` para `ACTIVE`. |
| **TC-06** | Fim do trial sem pagamento | Sistema bloqueia rotas operacionais com HTTP 402 e exibe o `PaywallModal` sem perda de dados. |

---

## 📅 Estimativa de Esforço

* **Backend (Preços + Cupons + Asaas + Webhooks):** ~24 a 32 horas (3 a 4 dias úteis).
* **Frontend (Página de Planos + Cupom + Banners + Paywall):** ~16 a 24 horas (2 a 3 dias úteis).
* **Homologação e Testes no Sandbox do Asaas:** ~8 horas (1 dia útil).
* **Tempo Total Estimado:** **~1 a 2 semanas** para entrega completa em produção.
