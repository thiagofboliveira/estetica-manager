# Backlog Sprint 2 — Backend

Sprint focada em **validação de mercado e go-to-market**, derivada da análise de produto PO/PM (2026-08-31).
Todas as features endereçam riscos concretos identificados na entrevista com a Cliente Zero.

## 📊 Progresso Geral

- **Total de Tarefas:** 20 implementadas + 3 ações corretivas — **todas corrigidas** (2026-09-04)
- **Aprovadas no Code Review:** 20/20 (100%)
- **Ações Corretivas Pendentes:** 0

---

## EPIC-S2-01: Widget de ROI — Receita Recuperada pelo Sistema

*Demonstrar que o sistema se paga. Sem essa métrica visível, a profissional não percebe valor e cancela no mês 2.*

**Contexto:** A hipótese central é que RMAS (Receita Mensal Atribuível ao Sistema) > mensalidade.
Precisamos calcular e expor isso como API. Segue a regra de atribuição conservadora do MVP v6:
- Janela de 21 dias após `contacted_at`
- Apenas oportunidades que estavam `OVERDUE` no momento do contato (ignora orgânico `UPCOMING`)
- Exige `contact_status = BOOKED`
- Sem dupla contagem (`resolved_by_sale_id` único)

### Tarefas

- [x] `[BACK-S2-01]` **Domain: Motor de Atribuição de Receita** — ✅ Aprovado no review.
- [x] `[BACK-S2-02]` **Repository: Query de Oportunidades Atribuíveis** — ✅ Corrigido, ver AC-01
- [x] `[BACK-S2-03]` **Service: `AttributionService`** — ✅ Aprovado no review.
- [x] `[BACK-S2-04]` **API: `GET /api/v1/dashboard/roi`** — ✅ Aprovado no review.
- [x] `[BACK-S2-05]` **Testes: Attribution Domain** — ✅ Aprovado no review.

---

## EPIC-S2-02: Anti-No-Show — Lembretes D-1

*20% de no-show = R$ 420/mês perdidos. Reduzir para 10% já cobre a mensalidade.*

### Tarefas

- [x] `[BACK-S2-06]` **API: `GET /api/v1/sessions/unconfirmed`** — ✅ Aprovado no review.
- [x] `[BACK-S2-07]` **Schema: `UnconfirmedSessionOut`** — ✅ Aprovado no review.
- [x] `[BACK-S2-08]` **Domain: Template de Confirmação** — ✅ Aprovado no review.
- [x] `[BACK-S2-09]` **Model/Migration: Campo `confirmed_at`** — ✅ Aprovado no review.
- [x] `[BACK-S2-10]` **API: `POST /api/v1/sessions/{id}/confirm`** — ✅ Aprovado no review.
- [x] `[BACK-S2-11]` **Métricas de No-Show no Dashboard** — ✅ Aprovado no review.
- [x] `[BACK-S2-12]` **Testes: Anti-No-Show** — ✅ Aprovado no review.

---

## EPIC-S2-03: Importação em Lote de Pacientes (Quick Start)

*Resolver o problema do Dia Zero: a profissional não tem cadastro estruturado e precisa popular o sistema em < 15 minutos.*

### Tarefas

- [x] `[BACK-S2-13]` **Schema: `PatientBatchImport`** — ✅ Aprovado no review.
- [x] `[BACK-S2-14]` **Service: `PatientService.batch_import()`** — ✅ Aprovado no review.
- [x] `[BACK-S2-15]` **API: `POST /api/v1/patients/import`** — ✅ Corrigido, ver AC-07
- [x] `[BACK-S2-16]` **Testes: Importação em Lote** — ✅ Aprovado no review.

---

## EPIC-S2-04: Templates de Procedimentos (Onboarding Acelerado)

*Reduzir fricção no cadastro inicial: oferecer procedimentos pré-preenchidos comuns do mercado de estética.*

### Tarefas

