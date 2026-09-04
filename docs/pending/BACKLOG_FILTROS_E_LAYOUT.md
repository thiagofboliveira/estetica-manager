# Backlog — Filtros de Pacientes/Procedimentos, Retenção Configurável, Menu Lateral e Dashboard

**Origem:** pedido direto do usuário em 2026-09-03. **Estado:** nenhum item iniciado.

Auditoria de código feita antes de escrever este backlog (não confiar em suposição — ver `.claude/skills/po-escopo`). Resultado: quase todos os itens pedidos são **capacidade nova** (coluna/tabela que não existe hoje), não configuração de UI. Isso muda a estimativa — não é "adicionar um filtro na tela", é "criar o dado que o filtro vai filtrar".

## Decisões (respondidas pelo usuário em 2026-09-03)

| # | Pergunta | Decisão |
|---|---|---|
| 1 (E1) | Reserva provisória conta como "tem agendamento"? Sale sem Session conta como "já tratou"? | **Ok** — segue a recomendação proposta: `Booking PROVISIONAL` futuro OU `Session` agendável futura contam como "tem agendamento"; `Session COMPLETED` **ou** `Sale` (mesmo sem sessão, ex. produto revendido) contam como "já tratou". |
| 2 (E2) | `session_plan` é rótulo informativo simples, ou acopla a pacote? | **Ok** — rótulo informativo no catálogo (`SINGLE`\|`MULTIPLE`), sem acoplar a pacotes. |
| 3 (E3) | Abas dentro de Configurações ou itens de menu de primeiro nível? | **Itens de menu de primeiro nível.** Tirar "Financeiro" e "Despesas Fixas" de dentro de Configurações e colocá-los como itens próprios na navegação principal. |
| 4 (E4) | "Nunca tratados" pertence à tela de retenção ou é lista separada? | **Mesma tela** ("Quem chamar hoje"), como seções à parte que não se misturam com as oportunidades `OPEN` reais. |
| 5 (E5) | Carrossel de métricas + carrossel de gráficos, tabela de ranking fora dos carrosséis | **Concordo.** Segue como desenhado. |

Todas as tasks abaixo estão destravadas. F2-01 (default de `is_invasive`) segue como default técnico seguro (`false`), mas ainda vale confirmar com a cliente zero no cadastro real antes de considerar DONE — não é mais bloqueio de início, é validação de dado durante a implementação.

---

## E1 — Filtros de Pacientes (sexo, tem agendamento, já tratou)

Auditoria: `Patient` não tem campo de sexo/gênero. Não existe query "paciente com booking futuro" nem "paciente com pelo menos uma sessão concluída" — precisam ser construídas.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `F1-01` | Migration: `patients.gender` (`enum` nullable: `FEMALE`\|`MALE`\|`OTHER`\|`UNDISCLOSED`, default `NULL`) | `[x]` | — | Feito: `alembic/versions/0011_patient_gender_procedure_filters.py`, `models/patient.py` (`Gender` StrEnum, `native_enum=False` como padrão do projeto). Aplicado no Postgres real. |
| `F1-02` | `PatientCreate`/`PatientUpdate`/`PatientOut` com `gender` opcional | `[x]` | F1-01 | Feito em `schemas/patient.py`. `update()` já usa `setattr` genérico via `model_dump(exclude_unset=True)`, cobre `gender` sem mudança adicional. |
| `F1-03` | `PatientRepository`: filtro `gender` em `list()`/`count()` (reaproveitar `_filtered()`) | `[x]` | F1-01 | Feito. |
| `F1-04` | `PatientRepository`: subquery "tem agendamento" — join com `Session`/`SaleItem`/`Sale` (Session não tem `patient_id` direto, I5) futura agendável, **OU** `Booking` não convertido (`status=SCHEDULED`) com horário futuro (decidido: os dois tipos contam) | `[x]` | — | Feito: `_upcoming_booking_subquery()`. Nota técnica: `BookingStatus` não tem `PROVISIONAL` — o status "ainda não virou venda" é `SCHEDULED` (default do model); ajustado na implementação. |
| `F1-05` | `PatientRepository`: subquery "já tratou" — `Session COMPLETED` (via join) **ou** `Sale` (mesmo sem sessão, produto revendido) — decidido | `[x]` | — | Feito: `_completed_treatment_subquery()`. |
| `F1-06` | `GET /patients` aceita `gender`, `has_upcoming_booking: bool`, `has_completed_treatment: bool`, aplicados em `list()`/`count()` | `[x]` | F1-04, F1-05 | Feito. 12 testes de integração novos contra Postgres real (`tests/test_patient_procedure_filters.py`) provando cada critério (booking futuro conta, venda sem sessão conta, sessão SCHEDULED não conta como "tem agendamento" implícito, etc). |
| `F1-07` | Frontend: 3 filtros na `PatientsPage` (select de sexo, toggle "tem agendamento", toggle "já tratou") | `[x]` | F1-06 | Feito. Toggles de 3 estados (indefinido/sim/não) com classe `.filters-bar__toggle` nova em `index.css`. Reset de página ao mudar qualquer filtro. Campo `gender` também exposto no `PatientForm` (select). Verificado via Playwright: criar paciente com sexo, filtrar por sexo+busca, toggle "tem agendamento" esconde corretamente paciente sem agendamento. |

