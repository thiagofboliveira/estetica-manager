# Motor de Retenção (T-025..T-031) — Design

**Data:** 2026-09-01
**Escopo do backlog:** `backend/BACKLOG.md` T-025, T-026, T-027 (já implementada), T-028, T-029, T-030, T-031, T-045, T-045a, T-045b — mais **T-016** (`PATCH /sessions/{id}`), adicionada como pré-requisito descoberto durante o design.
**Fonte de verdade do domínio:** MVP v7.1 §11.6, §14 (EPIC-10), §15 (EPIC-11), §18/19 (atribuição — fora de escopo aqui), §20.3/§20.4.

## Por que T-016 entra no escopo

O backlog original deixa `T-016` (`PATCH /sessions/{id}`) fora desta entrega. Mas o motor de retorno nasce quando um item de venda se esgota (§11.6: "última sessão `COMPLETED` do item + `return_interval_applied` = `due_date`") — e hoje **nenhum caminho de código** move uma sessão para `COMPLETED`. Sem T-016, o motor de retenção não tem gatilho em produção; ficaria coberto só por testes que chamam o service diretamente, o que não é aceitável para uma feature P0 do produto. T-016 entra com o escopo mínimo necessário: validar transição via a máquina de estados já pronta (`session_state_machine.py`) e persistir.

## Modelo de dados

### `sessions` (sem migration nova)

`completed_at: TIMESTAMP(timezone=True) | None` já existe (`app/models/session.py`). T-016 apenas o preenche quando o novo status é `COMPLETED`.

### `return_opportunities` (nova tabela — migration `0005_return_opportunities.py`)

Segue o padrão de `sale_items`/`sessions`: `TenantModel` + FKs compostas `(id, professional_id)` contra as tabelas pai, para RLS sem JOIN e defesa em profundidade.

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | UUID PK | |
| `professional_id` | UUID FK→professionals | herdado de `TenantModel` |
| `patient_id` | UUID | FK composta `(patients.id, patients.professional_id)` |
| `procedure_id` | UUID | FK composta `(procedures.id, procedures.professional_id)` |
| `source_sale_item_id` | UUID | FK composta `(sale_items.id, sale_items.professional_id)` |
| `due_date` | DATE | calculado 1x na criação (§11.6), não recalculado depois |
| `potential_value` | NUMERIC(12,2) | congelado de `sale_item.unit_price × sale_item.quantity` na criação — mesma disciplina de snapshot usada em `sales`/`sale_items` (I3): o valor não muda se o preço do procedimento mudar depois |
| `status` | enum `ReturnOpportunityStatus` | ver máquina de estados abaixo |
| `contacted_at` | TIMESTAMPTZ null | |
| `contact_channel` | enum `WHATSAPP\|PHONE\|IN_PERSON\|OTHER` null | |
| `contact_status` | enum `ReturnOpportunityStatus` subconjunto pós-contato, ou coluna própria — **decisão:** reaproveitar `status` (ver nota abaixo), não duplicar em `contact_status` |
| `resolved_by_sale_id` | UUID null | FK composta `(sales.id, sales.professional_id)`, `ondelete=RESTRICT` |
| `dismissed_at` | TIMESTAMPTZ null | |
| `created_at`/`updated_at` | herdado de `TimestampMixin` | |

**Nota sobre `contact_status`:** o MVP lista `contact_status` como campo separado de `status` na tabela (§14), mas a máquina de estados de §14 já usa os mesmos nomes (`CONTACTED`, `BOOKED`, `DECLINED`, `NO_RESPONSE`) como *status* da oportunidade. Duplicar em duas colunas cria duas fontes de verdade para o mesmo fato. Vou implementar com **uma única coluna `status`** cobrindo o ciclo inteiro (`OPEN → CONTACTED → BOOKED/DECLINED/NO_RESPONSE → CLOSED`, mais `DISMISSED`), e sem coluna `contact_status` separada. `PATCH /retention/opportunities/{id}` registra `contacted_at` + `contact_channel` + a transição de `status` num único request.

**Índices** (§20.4): `(professional_id, due_date, status)` em `return_opportunities` para a query de listagem; `(professional_id, completed_at)` em `sessions` — **confirmado que não existe ainda** (grep no schema atual), criado nesta mesma migration.

