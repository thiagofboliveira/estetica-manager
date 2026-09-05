# 📋 Relatório Consolidado de QA — Estética Manager (Sprint 1, 2 & 3)

Este documento consolida a auditoria completa de QA sobre todas as funcionalidades e correções entregues nas **Sprints 1, 2 e 3**, cobrindo arquitetura, regras de negócio, testes automatizados e integração de **Backend** e **Frontend**.

Os relatórios detalhados específicos de cada camada estão disponíveis em:
- 🔗 [`backend/bugs.md`](file:///d:/Thiago/Projetos/Estetica/backend/bugs.md)
- 🔗 [`frontend/bugs.md`](file:///d:/Thiago/Projetos/Estetica/frontend/bugs.md)

---

## 🎯 Avaliação Consolidada das Sprints

| EPIC / Funcionalidade | Backend | Frontend | Status QA |
| :--- | :---: | :---: | :---: |
| **EPIC-S3-01: Split por Procedimento (E6)** | 🟢 100% Coberto (4 testes) | 🟢 Compatível | ✅ **Aprovado com Excelência** |
| **EPIC-S3-02: Exportação CSV (LGPD/Relatórios)** | 🟢 100% Coberto (BOM + ;) | 🟢 Download direto | ✅ **Aprovado com Excelência** |
| **EPIC-S3-03: Projeção de Recebíveis (Fluxo)** | 🟢 100% Coberto (Maior Resto) | 🟢 API pronta | ✅ **Aprovado (Obs: is_anticipated)** |
| **EPIC-S3-04: Antecipação de Recebíveis (E7)** | 🟢 100% Coberto (D+2) | 🟢 Configs prontas | ✅ **Aprovado com Excelência** |
| **EPIC-S2-01: Widget de ROI (Receita Recuperada)**| 🟢 100% Coberto | 🟢 `<ROICard />` | ✅ **Aprovado** |
| **EPIC-S2-02: Anti-No-Show (Lembretes D-1)** | 🟡 1 bug (Booking info) | 🟡 1 bug (Fuso UTC) | ⚠️ **Ajuste de Regra/Fuso** |
| **EPIC-S2-03: Importação em Lote de Pacientes** | 🟢 100% Coberto (Atômico) | 🟡 1 melhoria (CSV `;`) | ✅ **Aprovado com Ressalva** |
| **EPIC-S2-04: Templates de Procedimentos** | 🟢 100% Coberto (Catálogo) | 🟢 Selector Pronto | ✅ **Aprovado** |
| **EPIC-S2-05: PWA & Build de Produção** | — | 🔴 Workbox Node 18 | 🔴 **Bloqueante de Build** |
| **Multi-Tenant & Admin (Rotas HTTP)** | 🟢 166 testes passando | 🔴 Prefixo `/api/v1` Duplo | 🔴 **Bloqueante (404)** |

---

## 🚨 Principais Pontos de Ação (Priorizados)

> ✅ **2026-09-02 — Os quatro itens abaixo foram verificados e estão corrigidos no código atual.** Este relatório ficou desatualizado em relação ao estado real do repositório; mantido como histórico.

### 1. [BUG-FRONT-S3-01] Falha no Build do Service Worker PWA no Node.js 18 — ✅ Corrigido
* **Arquivo:** `frontend/vite.config.ts`
* **Erro:** `Error: Unable to write the service worker file. 'crypto is not defined'` ao rodar `vite build`.
* **Verificado:** `vite.config.ts` já tem o polyfill (`globalThis.crypto = nodeCrypto.webcrypto`) e o polyfill de `diagnostics_channel.tracingChannel`. `npm run build` roda limpo, PWA gera `sw.js` normalmente.

### 2. [BUG-FRONT-S2-03] Prefixo Duplicado `/api/v1` nas Telas Administrativas — ✅ Corrigido
* **Arquivos:** `SuperAdminUsersPage.tsx`, `SuperAdminClinicsPage.tsx`, `AdminUsersPage.tsx`, `RequireAuth.tsx`, `SetupWizardPage.tsx`, `AuthContext.tsx`.
* **Verificado:** nenhuma chamada com prefixo duplicado encontrada; `client.ts` centraliza `BASE = VITE_API_URL` e os call sites usam paths relativos sem repetir `/api/v1`.

### 3. [BUG-FRONT-S2-02] Filtro de Fuso Horário no `<NoShowAlert />` — ✅ Corrigido
* **Arquivo:** `frontend/src/features/agenda/NoShowAlert.tsx`
* **Verificado:** o componente já consome `useUnconfirmedSessions()` diretamente, sem refiltragem client-side por data UTC.

### 4. [OBS-BACK-S3-01] Flag `is_anticipated` na Projeção de Recebíveis — ✅ Corrigido em 2026-09-02
* **Arquivo:** `backend/app/services/dashboard_service.py`
* **Causa:** `is_anticipated` estava estático em `False` em `get_receivables_projection`, ignorando `financial_settings.anticipates_all` — vendas antecipadas eram projetadas em D+30/60/90 em vez de D+2.
* **Correção aplicada:** em vez de ler a config *atual* (o que violaria a invariante I3 de snapshot congelado — ver `ENGENHARIA.md`), o valor de `anticipates_all` vigente no momento da venda passou a ser gravado em `Sale.snapshot_payload` (`sale_service.py::_snapshot_payload`) e é esse valor congelado que `DashboardService` lê agora.
* **Teste:** `backend/tests/test_dashboard_integration.py::TestReceivablesRespeitaAntecipacaoCongelada` — cria uma venda a crédito parcelada com `anticipates_all=True`, desliga a configuração de volta, e prova que a projeção ainda cai em D+2 no mês da venda (não D+30/60/90), confirmando que o dado vem do congelado e não da config atual.

---

## 📊 Estatísticas da Suíte de Testes
* **Backend (Pytest):** **166 testes passando com sucesso** (0 falhas, 21 testes de integração real Postgres pulados quando sem banco local ativo).
* **Frontend (TypeScript):** **100% aprovado pelo `tsc -b`** (zero erros de tipagem/módulos).