---

## E2 — Filtros de Procedimentos (invasivo, sessão única/múltipla)

Auditoria: `Procedure` não tem campo de invasividade. "Sessão única vs múltipla" **não é hoje uma propriedade do Procedure** — é decidido na hora da venda (`SaleItem`/pacote), então "filtrar procedimento por múltiplas sessões" exige uma decisão de modelagem antes de codar.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `F2-01` | Migration: `procedures.is_invasive` (`boolean not null default false`) | `[x]` | — | Feito: mesma migration `0011`. Default `false` mantido (ainda vale confirmar com a cliente zero no cadastro real — não é mais bloqueio técnico, é validação de dado). |
| `F2-02` | `ProcedureCreate`/`Update`/`Out` com `is_invasive` | `[x]` | F2-01 | Feito em `schemas/procedure.py`; `create()`/`update()` em `procedure_service.py` propagam o campo. |
| `F2-03` | Migration: `procedures.session_plan` (`enum`: `SINGLE`\|`MULTIPLE`, default `SINGLE`) | `[x]` | — | Feito: `models/procedure.py` (`SessionPlan` StrEnum), desacoplado de pacotes/`SaleItem` conforme decidido. |
| `F2-04` | `ProcedureRepository`: filtros `is_invasive`/`session_plan` em `list()`/`count()` | `[x]` | F2-01, F2-03 | Feito, mesmo padrão `_filtered()` do `PatientRepository`. |
| `F2-05` | `GET /procedures` aceita `is_invasive: bool`, `session_plan: str` | `[x]` | F2-04 | Feito. 6 testes de integração novos (`TestFiltroInvasivo`, `TestFiltroSessionPlan` em `tests/test_patient_procedure_filters.py`), incluindo defaults quando não informado. |
| `F2-06` | Frontend: filtros na `ProceduresPage` (toggle invasivo, select sessão única/múltipla) + badge no card do procedimento mostrando os dois atributos | `[x]` | F2-05 | Feito. Campos também expostos no `ProcedureForm` (radio + checkbox) — sem isso o usuário nunca conseguiria definir os valores. Verificado via Playwright: criar procedimento invasivo+múltiplas sessões, filtrar pelos dois simultaneamente, badges aparecem no card. |

---

## E3 — Configurações: Financeiro e Despesas Fixas como itens de primeiro nível

**Absorvido pelo E6.** A decisão original (tirar Financeiro/Despesas Fixas de dentro de Configurações e virarem itens de primeiro nível) passou a fazer parte da tarefa maior de migrar o menu para sidebar lateral (`F6-03`) — não faz sentido reorganizar os itens duas vezes (uma na barra horizontal atual, outra na sidebar nova). Ver E6.

---

## E4 — "Quem chamar hoje": incluir pacientes sem tratamento ou parados há X dias

