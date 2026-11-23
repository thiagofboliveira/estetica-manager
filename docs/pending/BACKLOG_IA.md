# Backlog — IA dentro do produto

**Papel:** PO/PM · **Data:** 2026-11-23 · **Auditoria:** código real (grep em `backend/app`)

> **Por quê.** Um chat genérico de IA explica margem, mas não conhece as vendas, os custos e as
> pacientes dela. O ativo do produto é o dado correto e congelado. A IA entra para **economizar
> tempo da profissional**, nunca para calcular dinheiro.
>
> **Regra que vale para todas as tasks:** a IA só **lê** números que a API já calculou (strings,
> I1) e **escreve texto** em cima deles. Nunca soma, rateia nem estima. Número estimado chega
> rotulado e o texto tem de preservar o rótulo (I7). Dado de saúde (anamnese, fotos, observações
> clínicas) nunca vai para o provedor de IA (ver REV-20).

## 0. Decisão de custo

**O custo da IA fica do nosso lado e entra no preço do plano. Não pedimos a chave da profissional (BYOK).**
Por quê: a esteticista autônoma não sabe o que é token, e criar conta num provedor mata a adoção;
guardar chave de terceiros cria risco de segurança e de suporte. Os textos são curtos (centavos por
profissional/mês). A margem é protegida por teto mensal (`AI_MONTHLY_DRAFT_LIMIT`, hoje 100) e por
modelo pequeno (`AI_MODEL`). Hoje existe um único plano (`pro`), então o teto é global; quando houver
mais de um plano, o teto passa a ser por plano. BYOK só se aparecer cliente técnico pedindo.

## 1. Auditoria do que já existe

| Item | Estado | Evidência |
|---|---|---|
| Cliente/SDK de LLM no backend | **Não existe** | `grep` por anthropic/openai sem resultado real |
| Oportunidade de retorno + reengajamento | Existe | `api/v1/retention.py` (`/reengagement`, `PATCH /opportunities/{id}`) |
| Templates de mensagem de campanha | Existe (texto fixo) | `api/v1/campaigns.py` (`/templates`) |
| Resumo semanal com lucro real | Existe (números, sem texto narrado) | `api/v1/weekly_summary.py` |
| Simulador de preço (`POST /simulate/price`) | **Não existe** | `grep simulate` só acha `sale_service`; **não prometer sugestão de preço** |

## 2. Tasks

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `AI-01` | Camada `services/ai_text_service.py` com provedor injetável, timeout, teto de uso por plano e fallback para o texto fixo | `[~]` | — | **Por quê:** sem fallback, a tela quebra quando o provedor cai. Teto por plano evita custo descontrolado. Envia só os campos necessários (nunca CPF nem saúde). **Feito:** `services/ai_text_service.py`, tabela `ai_usage` (migração 0038, RLS), provedor injetável, teto mensal, fallback; `tests/test_ai_draft_message.py` (17 testes, banco real, provedor falso). **Falta:** uma chamada real ao provedor com `ANTHROPIC_API_KEY` (aqui só foi testada com rede simulada). |
| `AI-02` | Mensagem de retorno por paciente: `POST /retention/opportunities/{id}/draft-message` | `[~]` | AI-01 | **Por quê:** é o gargalo do produto (não esquecer de chamar). Entrada: primeiro nome, último procedimento, dias desde o atendimento. A profissional revisa e envia; **nada sai sozinho**. Só para paciente com `consent_whatsapp`. **Feito:** `POST /retention/opportunities/{id}/draft-message` + botão "Sugerir mensagem" com texto editável em `RetentionCard` (4 testes de componente). **Falta:** clicar na tela contra a API real com chave. |
| `AI-03` | Resumo semanal narrado: texto de 4–5 frases sobre o `GET /weekly-summary` | `[ ]` | AI-01 | **Por quê:** é o gancho para abrir o app toda semana. O texto cita só valores do payload e mantém "estimado"/"provisório" quando o campo vier assim (I7). |
| `AI-04` | Alerta de procedimento no prejuízo: regra no backend (margem abaixo de limite) + explicação em texto | `[ ]` | AI-01, V-simulador | **Por quê:** é onde ela perde dinheiro sem ver. A regra de detecção é determinística no backend; a IA só explica com custo, taxa e tempo. **Sem sugestão de preço** enquanto não existir simulador no backend. |
| `AI-05` | Medir uso: quantos rascunhos foram enviados, editados ou descartados | `[ ]` | AI-02 | **Por quê:** sem isso não se sabe se a IA ajuda a reter pacientes. Mede o produto, não só a profissional. |

## 3. Definition of Done

- [ ] Teste prova que o payload enviado ao provedor não contém CPF, anamnese nem fotos
- [ ] Teste com provedor falso: timeout e erro caem no texto fixo, sem 500
- [ ] Teste prova que o texto não é salvo como dado financeiro
- [ ] Teto de uso por plano testado (429 ou fallback)
- [ ] Testado contra Postgres real, com isolamento cross-tenant

## 4. Ordem sugerida

`AI-01` → `AI-02` (a mais visível para a primeira cliente) → `AI-03` → `AI-05` → `AI-04`.

## 5. Fora de escopo (o "não")

- Chat livre com a IA dentro do app.
- A IA decidir preço, taxa ou rateio.
- Envio automático de mensagem sem revisão da profissional.