**Unicidade:** `UniqueConstraint(source_sale_item_id)` — um item de venda gera no máximo uma oportunidade aberta (esgota uma vez). Se uma oportunidade for fechada (`CLOSED`) e o item não gerar outra venda do mesmo item (não deveria acontecer, mas por segurança), a constraint deve permitir múltiplas linhas históricas — **decisão:** não usar `UniqueConstraint` simples; usar índice parcial `WHERE status NOT IN ('CLOSED')` para permitir no máximo uma oportunidade *ativa* por `source_sale_item_id`, mas preservar histórico.

## Máquina de estados — `ReturnOpportunityStatus`

Novo arquivo `app/domain/retention/return_opportunity_state_machine.py`, espelhando exatamente `session_state_machine.py`:

```python
class ReturnOpportunityStatus(StrEnum):
    OPEN = "OPEN"
    CONTACTED = "CONTACTED"
    BOOKED = "BOOKED"
    DECLINED = "DECLINED"
    NO_RESPONSE = "NO_RESPONSE"
    DISMISSED = "DISMISSED"
    CLOSED = "CLOSED"

RETURN_OPPORTUNITY_TRANSITIONS = {
    OPEN: {CONTACTED, DISMISSED},
    CONTACTED: {BOOKED, DECLINED, NO_RESPONSE},
    NO_RESPONSE: {CONTACTED},
    BOOKED: {CLOSED},
    DECLINED: {CLOSED},
    DISMISSED: {},       # terminal
    CLOSED: {},           # terminal
}
```

`validate_transition()` idêntica em forma a `session_state_machine.validate_transition()`. Teste espelhando `test_todo_status_esta_na_tabela`.

**Fechamento automático por venda (T-028)** é uma transição de sistema, não do usuário: `OPEN`/`CONTACTED` → `CLOSED` com `resolved_by_sale_id` preenchido. Implementado como uma chamada direta a `validate_transition(current, CLOSED)` dentro do service — mesma disciplina de nunca confiar no chamador.

## Cálculo da janela — `app/domain/retention/window.py` (puro)

```python
def calculate_due_date(completed_at: date, return_interval_days: int) -> date:
    return completed_at + timedelta(days=return_interval_days)

class Timing(StrEnum):
    UPCOMING = "UPCOMING"
    DUE = "DUE"
    OVERDUE = "OVERDUE"

def classify_timing(due_date: date, today: date) -> Timing:
    delta = (due_date - today).days
    if delta > 7:
        return Timing.UPCOMING
    if delta < -7:
        return Timing.OVERDUE
    return Timing.DUE
```

`Timing` nunca é persistido — computado em toda leitura, no fuso da profissional (`today_in_timezone`, mesma disciplina de I4 usada em `period.py`).

## Gatilho de criação — dentro de T-016

`PATCH /sessions/{id}` (`app/api/v1/sessions.py`, novo):

1. Busca a sessão via repositório tenant-scoped (404 se não existe).
2. `validate_transition(session.status, novo_status)` — 409 se inválida (mesmo padrão de erro de domínio → HTTP usado em `sales.py`).
3. Atualiza `status`; se `novo_status == COMPLETED`, seta `completed_at = now_in_timezone(professional)`.
4. Chama `RetentionService.check_and_create_opportunity(sale_item_id)`:
   - Busca todas as sessions do `sale_item_id`.
   - Se **nenhuma** estiver em `PENDING`/`SCHEDULED`/`CONFIRMED` (item esgotado) **e** existir ao menos uma `COMPLETED` **e** `sale_item.return_interval_applied is not None` (produtos sem intervalo não geram retorno) **e** não existir já uma oportunidade ativa (não-`CLOSED`) para esse `source_sale_item_id`:
     - `due_date = calculate_due_date(max(completed_at das sessions COMPLETED), return_interval_applied)`
     - `potential_value = sale_item.unit_price * sale_item.quantity`
     - Cria `ReturnOpportunity(status=OPEN, ...)`.
5. Tudo na mesma transação (mesmo padrão do `get_tenant_session`).

Isso cobre T-045a (pacote com sessão `PENDING` não gera oportunidade — condição de "nenhuma pendente/agendada" falha) e T-045b indiretamente (a oportunidade só nasce quando o item esgota, nunca antes).

## Regra de fechamento — dentro de `SaleService.create()` (T-028)

Após persistir a nova venda e seus itens (mesma transação):

```python
for procedure_id in {item.procedure_id for item in new_sale.items}:
    RetentionService.close_open_opportunities(
        patient_id=sale.patient_id,
        procedure_id=procedure_id,
        resolved_by_sale_id=sale.id,
    )
```