Auditoria: hoje `ReturnOpportunity` só nasce quando uma venda anterior termina todas as sessões (I6, `session_service.py`). Não existe nada disparando por "paciente nunca tratou" ou "paciente parado há X dias" fora desse fluxo — **isso é capacidade nova, paralela ao motor de retenção atual, não um filtro nele.** Decidido: entra na mesma tela "Quem chamar hoje", como seções adicionais separadas das oportunidades de retorno reais (não substituem nem se misturam com o critério de `return_interval_days`).

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `F4-02` | `PatientRepository`/novo repo: `list_never_treated()` — pacientes sem nenhuma `Session COMPLETED` nem `Sale` | `[x]` | reaproveita F1-05 | Feito: reaproveita `_filtered(has_completed_treatment=False)` já existente de E1 — nenhuma SQL nova precisou ser escrita. |
| `F4-03` | `list_inactive_for_days(days: int)` — pacientes com **última** `Session COMPLETED` há mais de N dias e **sem** oportunidade de retorno já aberta (evitar duplicar o que o motor de `return_interval_days` já cobre) | `[x]` | — | Feito: `_last_completed_session_subquery()` (MAX(completed_at) agrupado por paciente via join Session→SaleItem→Sale, I5) + `list_inactive_for_days()`. N é query param (`inactive_days`, default 60), não config salva, como decidido. Exclusão de oportunidade já aberta é feita no `RetentionService.list_reengagement()` (F4-04), não no repo. |
| `F4-04` | `GET /retention` aceita seção adicional (`never_treated` e/ou `inactive_days=N`) sem misturar com as oportunidades `OPEN` existentes — resposta separa os três grupos | `[x]` | F4-02, F4-03 | Feito como **endpoint separado** `GET /retention/reengagement?inactive_days=N&page=P&page_size=S` (decisão: não alterar o contrato de `/retention/opportunities`, que hoje devolve lista crua sem envelope — misturar quebraria o tipo de retorno). Resposta: `{never_treated, never_treated_total_count, inactive, inactive_total_count, inactive_days_threshold, page, page_size}`. `RetentionService.list_reengagement()` exclui pacientes que já têm oportunidade `OPEN/CONTACTED/BOOKED/NO_RESPONSE` ativa, para não duplicar cartão com o motor real (I6). **Paginação adicionada depois** (pedido do usuário: "faltou paginação nela também") — página única compartilhada pelas duas seções (`list_never_treated`/`list_inactive_for_days` ganharam `limit`/`offset` + `count_never_treated`/`count_inactive_for_days`), mesmo padrão de `/patients`/`/procedures`. 9 testes de integração contra Postgres real (`tests/test_retention_reengagement.py`), incluindo paginação. |
| `F4-05` | Frontend: seção nova/toggle em `RetentionPage` para os dois filtros, com input numérico para "X dias sem tratamento" | `[x]` | F4-04 | Feito: `ReengagementSection.tsx`, abaixo da lista de oportunidades reais, com rótulo explícito "Diferente das oportunidades acima" (I7) e input numérico para o limiar de dias. Botão de WhatsApp usa mensagem própria (`MESSAGES.RETENTION.WHATSAPP_REENGAGEMENT`), sem tocar na máquina de estado de `ReturnOpportunity` (esses pacientes não têm oportunidade, não há o que marcar como `CONTACTED`). Paginação (`nav.pagination`, mesmo componente visual de `PatientsPage`) adicionada junto com F4-04. Verificado via `curl` contra a API real rodando localmente (dev server), com dados reais do Postgres — **não foi possível verificar clique na tela via Playwright nesta sessão** (ferramenta de browser indisponível); `tsc -b` e lint limpos. |

---

## E5 — Dashboard: carrossel de métricas e carrossel de gráficos