- [x] `[BACK-S2-17]` **API: `GET /api/v1/procedures/templates`** — ✅ Corrigido, ver AC-02
- [x] `[BACK-S2-18]` **Domain: Catálogo de Templates** — ✅ Aprovado no review.
- [x] `[BACK-S2-19]` **API: `POST /api/v1/procedures/from-template`** — ✅ Aprovado no review.
- [x] `[BACK-S2-20]` **Testes: Templates** — ✅ Aprovado no review.

---

## 🔧 AÇÕES CORRETIVAS (Code Review — 2026-08-31)

*Itens identificados na revisão de código que devem ser corrigidos antes do deploy em produção.*

### ✅ AC-01: Query sem tenant scope na atribuição de ROI — CORRIGIDO (2026-09-04)
**Origem:** `BACK-S2-02`
**Arquivo:** `app/repositories/return_opportunity.py` — método `list_attributed()` (linha ~81)

**Problema:** O método usa `self._session.query(ReturnOpportunity, Sale)` ao invés do padrão `self._scoped()`. Isso faz a query **escapar do filtro de `professional_id`** imposto pelo `TenantRepository`. Embora o método adicione manualmente um `.where(ReturnOpportunity.professional_id == self._professional_id)`, isso viola o contrato do `TenantRepository` (docstring: "NENHUM método público devolve Query/Select sem filtro aplicado" via `_scoped()`).

**Risco:** Violação da Invariante I2. Se alguém remover o where manual no futuro (refactoring), haverá vazamento cross-tenant de dados financeiros.

**Fix requerido:**
- [x] Substituir `self._session.query(ReturnOpportunity, Sale)` por uma query usando `select()` com `self._scoped()` como base.
- Usar `select(ReturnOpportunity, Sale).select_from(self._scoped().subquery()).join(Sale, ...)` ou equivalente que mantenha o padrão 2.0-style do SQLAlchemy.
- Remover o `.where(ReturnOpportunity.professional_id == ...)` redundante — `_scoped()` já garante isso.
- Manter o `.where(Sale.professional_id == self._professional_id)` como defesa em profundidade para o join.

**Teste de validação:** O teste existente em `tests/test_attribution.py` deve continuar passando. Adicionalmente, confirmar que o teste de isolamento genérico (T-046) cobre esta rota.

**Evidência:** `app/repositories/return_opportunity.py::list_attributed` agora usa `aliased(ReturnOpportunity, self._scoped().subquery())` — o filtro de tenant vem do `_scoped()` padrão do `TenantRepository`, sem `.query()` cru e sem `where` manual redundante. `Sale.professional_id == self._professional_id` mantido como defesa em profundidade no join. `.venv/bin/pytest -q -k attribution` → 6 passed.

---

### ✅ AC-02: Rota de templates exigindo autenticação — CORRIGIDO (2026-09-04)
**Origem:** `BACK-S2-17`
**Arquivo:** `app/api/v1/procedures.py` — rota `GET /api/v1/procedures/templates` (linha ~27)

**Problema:** A rota injeta `svc: ProcedureSvc` como dependência FastAPI. `ProcedureSvc` resolve para `get_procedure_service()` que exige `CurrentProfessional` (JWT). Resultado: a rota retorna **HTTP 401** para chamadas anônimas.

**Requisito original:** A rota deveria ser **pública** (sem autenticação) para uso na landing page e no onboarding pré-login.

**Fix requerido:**
- [x] Remover a dependência `svc: ProcedureSvc` da rota `GET /templates`.
- Importar e chamar diretamente `list_procedure_templates()` de `app/domain/catalog/procedure_templates.py`.
- Converter os `ProcedureTemplateData` retornados para `ProcedureTemplateOut` diretamente no controller.
- A rota NÃO deve ter nenhum parâmetro que resolva para `CurrentProfessional` ou `DbSession`.

