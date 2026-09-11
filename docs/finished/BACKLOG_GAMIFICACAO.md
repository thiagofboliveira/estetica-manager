# 🎮 Backlog — Módulo de Gamificação, Fidelidade & Ativação da Clínica

**Documento de Especificação Funcional e Arquitetura**  
**Escopo:** Gamificação em 3 Sprints — Metas & Break-Even, Checklist de Maturidade Clínica, Clube VIP & Programa de Indicação ("Traga uma Amiga"), e Resolução de Casos de Borda de QA.  
**Data:** 11/09/2026  
**Status:** `completed` (Implementado, Testado e Mesclado na Main)

---

## 🎯 Visão Executiva do Produto

Transformar a gestão da clínica de estética em uma jornada de conquista, retenção de pacientes e crescimento previsível através de mecânicas de gamificação intencionais:

1. **Sprint 1 (Conquistas Financeiras & Break-Even):**
   * Metas mensais de faturamento configuráveis pelo profissional.
   * Termômetro visual de conquista no Dashboard e comemorações de meta batida.
   * Cálculo automático do Ponto de Equilíbrio (Break-Even) e comemoração do momento exato do mês em que a clínica superou seus custos fixos e passou a lucrar 100% no bolso.

2. **Sprint 2 (Checklist de Ativação & Níveis de Maturidade Clínica):**
   * Onboarding interativo com cálculo percentual de ativação da clínica.
   * 3 Níveis de Maturidade: 🌱 **Nível 1: Clínica Inicial**, ⚡ **Nível 2: Clínica Digital**, 👑 **Nível 3: Alta Performance**.
   * 6 etapas essenciais com verificação em tempo real: Procedimentos, Pacientes, Taxas & Despesas Fixas, Primeiro Atendimento/Venda, Campanhas de WhatsApp e Meta de Faturamento.
   * Certificado de ativação comemorativo ao atingir 100% de maturidade.

3. **Sprint 3 (Clube VIP, Fidelidade & "Traga uma Amiga"):**
   * Sistema de pontuação baseado no consumo de serviços (1 ponto a cada R$ 10 gastos).
   * 4 Tiers de fidelidade com promoção automática: **Bronze** (0 pts), **Prata** (100 pts), **Ouro** (300 pts) e **Diamante** (700 pts).
   * Programa de Indicação ("Traga uma Amiga"): código exclusivo por paciente, concessão de pontos bônus no primeiro atendimento da amiga indicada.
   * Resgate de pontos em créditos de desconto no prontuário e na venda.
   * Campanhas de WhatsApp segmentadas por nível VIP com placeholders `{pontos}` e `{nivel_vip}`.

4. **QA & Casos de Borda (Sprint de Estabilização):**
   * Configuração de meta mensal diretamente no formulário financeiro (`/financeiro`) com atalhos de sugestão rápida.
   * Modal pop-up ágil de meta integrado ao Checklist de Ativação (configuração em 1 clique).
   * Correção de regressão de importação em lote (`batch_import`) e dashboards agregados (`scope=clinic`).

---

## 🏗️ Arquitetura e Invariantes de Engenharia

O módulo segue rigorosamente as diretrizes de arquitetura do `ENGENHARIA.md`:

* **Invariante I1 (Dinheiro nunca é float):** Valores monetários e metas (`monthly_revenue_goal`, `discount_credit`) utilizam `NUMERIC(12,2)` no PostgreSQL, `Decimal` no Python e `string` na API REST.
* **Invariante I2 (Multi-Tenancy por Clínica/Profissional):** Tabela `loyalty_transactions` e configurações financeiras isoladas com `tenant_id` e Row-Level Security (RLS).
* **Domínio Puro e Testável:** Regras de negócio de acúmulo de pontos, promoção de nível VIP e recompensa por indicação isoladas em `app/domain/loyalty/rules.py`, sem acoplamento com banco ou I/O.
* **Idempotência e Auditoria:** Cada movimentação de pontos (acúmulo, resgate, bônus de indicação, ajuste manual) gera registro imutável em `loyalty_transactions`.

---

## 📦 Detalhamento das Entregas e Tarefas

### SPRINT 1: Metas Financeiras, Ponto de Equilíbrio & Micro-Feedbacks

