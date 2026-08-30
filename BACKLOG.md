# Backlog — Coordenação

Índice dos backlogs por projeto. **Não contém tasks** — cada repo mantém as suas.

| Projeto | Backlog | Tasks | Progresso |
|---|---|---:|---:|
| Backend (FastAPI) | [backend/BACKLOG.md](backend/BACKLOG.md) | 86 | 78/86 (91% · 100% P0) |
| Frontend (React) | [frontend/BACKLOG.md](frontend/BACKLOG.md) | 36 | 36/36 (100%) |
| Produto / validação | §Produto abaixo | 5 | 1/5 (20%) |
| | **Total MVP** | **127** | **91%** |

**Guias de engenharia:** [ENGENHARIA.md](ENGENHARIA.md) (invariantes) · [backend](backend/ENGENHARIA.md) · [frontend](frontend/ENGENHARIA.md)

**Fonte de escopo:** [MVP v7](MVP%20—%20Micro-SaaS%20para%20Gestão%20Financeira%20e%20Retenção%20em%20Estética%20\(v6\).md) — mudança de escopo vai lá primeiro; os backlogs refletem, não decidem. (Arquivo continua nomeado `v6` — a v7 é a seção §12.5 adicionada dentro dele, não um novo arquivo.)

**Atualizado:** 2026-08-30

---

## ✅ Bloqueio resolvido — Fase 2 destravada

| ID | Task | Status | Dono |
|---|---|:--:|---|
| T-048 | Entrevista de calibração dos eixos | `[x]` | Produto |

📋 **Roteiro: [ENTREVISTA.md](ENTREVISTA.md)** — **duas rodadas respondidas em 2026-08-29** (via Thiago, não gravação formal). Ver seções "Respostas parciais" e "Respostas rodada 2" no fim do arquivo.

| Eixo | Pergunta em linguagem natural | Status | Impacto se ignorado |
|---|---|:--:|---|
| E1 | "A taxa do cartão sai do seu bolso ou a clínica cobre?" | `[x]` Pix majoritário, sem taxa. Default `PROFESSIONAL` p/ cartão raro | — |
| E2 | "A clínica calcula sobre o valor cheio ou sobre o que sobra?" | `[x]` não se aplica (sem split) | — |
| E4 | "Você parcela? Até quantas vezes?" | `[x]` não parcela — cobra por sessão | — |
| E5 | "Botox de 20 e de 50 unidades custam o mesmo pra você?" | `[x]` varia → `cost_override` é P0 | — |
| E6 | "A clínica fica com a mesma % em todo procedimento?" | `[x]` não se aplica (sem split) | — |
| E7 | "Você antecipa o dinheiro do cartão?" | `[x]` **Não** — Pix cai na hora, não há recebível | Segue **P1** |
| E8 | "Os pacotes têm prazo para usar?" | `[x]` sem prazo | — |

> ✅ **Achados das três rodadas:** (1) ela não tem split de clínica — paga aluguel fixo + água/luz/lixo biológico/taxa anual de vigilância/educação. Virou eixo novo: despesas fixas (MVP v7 §12.5, com `periodicity` MONTHLY\|YEARLY). (2) Baseline **resolvido**: custo R$1.300/mês, lucro R$800/mês, ~10 atendimentos/mês, no-show ~20%. (3) Hipótese de retenção **confirmada** — ela precisa lembrar o retorno ou o cliente não volta. (4) Incidente real de agenda gerou `bookings` (§16.6). (5) Pix por sessão **fecha E7** e faz "A receber" ser sempre zero no caso dela.
>
> ⚠️ **Risco de validação registrado:** como ela só usa Pix, a distinção competência-vs-caixa (TASK-021) **não será exercitada** nos 30 dias de teste. Esse caminho depende de teste automatizado, não de uso real.

---

## Produto e validação

Tasks que não são de código.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| T-048 | Entrevista de calibração | `[x]` | — | ✅ 3 rodadas em 2026-08-29 — E1-E8 fechados. Ver `ENTREVISTA.md` |
| T-049 | Configurar operação real | `[ ]` | T-047, F-030 | Pacientes **com consentimento** |
| T-050 | Registrar baseline | `[~]` | T-049 | Parcial: custo R$1.300, lucro R$800, ~10 atend./mês, no-show 20%. Falta **taxa de retorno %** (o contrafactual) e faturamento bruto |
| T-051 | Rodar 30 dias | `[ ]` | T-050 | 10 perguntas de validação (§24 da v6) |
| P-001 | Protótipo da tela de venda | `[ ]` | — | Papel/Figma **antes** de F-014 |

---

## Sincronia entre os dois projetos

