# 🐛 Relatório de QA & Auditoria de Bugs — Backend (Sprint 1, 2 & 3)

**Data da Auditoria:** 31/08/2026  
**Perfil do Auditor:** QA Lead & Test Automation Engineer  
**Escopo:** API FastAPI, SQLAlchemy ORM, Alembic Migrations, Regras de Negócio e Suíte de Testes (Pytest).

---

## Sumário Executivo — Status Geral das Sprints

| Sprint / EPIC | Severidade Alta | Severidade Média | Severidade Baixa / Melhoria | Status de QA |
| :--- | :---: | :---: | :---: | :---: |
| **Sprint 3: EPIC-S3-01 (Split por Procedimento)** | 0 | 0 | 0 | ✅ Aprovado com Excelência |
| **Sprint 3: EPIC-S3-02 (Exportação CSV / LGPD)** | 0 | 0 | 0 | ✅ Aprovado com Excelência |
| **Sprint 3: EPIC-S3-03 (Projeção de Recebíveis)** | 0 | 1 | 0 | ✅ Aprovado com Observação |
| **Sprint 3: EPIC-S3-04 (Antecipação de Recebíveis)**| 0 | 0 | 0 | ✅ Aprovado com Excelência |
| **Sprint 2: EPIC-S2-01 (Widget de ROI)** | 0 | 0 | 0 | ✅ Aprovado (`period.kind.value`) |
| **Sprint 2: EPIC-S2-02 (Anti-No-Show)** | 0 | 1 | 0 | ⚠️ Ajuste de Regra |
| **Sprint 2: EPIC-S2-03 (Importação em Lote)** | 0 | 0 | 0 | ✅ Aprovado |
| **Sprint 2: EPIC-S2-04 (Templates de Procedimentos)**| 0 | 0 | 0 | ✅ Aprovado |
| **Sprint 1: Multi-Tenant, Users & Super Admin** | 0 | 0 | 0 | ✅ 166 testes passando |

---

## 1. Avaliação dos Novos Recursos da Sprint 3

### ✅ EPIC-S3-01: Split por Procedimento (E6) — APROVADO
* **Implementação:** Coluna `split_override NUMERIC(5,2)` adicionada na tabela `procedures` (migration `0009_split_override_and_anticipation.py`).
* **Motor Financeiro:** O `calculator.py` suporta perfeitamente split individual por item com precedência sobre o percentual da clínica, suportando bases `GROSS` e `NET_OF_FEE`.
* **Testes:** Suíte `tests/test_procedure_split_override.py` cobriu caso único, itens mistos e com desconto rateado.

---

### ✅ EPIC-S3-02: Exportação de Dados em CSV (LGPD & Relatórios) — APROVADO
* **Implementação:** Endpoints `GET /api/v1/export/patients.csv`, `GET /api/v1/export/sales.csv` e `GET /api/v1/export/sessions.csv`.
* **Padrão Brasileiro:** CSVs gerados com delimitador `;`, UTF-8 BOM (`\ufeff`) para abertura nativa no Excel sem falhas de acentuação e valores monetários com vírgula.
* **Testes:** Suíte `tests/test_export.py` validando cabeçalhos e formatação.

---

### 🟡 EPIC-S3-03: Projeção de Recebíveis Futuros (Fluxo de Caixa) — APROVADO COM OBSERVAÇÃO
* **[OBS-BACK-S3-01] Flag `is_anticipated` fixada em `False` no `DashboardService`**
  * **Arquivo:** `backend/app/services/dashboard_service.py` (linha 108)
  * **Descrição:** Ao listar as vendas para projeção de fluxo de caixa em `get_receivables_projection()`, a propriedade `is_anticipated` do input é definida como `False` de forma estática.
  * **Impacto:** Se a clínica opera com antecipação automática (`anticipates_all = True`), as parcelas de cartão são projetadas mês a mês (D+30, D+60) em vez de caírem em D+2 no mês da venda.
  * **Correção Recomendada:**
    Consultar `financial_settings.anticipates_all` no `DashboardService` e passar para o `SaleReceivableInput(..., is_anticipated=settings.anticipates_all)`.

---

### ✅ EPIC-S3-04: Antecipação de Recebíveis (E7) — APROVADO
* **Implementação:** Colunas `anticipates_all` e `anticipation_rate_per_installment` em `financial_settings`.
* **Cálculo:** `calculator.py` computa a taxa de antecipação proporcional às parcelas e `expected_receipt_date` ajusta a liquidação para D+2.
* **Testes:** Suíte `tests/test_anticipation.py` passando.

---

## 2. Status dos Itens das Sprints Anteriores

### 🟡 [BUG-BACK-S2-02] Omissão de Telefone/WhatsApp em Bookings Vinculados a Pacientes
* **Severidade:** Média
* **Arquivo:** `backend/app/services/session_service.py` (linhas 391-409)
* **Descrição:** Em `list_unconfirmed()`, bookings não verificam `b.patient` para preencher `patient_phone` e gerar link de WhatsApp quando o agendamento provisório pertence a uma paciente já cadastrada.