- [x] `[TASK-GAME-01]` **Migration Alembic 0033:** Adição da coluna `monthly_revenue_goal NUMERIC(12,2) NULL` na tabela `financial_settings`.
- [x] `[TASK-GAME-02]` **Backend DTOs & Schemas:** Suporte a `monthly_revenue_goal` em `FinancialSettingsUpdate` e `FinancialSettingsOut`.
- [x] `[TASK-GAME-03]` **Domínio de Break-Even no Dashboard:** Enriquecimento do cálculo de dashboard com `breakeven_beaten`, `breakeven_beaten_date`, `breakeven_remaining_amount` e `monthly_revenue_goal`.
- [x] `[TASK-GAME-04]` **Componente MonthlyAchievementsCard.tsx:**
  * Termômetro visual de progresso da meta com micro-feedbacks.
  * Celebração comemorativa quando a meta é batida.
  * Banner de comemoração de superação do Ponto de Equilíbrio (*"Sua clínica já pagou todos os custos fixos no dia DD/MM!"*).
  * Modal de compartilhamento no WhatsApp e cópia de conquistas.

---

### SPRINT 2: Onboarding Gamificado & Níveis de Maturidade Clínica

- [x] `[TASK-GAME-05]` **Componente OnboardingChecklist.tsx:**
  * Barra de progresso dinâmica com percentual de 0% a 100%.
  * Badges de maturidade clínica (*Inicial*, *Digital*, *Alta Performance*).
  * 6 etapas guiadas com links de atalho inteligentes e estado concluído/pendente.
  * Opções de minimizar e dispensar persistidas no `localStorage`.
- [x] `[TASK-GAME-06]` **Certificado de Ativação 100%:**
  * Card comemorativo dourado com troféu e micro-cópia encorajadora.
  * CTA de conversão apontando para planos e benefícios ativos (`/planos`).

---

### SPRINT 3: Clube VIP, Fidelidade & "Traga uma Amiga"

- [x] `[TASK-GAME-07]` **Migration Alembic 0034:**
  * Colunas na tabela `patients`: `loyalty_points INT DEFAULT 0`, `vip_tier VARCHAR(20) DEFAULT 'BRONZE'`, `referral_code VARCHAR(20) UNIQUE`, `referred_by_id UUID FK`.
  * Criação da tabela `loyalty_transactions`: `id`, `tenant_id`, `patient_id`, `sale_id`, `type`, `points`, `balance_after`, `description`, `created_at`.
  * Políticas de RLS habilitadas para `loyalty_transactions`.
- [x] `[TASK-GAME-08]` **Regras de Negócio de Domínio (`app/domain/loyalty/rules.py`):**
  * `calculate_sale_loyalty_points(net_amount)`: 1 ponto a cada R$ 10,00 gastos.
  * `determine_vip_tier(total_points)`: Bronze (0-99), Prata (100-299), Ouro (300-699), Diamante (700+).
  * `apply_referral_reward()`: 50 pontos para a madrinha e 30 pontos de boas-vindas para a afilhada na primeira venda.
  * `points_to_discount_credit(points)`: Conversão de pontos em desconto monetário.
- [x] `[TASK-GAME-09]` **API de Fidelidade (`/api/v1/loyalty`):**
  * `GET /api/v1/loyalty/{patient_id}`: Saldo, tier VIP, código de indicação e histórico de transações.
  * `POST /api/v1/loyalty/{patient_id}/manual-credit`: Crédito/ajuste manual com justificativa.
  * `POST /api/v1/loyalty/{patient_id}/redeem`: Resgate de pontos com validação de saldo.
  * `POST /api/v1/loyalty/validate-referral`: Validação de código de indicação antes da venda.
- [x] `[TASK-GAME-10]` **Frontend de Fidelidade & VIP:**
  * Aba **Clube VIP & Fidelidade** no Prontuário da Paciente (`PatientLoyaltyTab.tsx`).
  * Modal de resgate de pontos e cópia de link/código "Traga uma Amiga".
  * Badges visuais de Nível VIP na listagem de pacientes (`PatientsPage.tsx`).
  * Filtro de segmentação por Nível VIP e tags `{pontos}` e `{nivel_vip}` no Disparador de Campanhas do WhatsApp (`WhatsAppCampaignsPage.tsx`).

---

### SPRINT DE QA & ESTABILIZAÇÃO: Correções e Casos de Borda

- [x] `[TASK-GAME-11]` **Formulário de Configuração Financeira (`FinancialSettingsForm.tsx`):**
  * Inclusão do campo `monthly_revenue_goal` no schema Zod, nos valores padrão e no payload de envio.
  * Card de destaque visual com explicação, campo formatado em R$ e chips de sugestão rápida (`R$ 5.000`, `R$ 10.000`, `R$ 20.000`, `R$ 30.000`, `R$ 50.000`).
  * Botão de acesso direto a Custos Fixos (`/despesas-fixas`) na página `/financeiro`.
- [x] `[TASK-GAME-12]` **Modal Ágil de Meta no Onboarding (`OnboardingChecklist.tsx`):**
  * Criação de modal inline para configuração de meta em 1 clique diretamente pelo checklist.
  * Validação de valor positivo, persistência via API, recarregamento automático e feedback visual imediato.