**Exemplo de implementação:**
```python
from app.domain.catalog.procedure_templates import list_procedure_templates

@router.get("/templates", response_model=list[ProcedureTemplateOut])
def get_procedure_templates() -> list[ProcedureTemplateOut]:
    """Templates públicos de procedimentos do mercado de estética (EPIC-S2-04)."""
    templates = list_procedure_templates()
    return [ProcedureTemplateOut.model_validate(t.__dict__) for t in templates]
```

**Teste de validação:** Adicionar teste em `tests/test_procedure_templates.py` que faz `GET /templates` **sem header Authorization** e espera 200.

**Evidência:** `app/api/v1/procedures.py::get_procedure_templates` não declara `ProcedureSvc` nem `DbSession` — chama `list_procedure_templates()` do domínio diretamente e converte para `ProcedureTemplateOut` no controller. `ProcedureService.list_templates()` (agora morto) foi removido. Teste `test_get_templates_route_is_public` em `tests/test_procedure_templates.py` chama `GET /api/v1/procedures/templates` sem header e confirma 200. `.venv/bin/pytest -q -k procedure_templates` → 5 passed.

---

### ✅ AC-07: Rate limit ausente na importação em lote — CORRIGIDO (2026-09-04)
**Origem:** `BACK-S2-15`
**Arquivo:** `app/api/v1/patients.py` — rota `POST /api/v1/patients/import` (linha ~23)

**Problema:** O backlog pedia rate limit suave de **3 chamadas/hora** por profissional para prevenir loops acidentais de importação. Não foi implementado.

**Fix requerido:**
- [x] Implementar rate limiting in-memory simples (aceitável para MVP):
  - `dict[UUID, list[datetime]]` mapeando `professional_id` → timestamps das últimas chamadas.
  - Antes de processar, verificar se houve ≥ 3 chamadas nos últimos 60 minutos.
  - Se excedido, retornar **HTTP 429 Too Many Requests** com header `Retry-After`.
  - Limpar entradas antigas do dict periodicamente (ou usar TTL).
- Alternativa: usar uma dependência FastAPI (`Depends`) com a lógica de rate limit.

**Teste de validação:** Adicionar teste que faz 4 chamadas consecutivas e verifica que a 4ª retorna 429.

**Evidência:** `app/core/rate_limit.py::InMemoryRateLimiter` (dict `professional_id` → timestamps, janela deslizante de 1h) plugado via dependência `PatientImportRateLimit` em `app/api/deps.py` e usado em `POST /api/v1/patients/import`. Excedido o limite, retorna 429 com header `Retry-After`. Teste `test_import_route_rate_limited_after_3_calls_per_hour` em `tests/test_patient_import.py` faz 4 chamadas reais contra a API e confirma a 4ª como 429. `.venv/bin/pytest -q -k patient_import` → 4 passed.

---

## Referência Cruzada: Riscos Endereçados

| Risco (Análise PO/PM) | EPIC que endereça | Status |
|---|---|---|
| R1 — Unit Economics Apertada | EPIC-S2-01 (Widget ROI) | ✅ Completo (AC-01 corrigido) |
| R2 — Cold Start / Dia Zero | EPIC-S2-03 + EPIC-S2-04 | ✅ Completo (AC-02, AC-07 corrigidos) |
| R5 — Anti-No-Show Ausente | EPIC-S2-02 (Lembretes D-1) | ✅ Completo |

---

## Critérios de Aceite Globais (aplicam a todas as tasks)

1. **Invariante I1:** Dinheiro em `NUMERIC(12,2)` → `Decimal` → `string` no JSON. Zero floats.
2. **Invariante I2:** `professional_id` extraído exclusivamente do JWT (`sub` claim).
3. **Invariante I7:** Valores sugeridos/estimados devem incluir flag `is_suggested` ou `is_estimated`.
4. **Testes:** Cada EPIC tem suite de testes dedicada. Coverage mínimo: happy path + edge cases documentados.
5. **Migrations:** Qualquer mudança de schema requer migration Alembic incremental (não alterar migrations existentes).
6. **Docs:** Atualizar docstrings dos endpoints com referência ao EPIC/TASK ID.
