# Backlog — Fichas de Anamnese Digital e Visão do Dono da Clínica

**Data:** 2026-09-07  
**Origem:** Alinhamento de produto e arquitetura para a plataforma Lumina  
**Prioridade:**  
1. **Fase 1 (Alta Prioridade):** Sistema de Anamnese Digital Estruturada (Configuração pelo profissional, preenchimento pelo paciente, alertas de saúde no prontuário e automação pós-agendamento).  
2. **Fase 2 (Segunda Prioridade):** Visão Agregada do Dono da Clínica (Métricas macro e consolidadas para `role: admin`, sem adicionar restrições ao usuário padrão/solo).

---

## Diretrizes e Invariantes do Projeto

1. **Zero atrito para Usuário Padrão:** Nenhuma tela existente (Dashboard, Financeiro, Despesas Fixas, Relatórios, etc.) será restrita para o usuário padrão (`role: user` / profissional solo).
2. **Tabelas Estruturadas para Anamnese:** Nada de JSON solto sem schema. Perguntas e templates são entidades estruturadas em banco com tipagem forte (`yes_no`, `text`, `long_text`, `select`), permitindo consultas analíticas, desativação segura e alertas de risco indexados.
3. **Isolamento de Tenant (I1/I2/S-02a):** Todas as tabelas de anamnese respeitam `professional_id` via Postgres RLS e transações gerenciadas por tenant session.
4. **4 Gates de CI Invioláveis:**
   * Backend: `pytest` com 100% de cobertura nos novos fluxos e `ruff check .` sem erros.
   * Frontend: `npx tsc -b` limpo e `vitest run` passando.

---

## Fase 1 — Sistema de Anamnese Digital Estruturada (Prioridade 1)

### Épico A1: Modelagem e Banco de Dados (Backend)

| ID | Status | Task | Depende | Descrição / Critérios de Aceite |
|---|:--:|---|:--:|---|
| `AN-01` | ✅ Concluído | Migration Alembic `0024_anamnesis_system.py` | — | Criar tabelas `anamnesis_templates`, `anamnesis_questions` e `anamnesis_submissions`. Configurar Foreign Keys, índices e RLS (`app.professional_id`). Incluir seed do template padrão de estética facial e corporal com as 7 perguntas essenciais. |
| `AN-02` | ✅ Concluído | Models SQLAlchemy (`app/models/anamnesis.py`) | `AN-01` | Mapear `AnamnesisTemplate`, `AnamnesisQuestion` e `AnamnesisSubmission` estendendo `TenantModel`. Enums para `QuestionFieldType` (`yes_no`, `text`, `long_text`, `select`). |
| `AN-03` | ✅ Concluído | Schemas Pydantic (`app/schemas/anamnesis.py`) | `AN-02` | Schemas de entrada e saída para Templates, Perguntas (com validação de `options` e `risk_trigger_value`), Submissões públicas e Resumo de Alertas de Risco. |

### Épico A2: Serviços e Endpoints da API (Backend)

| ID | Status | Task | Depende | Descrição / Critérios de Aceite |
|---|:--:|---|:--:|---|
| `AN-04` | ✅ Concluído | `AnamnesisRepository` e `AnamnesisService` | `AN-02` | Métodos para: buscar/atualizar template ativo; adicionar/editar/desativar perguntas; reordenar perguntas (`order_index`); submeter respostas calculando automaticamente `has_risk_alerts` e `risk_alerts_summary`; buscar histórico por paciente/booking. |
| `AN-05` | ✅ Concluído | Endpoints Autenticados (`/api/v1/anamnesis`) | `AN-04` | CRUD do template e perguntas: `GET /anamnesis/template`, `PUT /anamnesis/template`, `POST /anamnesis/questions`, `PUT /anamnesis/questions/{id}`, `DELETE /anamnesis/questions/{id}`, `POST /anamnesis/questions/reorder`, `GET /anamnesis/submissions`. |
| `AN-06` | ✅ Concluído | Endpoint Público de Resposta (`/api/v1/public/anamnesis`) | `AN-04` | `GET /public/anamnesis/{token}` (retorna perguntas ativas e dados do agendamento sem exigir autenticação) e `POST /public/anamnesis/{token}` (recebe respostas, valida obrigatoriedade e gera o registro no prontuário). |
| `AN-07` | ✅ Concluído | Testes Automatizados de Integração Backend | `AN-05`, `AN-06` | Testes com `pytest` cobrindo criação de perguntas, submissão pública, detecção de gatilhos de alerta de risco e isolamento RLS entre profissionais. |

### Épico A3: Construtor de Anamnese no Painel (Frontend)