`close_open_opportunities` busca oportunidades `OPEN`/`CONTACTED`/`NO_RESPONSE` do par `(patient_id, procedure_id)`, aplica `validate_transition(status, CLOSED)`, seta `resolved_by_sale_id`. Isso cobre T-045 (ciclo completo) — a nova oportunidade do mesmo procedimento só nasce depois, quando o novo item esgotar (T-016 cuida disso), nunca nesta chamada.

## Endpoints

### `GET /retention/opportunities`

Query params: nenhum obrigatório. Regras de negócio na resposta (T-029, T-030, T-031 combinados):

1. Busca todas as oportunidades **não-`CLOSED`** e **não-`DISMISSED`** do tenant.
2. **Supressão (§15, P0):** exclui pacientes com `contacted_at` nos últimos 14 dias (configurável futuramente; hardcoded 14 por ora) — aplicada por paciente, não por oportunidade individual.
3. **Consentimento:** paciente sem `consent_whatsapp=True` ou com `opted_out_at` preenchido não é excluída da lista, mas o botão de contato vem desabilitado com motivo — decisão de UI, mas o endpoint expõe `can_contact: bool` + `cannot_contact_reason: str | None` por paciente.
4. Agrupa por paciente (T-030): 1 card por paciente, procedimento com `due_date` mais atrasado como principal, demais como secundários.
5. Ordena por soma de `potential_value` do paciente, decrescente.
6. `timing` computado por `classify_timing()` no fuso da profissional.

Formato de resposta (schema `PatientRetentionOut`):
```json
[{
  "patient_id": "uuid",
  "patient_name": "Maria",
  "phone": "+5511999999999",
  "can_contact": true,
  "cannot_contact_reason": null,
  "total_potential_value": "1300.00",
  "opportunities": [
    {"id": "uuid", "procedure": "Botox", "due_date": "2026-08-28", "timing": "OVERDUE", "status": "OPEN", "potential_value": "1000.00"},
    {"id": "uuid", "procedure": "Skinbooster", "due_date": "2026-09-05", "timing": "DUE", "status": "OPEN", "potential_value": "300.00"}
  ]
}]
```

### `PATCH /retention/opportunities/{id}`

Body (`InputSchema`, `extra=forbid`): `{status, contact_channel?, contacted_at?}` — ou dois endpoints separados (`/dismiss` e `/contact`)? **Decisão:** um único `PATCH` com `status` obrigatório e `contact_channel` obrigatório apenas quando `status in (CONTACTED, ...)`. Valida via `validate_transition`. 409 em transição inválida — mesmo padrão de `sales.py`/`session_state_machine`.

## Testes

**Puros** (sem DB): `tests/test_return_opportunity_state_machine.py` (espelha `test_session_state_machine.py`, incl. teste de cobertura total do enum) e `tests/test_retention_window.py` (`calculate_due_date`, `classify_timing`, casos de borda ±7 dias).

**Integração real (Postgres)** — `tests/test_retention_integration.py`, mesmo padrão de `test_sales_integration.py`/`test_fixed_expenses_integration.py`:
- T-045: ciclo completo — vende pacote → completa todas as sessões via `PATCH /sessions/{id}` → oportunidade `OPEN` aparece em `GET /retention/opportunities` → `PATCH` para `CONTACTED` → nova venda do mesmo procedimento → oportunidade correspondente vira `CLOSED` com `resolved_by_sale_id` correto.
- T-045a: pacote de N sessões com pelo menos uma `PENDING` — paciente não aparece na lista.
- T-045b: pacote de 10 sessões do mesmo item completadas — gera exatamente 1 oportunidade, não 10.
- Supressão de 14 dias: paciente contatada há 5 dias não aparece; há 20 dias aparece.
- Pacote com itens de procedimentos diferentes gera até 2 oportunidades independentes (§11.6).

## Fora de escopo (explícito)

- **T-090 (`GET /impact`)** e toda a lógica de atribuição de receita (§18/19, janela de 21 dias, `resolved_by_sale_id` como prova de conversão) — esquema já suporta, cálculo fica para Fase 5+.
- **T-034/T-034a/T-034b (agenda/bookings)** — fora, não bloqueia retenção.
- Configurabilidade do período de supressão (14 dias fica hardcoded).
- Templates de mensagem de reativação (T-103, P1/Fase 5+).