Auditoria: dashboard hoje é uma coluna vertical fixa (ROICard → DashboardMetrics → ExpensesByCategoryChart → ProcedureChartsSection → ProcedureRankingTable). **Não existe nenhum componente de carrossel no frontend** — precisa ser construído do zero.

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `F5-01` | Componente `Carousel` genérico (CSS scroll-snap + setas, sem lib nova — Recharts já foi a única lib de terceiro adicionada nesta sessão, evitar mais dependência para algo que scroll-snap nativo resolve) | `[x]` | — | Feito: `ui/Carousel.tsx` + `Carousel.module.css`. Setas somem em mobile (<640px) — o swipe nativo já resolve e economiza espaço horizontal. Dots clicáveis pulam direto para o slide. |
| `F5-02` | Extrair cada métrica de `DashboardMetrics` (Faturamento, Lucro real, Lucro real do mês, Ponto de equilíbrio, A receber, Margem média, Ticket médio, Vendas/atendimentos) em um card individual reaproveitável dentro do `Carousel` | `[x]` | F5-01 | Feito: `dashboard/MetricCard.tsx` (cada card é seu próprio `<dl>` de item único, reaproveitando as classes CSS `.dashboard__metric*` já existentes). Toda a lógica condicional original preservada (lucro do mês só em period aplicável, ponto de equilíbrio com mensagem de "cobriu os custos" vs "faltam X"). |
| `F5-03` | Segundo `Carousel` agrupando os gráficos existentes (ExpensesByCategoryChart, os dois de ProcedureChartsSection) como slides | `[x]` | F5-01 | Feito: `ProcedureChartsSection.tsx` dividido em dois componentes de topo exportáveis (`ProfitByServiceChart`, `AppointmentsByServiceChart`) para virarem slides independentes; `ExpensesByCategoryChart` já era standalone. `ProcedureRankingTable` ficou de fora do carrossel, como planejado — segue abaixo dos dois carrosséis. |
| `F5-04` | `DashboardPage`: reorganizar em `<Carousel métricas>` → `<Carousel gráficos>` → `<ProcedureRankingTable>`, preservando `OnboardingChecklist` e seletor de período no topo | `[x]` | F5-02, F5-03 | Feito. Verificado via Playwright: navegação real por seta/dots (conteúdo troca e a lógica condicional do "ponto de equilíbrio" se mantém correta após rolar), viewport 375px (setas escondidas, swipe funcional), dark mode consistente. `tsc -b`/lint limpos, 244 testes de backend inalterados (mudança é só frontend). |

---

## E6 — Menu lateral fixo (sidebar), no lugar da topbar + barra horizontal

**Origem:** referência visual enviada pelo usuário em 2026-09-03 (print do concorrente Belasis) — pediu especificamente o menu lateral daquele print.

Auditoria: hoje a navegação é `frontend/src/app/layout/AppLayout.tsx` — uma topbar fixa (logo, seletor de clínica, botões de ação, avatar/logout) **mais** uma barra horizontal de 6 itens (`NAV_ITEMS`) logo abaixo. Não existe sidebar em lugar nenhum do frontend (`AdminLayout`/`SuperAdminLayout` também usam o mesmo padrão de topo). Migrar para sidebar lateral fixa é uma mudança estrutural do `AppLayout` — afeta o esqueleto de toda página autenticada, não uma tela isolada.

**Decisões já tomadas com o usuário:**
- Sidebar fixa à esquerda, sem colapsar em ícone-only (ainda não pedido).
- **Lista simples de itens, sem seções colapsáveis** por enquanto — o print tem grupos expansíveis (Financeiro, Cadastros, Relatórios…), mas com os ~8 itens que o sistema tem hoje isso seria complexidade sem ganho; revisitar se o menu crescer muito.
- O dashboard (E5, carrossel de métricas + carrossel de gráficos) **não muda** por causa deste épico — a referência visual do print é só para a sidebar, não para o conteúdo do dashboard.
- Absorve a decisão do E3: "Financeiro" e "Despesas Fixas" entram como itens próprios da sidebar, não mais dentro de "Configurações".