| ID | Status | Task | Depende | Descrição / Critérios de Aceite |
|---|:--:|---|:--:|---|
| `AN-08` | ✅ Concluído | Novo Item no Menu Lateral e Rota `/anamnese` | — | Adicionar `IconClipboardList` no `Sidebar.tsx` e registrar a rota `/anamnese` no `router.tsx` dentro do `AppLayout`. |
| `AN-09` | ✅ Concluído | API Client e React Query Hooks (`features/anamnesis`) | `AN-05` | Hooks `useAnamnesisTemplate`, `useUpdateTemplate`, `useCreateQuestion`, `useUpdateQuestion`, `useDeleteQuestion`, `useReorderQuestions`. |
| `AN-10` | ✅ Concluído | Construtor de Ficha (`AnamnesisPage.tsx`) | `AN-08`, `AN-09` | Lista visual das perguntas do formulário; botões para subir/descer ordem; switch de obrigatória; toggle de alerta de risco; botão de exclusão com confirmação; botão `+ Adicionar Pergunta` com modal intuitivo. |
| `AN-11` | ✅ Concluído | Barra de Ações Rápidas da Anamnese | `AN-10` | Botão "Copiar Link da Ficha" (gera link público direto), botão "Pré-visualizar no Celular" (modal/drawer simulando o smartphone da cliente) e switch "Solicitar automaticamente após agendamento online". |

### Épico A4: Experiência do Paciente & Prontuário Clínico (Frontend)

| ID | Status | Task | Depende | Descrição / Critérios de Aceite |
|---|:--:|---|:--:|---|
| `AN-12` | ✅ Concluído | Tela Pública de Preenchimento Mobile (`/anamnese/:token`) | `AN-06` | Interface leve, responsiva, amigável no celular. Preenchimento guiado com barra de progresso, botões táteis grandes, validação de campos obrigatórios e confirmação final com aceite de veracidade. |
| `AN-13` | ✅ Concluído | Automação no Agendamento Online (`/agendamento/:id`) | `AN-12` | Na tela de confirmação de agendamento público, exibir card de destaque convidando a paciente a preencher a anamnese em 2 minutos. Atualizar o texto de compartilhamento via WhatsApp para incluir o link direto da ficha. |
| `AN-14` | ✅ Concluído | Card de Alertas Clínicos no Prontuário (`PatientDetailPage.tsx`) | `AN-05` | Exibir no topo do perfil da paciente badges de destaque para contraindicações identificadas (ex: `⚠️ Gestante`, `⚠️ Alergia a Frutos do Mar`, `⚠️ Usa Roacutan`). |
| `AN-15` | ✅ Concluído | Aba "Anamnese" no Prontuário do Paciente | `AN-14` | Histórico cronológico das fichas respondidas pelo paciente com visualização completa de perguntas, respostas e data/hora do preenchimento. |

---

## Fase 2 — Visão do Dono da Clínica (Gestão Agregada) (Prioridade 2)

*Nota: Todas as funcionalidades desta fase operam de forma aditiva. O usuário padrão (`role: user` / solo) mantém seu fluxo 100% livre e direto sem restrições.*

### Épico C1: Agregação por Clínica no Backend

| ID | Status | Task | Depende | Descrição / Critérios de Aceite |
|---|:--:|---|:--:|---|
| `GC-01` | ⏳ Pendente | Suporte a `scope=clinic` nos Serviços de Relatórios | — | Estender `DashboardService`, `ProcedureRankingService` e relatórios de agendamento para aceitar agregação por `clinic_id` quando o usuário solicitante possuir `role: admin`. |
| `GC-02` | ⏳ Pendente | Endpoints de Relatórios com Filtro Opcional de Profissional | `GC-01` | Permitir que o admin consulte o consolidado da clínica inteira ou filtre por um `professional_id` específico vinculado àquela clínica. Se for usuário padrão ou solo, o filtro padrão da própria conta permanece inalterado. |
| `GC-03` | ⏳ Pendente | Testes de Integração de Métricas Agregadas | `GC-02` | Testar no `pytest` que: (a) o dono visualiza o somatório de todos os profissionais da clínica; (b) um profissional isolado não enxerga dados de outro profissional; (c) usuário padrão continua operando normalmente. |

### Épico C2: Interface de Relatórios Consolidados (Frontend)

| ID | Status | Task | Depende | Descrição / Critérios de Aceite |
|---|:--:|---|:--:|---|
| `GC-04` | ⏳ Pendente | Seletor de Escopo nos Relatórios (Apenas para `admin` com equipe) | `GC-02` | Na página `/relatorios`, caso a clínica tenha múltiplos profissionais e o usuário seja `admin`, exibir seletor discreto: "Toda a Clínica (Consolidado)" ou nome de uma profissional específica. Oculto para usuários comuns/solo. |
| `GC-05` | ⏳ Pendente | Cards Consolidados no Dashboard do Dono | `GC-04` | Exibição clara de faturamento bruto total da clínica, total de atendimentos da equipe, despesas fixas corporativas e margem líquida real consolidada. |

---

## Definição de Pronto (Definition of Done)

- [x] Todas as migrations executadas e testadas contra PostgreSQL real (`0024_anamnesis_system.py`).
- [x] Formulário padrão de anamnese pré-carregado e funcional desde o primeiro login.
- [x] Link público de anamnese responsivo e testado em telas mobile.
- [x] Alertas de saúde renderizados em destaque no prontuário do paciente.
- [x] Testes de backend passando (`pytest -v` 317 passed).
- [x] Linter sem erros (`ruff check .` clean).
- [x] Build e testes de frontend íntegros (`npx tsc -b`, `vitest run`, `vite build`).
- [x] Nenhuma quebra ou bloqueio introduzido para o usuário padrão.
