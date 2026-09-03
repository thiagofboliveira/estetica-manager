---
name: dev-backend
description: Use when writing or modifying Python/FastAPI backend code in the Estética Manager project — endpoints, SQLAlchemy models, Alembic migrations, financial calculations, repositories, services, or backend tests
---

# DEV Backend — FastAPI · SQLAlchemy 2.0 · PostgreSQL

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 (**sync**, `psycopg2`) · PostgreSQL/Supabase · Pydantic v2 · Alembic · pytest

**Referência completa:** [backend/ENGENHARIA.md](../../../backend/ENGENHARIA.md) (as treze decisões) e [ENGENHARIA.md](../../../ENGENHARIA.md) (invariantes I1-I7). Esta skill é o resumo operacional — os detalhes e o *porquê* estão lá.

## As quatro regras que quebram o produto se violadas

### 1. Dinheiro nunca é float (I1)

`NUMERIC(12,2)` no banco → `Decimal` no Python → **string** no JSON.

```python
# ✅
from app.core.money import money, allocate
valor = money("1000.00")          # Decimal, ROUND_HALF_UP
partes = allocate(total, pesos)   # largest remainder — a soma FECHA

# ❌ float em qualquer ponto do caminho monetário
valor = 1000.00 * 0.30   # 300.00000000000006
```

Rateio **sempre** via `allocate()`. A soma das partes precisa fechar exatamente com o total; o último item absorve o resto.

Garantido por teste: `test_core_money_nao_usa_float`, `test_dominio_nao_usa_float`.

### 2. `professional_id` vem só do JWT (I2)

```python
# ✅ derivado do claim "sub" do JWT validado
professional_id = get_current_professional_id()

# ❌ NUNCA de query param, header, body ou path
professional_id = request.query_params["professional_id"]
```

Rota que não declara `DbSession` é pública. **É impossível obter uma `DbSession` sem passar pela validação do JWT** — essa é a cadeia que torna o vazamento impossível.

Garantido por teste: `test_nenhuma_rota_tem_professional_id_no_path`.

### 3. Toda query passa por `TenantRepository`

```python
# ✅
class MinhaRepo(TenantRepository):
    def listar(self):
        return self._session.execute(self._scoped()).scalars().all()

# ❌ query() cru escapa do filtro de tenant
self._session.query(Modelo)   # ruff banned-api barra isso
```

Três camadas: ruff `banned-api` + `test_nenhum_query_cru_fora_do_repositorio` + RLS no Postgres.

> ⚠️ **Dívida conhecida:** `app/repositories/return_opportunity.py:82` ainda usa `query()` cru. Está registrada em `docs/in_progress/BACKLOG_SPRINT2_backend.md`. Não copie esse padrão.

### 4. Snapshot congelado é imutável (I3)

Ao concluir uma venda, os valores **e a fórmula** são copiados para a `Sale` e nunca recalculados a partir da config atual.

```python
# ✅ campo novo de snapshot entra em FROZEN_FIELDS
FROZEN_FIELDS[Sale] = {..., "meu_campo_applied"}
```

Ao editar venda histórica: recalcule com a config **do momento original**, nunca com a de hoje.

Única exceção: `cost_realized` (muda quando sessões de pacote concluem ou expiram).

**Precedente real:** `is_anticipated` foi corrigido gravando `anticipates_all` em `Sale.snapshot_payload` no momento da venda — não lendo `financial_settings` atual. Se você precisa de uma config antiga, congele-a; não leia a atual.

Garantido por teste: `test_snapshot_immutability.py`.

## Tabela nova — o checklist que não pode falhar

```python
# Na migration:
# 1. professional_id NOT NULL (desnormalizado, mesmo com FK indireta)
# 2. RLS: ENABLE + FORCE + policy com USING e WITH CHECK
op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
op.execute(f"""
    CREATE POLICY {t}_tenant ON {t}
      FOR ALL TO estetica_app
      USING (professional_id = current_setting('app.professional_id')::uuid)
      WITH CHECK (professional_id = current_setting('app.professional_id')::uuid)
""")
# 3. GRANT para estetica_app
# 4. Índice liderando por professional_id
```