| ID | Task | Status | Depende | Nota |
|---|---|:--:|---|---|
| `F6-01` | Protótipo de `Sidebar` (estrutura + CSS): coluna fixa à esquerda, logo/marca no topo, lista de itens com ícone+label, avatar/logout no rodapé — sem lógica de dados ainda | `[x]` | — | Feito: `app/layout/Sidebar.tsx` + `Sidebar.module.css`. Reaproveitou ícones existentes; criou só 4 novos (`IconWallet`, `IconReceipt`, `IconMenu`, `IconX`) por não existir equivalente. Cor/tema seguem os tokens do design system atual — verificado em claro e escuro via Playwright. |
| `F6-02` | `AppLayout.tsx`: substituir `<header className={topHeader}>` + `<nav className={mainNav}>` por `<Sidebar />` + área de conteúdo ao lado; mover para dentro da sidebar (ou manter num header fino no topo) os elementos que hoje ficam na topbar: seletor de clínica, botão "Nova Venda", "Modo Ocupado", ThemeToggle, avatar/logout | `[x]` | F6-01 | Feito: usuário/clínica/logout foram para o rodapé da sidebar; "Nova Venda", "Modo Ocupado", ThemeToggle e atalhos admin/super-admin ficaram num header fino no topo do conteúdo. Testado em Dashboard, Financeiro e Despesas Fixas via Playwright (screenshots), `tsc -b` e lint limpos. Agenda/Pacientes/Procedimentos/Retenção não teve o conteúdo interno alterado, só herdam o novo esqueleto — sem risco adicional. |
| `F6-03` | Menu da sidebar com itens: Dashboard, Quem chamar hoje?, Agenda, Pacientes, Procedimentos, **Financeiro** (novo, ex-aba de Configurações), **Despesas Fixas** (novo, ex-aba de Configurações) | `[x]` | F6-02 | Feito: `SettingsPage.tsx` removido (não sobrava nada nela além das duas abas); criadas `FinancialSettingsPage.tsx` e `fixed-expenses/FixedExpensesPage.tsx`, roteadas em `/financeiro` e `/despesas-fixas`. `OnboardingChecklist` atualizado (linkava para `/configuracoes`). Item "Configurações" **não existe mais** no menu — decisão tomada: nada sobrava para justificar a tela. |
| `F6-04` | Responsivo: em viewport mobile (<900px), sidebar vira drawer retrátil com hambúrguer | `[x]` | F6-02 | Feito: hambúrguer no header abre drawer (`translateX`) com overlay escurecido; botões de ação da topbar colapsam para ícone-only; clicar num item do menu fecha o drawer e navega. Testado em viewport 375×800 via Playwright — sem erros de console, navegação confirmada (`/pacientes` após clique). |
| `F6-05` | Aplicar o mesmo `Sidebar` em `AdminLayout`/`SuperAdminLayout` (hoje usam o mesmo padrão de topo) ou decidir explicitamente que ficam de fora por serem áreas administrativas separadas | `[ ]` | F6-02 | Não feito nesta rodada — mantido como decisão explícita de escopo, não esquecimento: painéis administrativos internos têm audiência diferente (não é a esteticista no celular) e não foram pedidos. Evita o sistema ficar com dois padrões coexistindo sem necessidade, mas segue como item separado do backlog. |

---

## Ordem sugerida

Todas as decisões de produto já vieram — nenhum item está mais bloqueado por pergunta em aberto. Ordem por menor esforço/risco primeiro:

1. **F6-01 → F6-04** (sidebar) — mudança estrutural, quanto antes acontecer menos retrabalho de CSS nas outras telas que forem sendo construídas em paralelo (E1/E2/E4/E5). Absorve a entrega do antigo E3.
2. **F1** e **F2** em paralelo — mesmo padrão técnico já usado na paginação desta sessão (`_filtered()`, `count()`, reset de página ao filtrar).
3. **E5** — maior volume de CSS/refatoração de UI, sem dependência de schema.
4. **E4** por último — depende de F1-05 (`has_completed_treatment`) para o critério "nunca tratado", então naturalmente vem depois de E1.
5. **F6-05** (admin/super-admin) pode esperar — não bloqueia nada do resto e tem audiência diferente.
