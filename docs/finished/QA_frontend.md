# 🐛 Relatório de QA & Auditoria de Bugs — Frontend (Sprint 1, 2 & 3)

**Data da Auditoria:** 31/08/2026  
**Perfil do Auditor:** QA Lead & Frontend Engineer  
**Escopo:** Aplicação React 19 + TypeScript + Vite, PWA, Roteamento, Formulários, Máscaras e Integração com API.

---

## Sumário Executivo — Status Geral das Sprints

| EPIC / Módulo | Severidade Alta | Severidade Média | Severidade Baixa / UX | Status de QA |
| :--- | :---: | :---: | :---: | :---: |
| **PWA & Build de Produção (`vite build`)** | 1 | 0 | 0 | 🔴 Bloqueante no Node 18 |
| **EPIC-S2-01: Widget de ROI (`<ROICard />`)** | 0 | 0 | 0 | ✅ Aprovado |
| **EPIC-S2-02: Anti-No-Show (`<NoShowAlert />`)** | 1 | 0 | 0 | ⚠️ Fuso Horário UTC |
| **EPIC-S2-03: Importação em Lote de Pacientes** | 0 | 1 | 0 | ✅ Aprovado com Ressalva |
| **EPIC-S2-04: Templates de Procedimentos** | 0 | 0 | 0 | ✅ Aprovado (TS Types OK) |
| **Multi-Tenant / Admin / Client HTTP** | 1 | 0 | 0 | 🔴 Prefixo `/api/v1` Duplo |

---

## 1. Novos Achados & Status de Build

### 🔴 [BUG-FRONT-S3-01] Falha no Build do Service Worker PWA no Node.js 18 (`crypto is not defined`)
* **EPIC:** `EPIC-S2-05` (PWA Mínimo)
* **Severidade:** Crítica / Bloqueante
* **Arquivo:** `frontend/vite.config.ts` (integração com `vite-plugin-pwa` e `workbox-build`)
* **Descrição:** A compilação TypeScript (`tsc -b`) passou com 100% de sucesso. Porém, na etapa de empacotamento do Vite (`vite build`), a biblioteca `workbox-build` falha ao tentar gerar o arquivo do Service Worker com o seguinte erro:
  ```
  error during build:
  Error: Unable to write the service worker file. 'crypto is not defined'
      at writeSWUsingDefaultTemplate (node_modules/workbox-build/build/lib/write-sw-using-default-template.js:68:15)
  ```
* **Causa:** No Node.js v18 (utilizado no ambiente), `globalThis.crypto` não é exposto globalmente por padrão em todos os contextos de módulo CommonJS/ESM do Workbox.
* **Impacto:** O comando `npm run build` falha e impede a geração dos arquivos de produção na pasta `dist/`.
* **Correção Recomendada:**
  Adicionar a definição de `globalThis.crypto` no topo do arquivo `frontend/vite.config.ts`:
  ```typescript
  import crypto from 'node:crypto'
  if (!globalThis.crypto) {
    // @ts-ignore
    globalThis.crypto = crypto.webcrypto
  }
  ```

---

### 🔴 [BUG-FRONT-S2-03] Duplicação de Prefixo `/api/v1` nas Telas Administrativas (Erro 404)
* **Severidade:** Alta / Bloqueante
* **Arquivos:**
  - `frontend/src/features/admin/SuperAdminUsersPage.tsx`
  - `frontend/src/features/admin/SuperAdminClinicsPage.tsx`
  - `frontend/src/features/admin/AdminUsersPage.tsx`
  - `frontend/src/features/admin/SetupWizardPage.tsx`
  - `frontend/src/app/layout/RequireAuth.tsx`
  - `frontend/src/lib/auth/AuthContext.tsx`
* **Descrição:** O cliente HTTP `client.ts` utiliza `BASE = import.meta.env.VITE_API_URL`, que já é configurado como `http://localhost:8000/api/v1`. Os arquivos listados chamam métodos com `/api/v1/...` (ex: `api.get("/api/v1/super-admin/users")`).
* **Impacto:** A URL final requisitada se torna `http://localhost:8000/api/v1/api/v1/super-admin/users`, resultando em erro HTTP 404 Not Found em todas as operações dessas telas.
* **Correção Recomendada:**
  Padronizar as chamadas para remover o `/api/v1` inicial (ex: `api.get("/super-admin/users")`, `api.get("/users")`, `api.get("/system/status")`).

---

### 🔴 [BUG-FRONT-S2-02] Filtro Incorreto de Fuso Horário em `<NoShowAlert />`
* **EPIC:** `EPIC-S2-02` (Anti-No-Show)
* **Severidade:** Alta
* **Arquivo:** `frontend/src/features/agenda/NoShowAlert.tsx` (linhas 13-17)
* **Descrição:** O componente refiltra as sessões recebidas do backend utilizando `const tomorrowIso = tomorrow.toISOString().split("T")[0]` e comparando com `s.scheduled_at.startsWith(tomorrowIso)`.
* **Impacto:** O backend (`GET /sessions/unconfirmed`) já entrega apenas as sessões do dia seguinte no fuso da profissional. Comparar com data UTC faz com que sessões noturnas no Brasil (UTC-3) sumam do card de lembretes.
* **Correção Recomendada:**
  Consumir diretamente a lista da API sem refiltragem por ISO UTC.

---

### 🟡 [BUG-FRONT-S2-05] Parser de Importação em Lote não Suporta Ponto e Vírgula (`;`)
* **EPIC:** `EPIC-S2-03` (Importação em Lote)
* **Severidade:** Média / UX
* **Arquivo:** `frontend/src/features/patients/PatientImportPage.tsx` (linha 27)
* **Descrição:** A divisão de colunas utiliza `line.split(/[\t,]/)`. No Brasil, arquivos CSV gerados pelo Microsoft Excel utilizam ponto e vírgula (`;`) como separador padrão.
* **Impacto:** Ao colar dados de CSV brasileiro aberto em texto, nome e telefone não são separados corretamente.
* **Correção Recomendada:**
  Alterar para `line.split(/[\t,;]/)`.