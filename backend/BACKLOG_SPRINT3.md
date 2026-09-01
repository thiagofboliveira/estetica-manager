# Backlog Sprint 3 — Backend

Sprint focada em **Recursos Financeiros Avançados, Projeção de Fluxo de Caixa e Portabilidade/LGPD**, derivada do modelo de negócio e especificações de P1 (2026-08-31).

---

## 🎯 Status Geral da Sprint 3

| EPIC | Descrição | Status | Tarefas | Testes Automatizados |
| :--- | :--- | :---: | :---: | :---: |
| **EPIC-S3-01** | **Split por Procedimento (E6)** | ✅ Concluído | 4/4 | `tests/test_procedure_split_override.py` |
| **EPIC-S3-02** | **Exportação de Dados em CSV (LGPD/Relatórios)** | ✅ Concluído | 4/4 | `tests/test_export.py` |
| **EPIC-S3-03** | **Projeção de Recebíveis Futuros (Fluxo de Caixa)** | ✅ Concluído | 4/4 | `tests/test_receivables.py` |
| **EPIC-S3-04** | **Antecipação de Recebíveis (E7)** | ✅ Concluído | 4/4 | `tests/test_anticipation.py` |

---

## 📦 Detalhamento das Tarefas

### EPIC-S3-01: Split por Procedimento (E6)
- [x] `[TASK-BACK-S3-01]` Adicionar coluna `split_override NUMERIC(5,2) NULL` em `procedures` e migração Alembic `0009_split_override_and_anticipation.py`.
- [x] `[TASK-BACK-S3-02]` Atualizar modelo `Procedure` e schemas `ProcedureCreate`, `ProcedureUpdate`, `ProcedureOut` e `ProcedureFromTemplateCreate`.
- [x] `[TASK-BACK-S3-03]` Atualizar `calculator.py` com cálculo de split customizado por item com precedência sobre a taxa padrão da clínica.
- [x] `[TASK-BACK-S3-04]` Criar suíte de testes unitários `tests/test_procedure_split_override.py`.

### EPIC-S3-02: Exportação de Dados em CSV (LGPD & Relatórios)
- [x] `[TASK-BACK-S3-05]` Criar serviço puro `ExportService` com formatação brasileira (separador `;`, UTF-8 BOM para Excel e valores em R$).
- [x] `[TASK-BACK-S3-06]` Implementar endpoint `GET /api/v1/export/patients.csv`.
- [x] `[TASK-BACK-S3-07]` Implementar endpoint `GET /api/v1/export/sales.csv`.
- [x] `[TASK-BACK-S3-08]` Implementar endpoint `GET /api/v1/export/sessions.csv` e suíte `tests/test_export.py`.

### EPIC-S3-03: Projeção de Recebíveis Futuros (Fluxo de Caixa)
- [x] `[TASK-BACK-S3-09]` Criar motor puro `receivables.py` (`project_monthly_receivables`) para projeção mês a mês de parcelamento de cartão de crédito.
- [x] `[TASK-BACK-S3-10]` Integrar projeção no `DashboardService.get_receivables_projection()`.
- [x] `[TASK-BACK-S3-11]` Adicionar endpoint `GET /api/v1/dashboard/receivables` e schemas `ReceivablesOut`, `MonthlyReceivableOut`.
- [x] `[TASK-BACK-S3-12]` Criar suíte de testes `tests/test_receivables.py`.

### EPIC-S3-04: Antecipação de Recebíveis (E7)
- [x] `[TASK-BACK-S3-13]` Adicionar colunas `anticipates_all` e `anticipation_rate_per_installment` em `financial_settings`.
- [x] `[TASK-BACK-S3-14]` Atualizar modelo `FinancialSettings` e schemas `FinancialSettingsUpdate`, `FinancialSettingsOut`.
- [x] `[TASK-BACK-S3-15]` Atualizar `calculate_sale` e `expected_receipt_date` para computar taxa extra de antecipação e data D+2.
- [x] `[TASK-BACK-S3-16]` Criar suíte de testes `tests/test_anticipation.py`.
