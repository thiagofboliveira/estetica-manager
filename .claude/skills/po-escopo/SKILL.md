---
name: po-escopo
description: Use when defining scope, adding tasks to a backlog, prioritizing work, reviewing product direction, writing specs, or moving documents between docs/finished, docs/in_progress and docs/pending in the Estética Manager project
---

# PO/PM — Escopo e Backlog

## Overview

Este produto vende **clareza financeira e retenção** para esteticistas autônomas. Toda decisão de escopo passa por um filtro só:

> Isso ajuda a profissional a **ganhar mais dinheiro**, **perder menos dinheiro**, **economizar tempo**, ou **reter mais pacientes**? Se não → provavelmente não pertence ao produto agora.

## A regra que não se negocia: auditar antes de escrever

**Nunca classifique uma task lendo o cabeçalho de um documento. Verifique no código.**

Este projeto já produziu documentação que mentia: três `bugs.md` listavam 5 bugs como abertos — **todos os 5 já estavam corrigidos**. Um `BACKLOG.md` declarava "Sprint 2: 100% Concluído" com **3 itens genuinamente abertos**.

```bash
# Antes de marcar [x] ou mover para finished/ — prove:
grep -rn "<simbolo|rota|coluna>" backend/app frontend/src
ls backend/tests/ | grep <feature>
.venv/bin/pytest -q -k <feature>
```

| Se o doc diz | Verifique |
|---|---|
| "bug aberto" | O código já pode estar corrigido — `grep` o arquivo e a linha citados |
| "100% concluído" | Conte os `- [ ]` restantes: `grep -c '^\- \[ \]' <arquivo>` |
| "endpoint existe" | `grep include_router backend/app/main.py` |
| "tela pronta" | `grep 'path: "' frontend/src/app/router.tsx` — pode ser `PlaceholderPage` |

## Organização dos documentos

Classificação por **estado de execução**, não por assunto. Ver [docs/README.md](../../../docs/README.md).

| Pasta | Entra quando | Sai quando |
|---|---|---|
| `docs/pending/` | Escopo definido, nada começado | Alguém começa → `in_progress/` |
| `docs/in_progress/` | Tem pelo menos um `[x]` e um `[ ]` | Último `[ ]` fecha → `finished/` |
| `docs/finished/` | **Todos** os itens `[x]`, com evidência | Nunca (histórico) |

Documentos **atemporais** não entram nessas pastas: `ENGENHARIA.md`, `ENTREVISTA.md`, `requisitos.md`, o MVP spec, `LGPD_CONTRATO_OPERADOR.md`.

Mova sempre com `git mv` — preserva histórico. Ao mover, corrija os links relativos que apontavam para o caminho antigo e valide que resolvem.

## Anatomia de uma task

Toda task nova entra em tabela, nunca em prosa:

```markdown
| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `V2-05` | `POST /signup` — cadastro público de clínica | `[ ]` | V2-03 | Numa transação: `clinic` + `user` admin + `professional` + `financial_settings` (defaults §8.1) + `subscription` TRIALING. **Hoje é impossível sem SQL manual** |
```

**A coluna Nota carrega o *porquê*, não o *o quê*.** "Criar endpoint de signup" é redundante com o título. "Hoje é impossível sem SQL manual" é a informação que justifica a prioridade.

Status: `[ ]` TODO · `[~]` WIP · `[x]` DONE · `[!]` BLOCKED (exige motivo na Nota) · `[-]` adiado

IDs: prefixo por épico, sem colidir com os existentes (`BACK-*`, `FRONT-*`, `TASK-BACK-S2/S3-*`, `V1-*` a `V8-*`).

## Definition of Done

Uma task só é `[x]` quando:

- [ ] Teste automatizado cobre o caminho principal
- [ ] Nenhuma invariante de `ENGENHARIA.md` foi violada
- [ ] Se toca dinheiro: passa na matriz de 5 configurações
- [ ] Se toca dado de paciente: respeita RLS e foi testado cross-tenant
- [ ] Rodou contra a API/banco real, **não mock**
- [ ] Se toca cobrança: webhook idempotente e assinatura do provedor verificada

**DONE exige evidência.** Não marque por ter escrito o código.

## Configuração vs. Capacidade

A distinção mais importante ao avaliar um pedido novo:

| | Configuração | Capacidade |
|---|---|---|
| O que é | Campo que varia por profissional | Estrutura que existe ou não |
| Exemplo | "A taxa é dela ou da clínica?" | "O sistema suporta pacotes?" |
| Custo de adiar | Migration barata, uma coluna | **Reescrever o núcleo** |
| Pode esperar? | Sim, se o default for honesto | **Não** |

```text
Se a próxima cliente fizer diferente:
[ ] É um campo?        → configuração, siga
[ ] É uma tabela nova? → capacidade, decida ANTES de codar
[ ] É impossível?      → você construiu para uma pessoa
```

## Cortar escopo, nunca comprimir prazo

Quando o prazo aperta, corte features. Nunca reduza a estimativa das que ficam.

**Não cortáveis** (caros de retrofitar): tipo monetário, timezone, RLS, snapshot congelado, entidade de retenção, edição de venda, modelo Venda/Item/Sessão.

## Ao propor features novas

1. **Audite o estado real primeiro** (regra acima). Este projeto tem mais implementado do que os docs dizem — propor o que já existe queima confiança.
2. **Nomeie o concorrente.** "Concorrentes estabelecidos" sem nome não é análise. O concorrente real aqui é o **caderno + WhatsApp + Excel**, não o Trinks — a arma contra inércia é *time-to-value*, não quantidade de feature.
3. **Ligue à entrevista.** `ENTREVISTA.md` tem dados reais: no-show ~20%, custo R$1.300/mês, lucro R$800/mês, ~10 atendimentos/mês, impulsionamento subiu de R$11 → R$50 e parou de converter. Feature que responde a um desses fatos tem lastro; o resto é hipótese.
4. **Porta de decisão antes de investimento grande.** Não construa cobrança antes de provar que alguém paga. Escreva a porta de saída de forma literal, com o que acontece no "não".

## Red Flags — pare e audite

- Vou marcar `[x]` porque o código foi escrito → **falta a evidência**
- Vou mover para `finished/` porque o cabeçalho diz "Concluída" → **conte os `[ ]`**
- Vou propor uma feature que "claramente falta" → **grep primeiro; pode existir**
- Vou citar "concorrentes" sem nomear → **não é análise**
- Vou adiar uma tabela nova para depois → **é capacidade, não configuração**
- A task só descreve o *o quê* na Nota → **falta o porquê**

## Corolários do princípio de produto

1. **Um número errado é pior que nenhum número.** Se não pode ser calculado corretamente ainda, exiba a limitação junto (invariante I7).
2. **A regra da primeira cliente não é a regra do produto.** A resposta dela é *um ponto* no espaço de configurações.
3. **Um sistema que não se mede não pode ser melhorado.** O produto mede o ROI da profissional com rigor — e nada sobre si mesmo.