`WITH CHECK` sem `USING` deixa escrever no tenant alheio. `ENABLE` sem `FORCE` não vale para o owner da tabela.

Garantido por teste: `test_toda_tabela_com_professional_id_tem_rls_nas_migrations` — **pega migration nova sem policy no CI.**

## Camadas

```
api/v1/      → rota fina: valida, delega, traduz erro em HTTP
services/    → orquestra, abre transação, monta snapshot
domain/      → cálculo PURO (sem SQLAlchemy, sem FastAPI)
repositories/→ acesso a dado, sempre com tenant
models/      → SQLAlchemy
schemas/     → Pydantic (InputSchema com extra="forbid")
```

**`app/domain/` não importa `models`, `schemas` nem `sqlalchemy`.** Garantido por `test_dominio_nao_importa_infraestrutura`. É isso que torna o cálculo testável em milissegundos e reutilizável (ex.: um simulador de preço reusa `calculate_sale()` sem tocar banco).

**Router devolve 404, nunca 403** para recurso de outro tenant. 403 confirma que o recurso existe.

## Datas (I4)

```python
# ✅ converte para o fuso da profissional ANTES de agrupar por dia/mês
from app.core.tz import today_in_timezone
hoje = today_in_timezone(professional.timezone)

# ❌ trunca em UTC — venda das 22h em SP cai no dia seguinte
datetime.now(UTC).date()
```

Exceção deliberada: `return_opportunities.due_date` é `DATE` (retorno é dia civil, não instante).

## Testes

```bash
.venv/bin/pytest -q                      # tudo
.venv/bin/pytest -q -k <feature>          # focado
.venv/bin/ruff check .                    # lint
.venv/bin/alembic upgrade head            # migrations
```

Ambiente local: Postgres em `localhost:5434` (ver `docker-compose.dev.yml`), `.env` deve bater com essa porta.

**Se toca cálculo financeiro:** a matriz de 5 configurações (`test_matriz_de_5_configuracoes`) precisa passar. Valores oficiais: A=350, B=365, C=365, **D=400**, E=650. `fee_payer` é ortogonal a `split_base` e se aplica sempre.

**Se toca dado de paciente:** teste cross-tenant (A não vê nada de B).

Teste de integração roda contra Postgres real, não mock.

## Máquinas de estado

Status novo entra na tabela de transições explícita (`SESSION_TRANSITIONS`, `SALE_TRANSITIONS`, `ReturnOpportunityStatus`). Transição inválida levanta erro; não é `if` espalhado pelo service.

## Checklist de PR

- [ ] Nenhum `float` em caminho monetário
- [ ] `Decimal` serializado como string no JSON
- [ ] Rateio usa `allocate()` e a soma fecha
- [ ] Query nova passa por `TenantRepository`
- [ ] Tabela nova tem RLS + `FORCE` + `USING` + `WITH CHECK` + GRANT
- [ ] Índice novo lidera por `professional_id`
- [ ] Campo de snapshot está em `FROZEN_FIELDS`
- [ ] Status novo está na tabela de transições
- [ ] Recurso não encontrado devolve 404, nunca 403
- [ ] Se toca cálculo: matriz de 5 configurações passa
- [ ] `pytest -q` e `ruff check .` limpos

## Red Flags — pare

- Preciso de `float` "só para exibir" → **não. `Decimal` → string**
- Vou ler `financial_settings` para reconstituir venda antiga → **viola I3. Congele no snapshot**
- Vou usar `session.query()` "só nesse caso" → **ruff barra. Use `_scoped()`**
- Tabela nova sem policy, "adiciono depois" → **o CI pega, e o vazamento é evento de extinção**
- Vou devolver 403 para recurso de outro tenant → **404. 403 confirma existência**
- `date()` direto em `datetime.now(UTC)` → **use `today_in_timezone()`**
- Vou importar `models` no `domain/` → **teste de arquitetura quebra**
- Endpoint `/dev/*` novo → **precisa de teste provando que morre fora de `ENV=development`**