Trabalhe em paralelo. Frontend nunca espera "a API ficar pronta" — as sete telas foram a maior causa da subestimativa original.

```
Semana   Backend                          Frontend
──────────────────────────────────────────────────────────
  0      T-048 entrevista (1 dia)         P-001 protótipo em papel
──────────────────────────────────────────────────────────
  1      T-001c driver · T-001e deps      F-001 setup
         T-001d money · T-001f allocate   F-001b tipo Money
         T-001g property tests            [ambos: dinheiro primeiro]
  1-3    T-002..006 · T-057a role         F-002, F-003
         T-058 RLS · T-046 isolamento
         [auth + isolamento PROVADOS]
  3-5    T-007..011                       F-011, F-012
  5-9    T-012..021 · T-043 · T-044       F-014, F-013
         [motor provado em 5 configs]     [depois do protótipo]
  9-12   T-025..034                       F-015, F-017, F-018, F-021
 12-15   T-045, T-059..062, T-047         F-030, F-031
──────────────────────────────────────────────────────────
 15+     Cliente zero (T-049..051)
```

> 🆕 **Semana 1 começa pelo dinheiro, nos dois lados.** `allocate()` e o tipo `Money` são puros, não dependem de banco nem de API, e um erro ali é **não-retrofitável** — os valores ficam congelados e não podem ser recalculados depois.

### Contrato de API

Mudança nestes pontos quebra o front — avise antes.

| Endpoint | Backend | Frontend |
|---|---|---|
| Auth (JWT Supabase) | T-006 | F-001a, F-003 |
| `/patients`, `/procedures` | T-010, T-011 | F-011, F-012 |
| `/financial-settings` | T-007 | F-012a |
| `POST /sales` | T-015 | F-014 |
| `GET /dashboard` | T-022 | F-013 |
| `GET /retention/opportunities` | T-029 | F-015 |
| `GET /sessions?from&to` | T-032 | F-017 |
| `GET /packages/open` | T-034 | F-018 |

> 🔴 **Regra que atravessa os dois projetos:** valores monetários trafegam como **string** no JSON. `number` em JS é float64 — converter reintroduz no front o erro que o backend evitou com `Decimal`.

### Dois contratos a fechar 🆕

Vieram da análise de engenharia e precisam de acordo entre os dois lados:

| # | Contrato | Backend | Frontend | Sem isso |
|---|---|---|---|---|
| C-1 | **Idempotência do `POST /sales`** — mesma chave + mesmo corpo → 200 com a venda existente (não 409, não duplica). TTL 24h | T-015 | F-014a | `disabled` é a única defesa, e ela não sobrevive ao 4G do salão |
| C-2 | **`hasAnyData` no `GET /dashboard`** — 1 booleano | T-022 | F-031 | Empty state não distingue "primeira vez" de "mês sem venda" — erra a mensagem na sessão mais crítica |

---

## Cinco regras de sequência

1. **T-001c (sync vs async) antes de escrever a primeira linha.** O `pyproject.toml` atual é contraditório; decidir depois custa refactor de toda camada de dados.
2. **T-001f + T-001g (`allocate` + property tests) na semana 1.** 🆕 São puros, rodam em milissegundos, e um erro de rateio é **não-retrofitável** — os valores congelam e não podem ser recalculados.
3. **T-057a (role `NOBYPASSRLS`) antes de T-058.** 🆕 Sem ela as policies existem, os testes passam, e a proteção é **zero**.
4. **T-044 (matriz de 5 configurações) antes de qualquer tela financeira.** Cálculo não provado = número errado com aparência de certo.
5. **T-046 (isolamento genérico) antes das rotas de negócio.** Escrito antes, cada rota nova nasce coberta. Escrito depois, vira teatro de isolamento.

---

## Se o prazo apertar

Cortar escopo, nunca comprimir prazo.

| # | Cortar | Impacto |
|---|---|---|
| 1 | F-040 dashboard de impacto (manter os dados) | Nenhum na validação |
| 2 | T-024 / ranking de procedimentos | Perde insight, não o núcleo |
| 3 | T-023 filtros além de "este mês" | Menor |
| 4 | F-014b tela de pacote (manter migrations) | Pacote entra depois **sem migration nova** |

**Nunca cortáveis:** tipo monetário, timezone, RLS, snapshot congelado, `return_opportunities`, edição de venda, modelo Venda/Item/Sessão.

---

## Manutenção

- Atualize o status no momento da mudança, não em lote.
- `[!]` BLOCKED exige motivo na coluna Nota.
- Progresso por projeto vive no backlog do projeto; aqui só o consolidado.
- Task que passar dias em `[~]` deve ser quebrada em subtasks.
