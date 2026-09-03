# Estética Manager

Micro-SaaS de **gestão financeira e retenção** para esteticistas autônomas. Vende duas coisas: saber o **lucro real** de cada procedimento, e **não esquecer de chamar a paciente de volta**.

## Skills deste projeto

Invoque a skill correspondente **antes** de agir:

| Trabalho | Skill |
|---|---|
| Escopo, backlog, tasks novas, priorização, mover docs entre `finished`/`in_progress`/`pending` | `po-escopo` |
| Python/FastAPI: endpoints, models, migrations, cálculo, repositories, testes | `dev-backend` |
| React/TS: telas, componentes, forms, hooks, dinheiro no front, CSS | `dev-frontend` |

## As sete invariantes

Detalhe e o *porquê* em [ENGENHARIA.md](ENGENHARIA.md). Cada uma existe porque algo concreto quebra:

| # | Invariante |
|---|---|
| I1 | Dinheiro nunca é float — `NUMERIC(12,2)` → `Decimal` → **string** no JSON → `decimal.js` |
| I2 | `professional_id` vem só do JWT validado |
| I3 | Snapshot congelado é imutável (a fórmula também congela) |
| I4 | Toda data é `TIMESTAMPTZ` em UTC, convertida ao fuso dela antes de agrupar |
| I5 | Dinheiro vive na `Sale`, nunca na `Session` |
| I6 | Oportunidade de retorno nasce só em `COMPLETED`/`NO_SHOW` |
| I7 | Número estimado é exibido como estimado |

## Idioma

| Camada | Idioma |
|---|---|
| Banco, código, API | **Inglês** (`sales`, `net_profit`) |
| UI, mensagens ao usuário | **Português** ("Lucro real", "Quem devo chamar hoje?") |

Não misture.

## Ambiente local

```bash
docker compose -f docker-compose.dev.yml up -d          # Postgres :5434
cd backend && .venv/bin/alembic upgrade head
cd backend && .venv/bin/python -m uvicorn app.main:app --port 8010 --reload
cd frontend && npm run dev                              # :5173
```

`VITE_DEV_AUTH=true` no `frontend/.env.local` dispensa Supabase (botão "Entrar com Conta de Teste").

⚠️ **`backend/.env` precisa apontar para a porta 5434** — o compose deste branch usa 5434, e um `.env` herdado de outro branch pode apontar 5435.
⚠️ **`frontend/package.json` tem `@oxlint/binding-win32-x64-msvc`** como devDependency, que quebra `npm install` em Linux/Mac (`EBADPLATFORM`). Registrado como task `V1-03`.

## Verificação — "DONE exige evidência"

```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check .
cd frontend && npx tsc -b && npm run lint
```

Nunca marque `[x]` por ter escrito o código. Teste passando, ou tela clicada contra a API real (não mock) com o dado confirmado no Postgres.

## Documentação

| Onde | O quê |
|---|---|
| [docs/README.md](docs/README.md) | Índice por estado: `finished/`, `in_progress/`, `pending/` |
| [BACKLOG.md](BACKLOG.md) | Índice de coordenação das features entregues |
| [docs/pending/BACKLOG_VERSAO_COMPLETA.md](docs/pending/BACKLOG_VERSAO_COMPLETA.md) | Backlog da versão completa (74 tasks, V1-V8) |
| [ENTREVISTA.md](ENTREVISTA.md) | Dados reais da cliente zero — use para embasar decisão de produto |
| [MVP spec](MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) | Escopo original e visão de produto |

> ⚠️ **A documentação já divergiu do código antes.** Três `bugs.md` listavam 5 bugs como abertos — todos corrigidos. Um backlog dizia "100% concluído" com 3 itens abertos. **Audite no código antes de confiar em qualquer status.**

## Commits

```
feat(sales): adiciona rateio de desconto por item
fix(retention): oportunidade duplicada em paciente multi-procedimento
```

Escopos: `sales`, `retention`, `financial`, `patients`, `procedures`, `auth`, `agenda`, `infra`.

## Princípio de produto

> Isso ajuda a profissional a **ganhar mais dinheiro**, **perder menos dinheiro**, **economizar tempo**, ou **reter mais pacientes**? Se não → provavelmente não pertence ao produto agora.

**Corolário:** um número errado é pior que nenhum número.