- [x] `[TASK-GAME-13]` **Correções de Regressões do Backend:**
  * Importação de `Decimal` ausente em `dashboard_service.py` corrigindo falha no dashboard agregado (`scope=clinic`).
  * Sanitização de strings monetárias em `financial_settings_service.py` tratando vazios como `None` e vírgulas decimais.
  * Defaults resilientes de fidelidade em `PatientOut` e `PatientService.batch_import`, garantindo sucesso na importação de pacientes por CSV.
  * Teste unitário de casos de borda: `backend/tests/test_financial_settings_goal.py`.

---

## 🗂️ Arquivos Impactados

### Backend
| Arquivo | Descrição da Modificação |
| :--- | :--- |
| `alembic/versions/0033_monthly_revenue_goal.py` | Migration com campo de meta mensal em `financial_settings` |
| `alembic/versions/0034_loyalty_and_referral.py` | Migration de pontos, tiers, indicações e `loyalty_transactions` |
| `app/models/financial_settings.py` | Coluna `monthly_revenue_goal` no modelo SQLAlchemy |
| `app/models/patient.py` | Colunas de pontos, VIP tier e referral code no paciente |
| `app/models/loyalty.py` | Modelo `LoyaltyTransaction` e enum `LoyaltyTransactionType` |
| `app/domain/loyalty/rules.py` | Regras puras de pontuação, tiers VIP e indicação |
| `app/services/dashboard_service.py` | Métricas de break-even e agregação de metas da clínica |
| `app/services/financial_settings_service.py` | Sanitização e persistência da meta mensal |
| `app/services/patient_service.py` | Inicialização de fidelidade e geração de código de indicação |
| `app/schemas/financial_settings.py` | Schemas de entrada e saída de configurações financeiras |
| `app/schemas/patient.py` | Validadores de fidelidade para importação segura |
| `app/schemas/loyalty.py` | Schemas de requisição e resposta do módulo de fidelidade |
| `app/api/v1/loyalty.py` | Rotas REST de extrato, resgate e indicação |
| `tests/test_loyalty.py` | Testes de integração da API de fidelidade |
| `tests/test_loyalty_rules.py` | Testes unitários das regras de domínio de pontos e VIP |
| `tests/test_financial_settings_goal.py` | Testes de casos de borda da configuração de meta |

### Frontend
| Arquivo | Descrição da Modificação |
| :--- | :--- |
| `src/features/dashboard/MonthlyAchievementsCard.tsx` | Termômetro de metas, comemoração de break-even e modal de conquista |
| `src/features/onboarding/OnboardingChecklist.tsx` | Checklist de ativação, maturidade clínica e modal ágil de meta |
| `src/features/onboarding/OnboardingChecklist.module.css` | Estilos de barra de progresso, certificado e modal |
| `src/features/settings/FinancialSettingsForm.tsx` | Seção de meta mensal com chips de sugestão rápida |
| `src/features/settings/FinancialSettingsPage.tsx` | Navegação integrada entre metas, taxas e custos fixos |
| `src/features/patients/PatientLoyaltyTab.tsx` | Painel de fidelidade, resgate de pontos e indicação |
| `src/features/patients/PatientsPage.tsx` | Badges de Nível VIP (Bronze, Prata, Ouro, Diamante) |
| `src/features/whatsapp-campaigns/WhatsAppCampaignsPage.tsx` | Filtro por Nível VIP e tags dinâmicas de fidelidade |
| `src/features/loyalty/api.ts` e `useLoyalty.ts` | Camada de dados e hooks React Query de fidelidade |

---

## 🧪 Bateria de Testes e Validação de QA

A entrega foi submetida a verificação automatizada completa com cobertura total de regressão:

1. **Backend Tests (Pytest):**
   * **367 testes executados e aprovados com 100% de sucesso.**
   * Cobertura de regras financeiras, RLS de transações de fidelidade, deduplicação de importação e agregação de dashboards.
2. **Frontend Tests (Vitest):**
   * **18 testes unitários aprovados com 100% de sucesso.**
   * Precisão na aritmética monetária e formatação pt-BR.
3. **Frontend Production Build:**
   * Compilação com `tsc -b` e `vite build` sem qualquer erro de tipagem ou bundle.

---

## 🚀 Histórico de Commits e Entrega

* `aa2b55d`: feat(sprint1): metas financeiras, break-even e micro-feedbacks no dashboard
* `fa24312`: feat(sprint2): checklist de maturidade clinica e onboarding gamificado
* `e76a9e1`: feat(sprint3): clube vip, sistema de fidelidade e programa traga uma amiga
* `b8e17cf`: fix(qa): adicionar configuracao de meta mensal no financeiro, modal no onboarding e corrigir regressões

**Branch:** `main`  
**Status do Repositório:** Sincronizado e publicado em `origin/main`.
