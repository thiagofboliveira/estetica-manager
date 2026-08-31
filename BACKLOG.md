# Backlog Consolidado da Aplicação

Este documento centraliza as tarefas do Frontend e do Backend para facilitar o acompanhamento do desenvolvimento.

---

## 1. Feature: [SUPER_ADMIN] (Concluída)
*Gestão de usuários por clínica e fluxo de primeiro acesso da aplicação (Tenant Admin).*

### Backend
- [x] `[BACK-01]` **Migração do Modelo User**: Adicionar campos `role` (enum: 'superadmin', 'admin', 'user') e `is_superuser` (booleano) na tabela `users`.
- [x] `[BACK-02]` **API de Setup (Primeiro Acesso)**: Criar rota `GET /api/v1/system/status` para verificar se existe algum usuário no sistema.
- [x] `[BACK-03]` **API de Criação de Root**: Criar rota `POST /api/v1/system/setup` que aceita os dados do admin e só funciona caso a contagem de usuários do sistema seja 0.
- [x] `[BACK-04]` **RBAC Middleware**: Criar decoradores/dependências para rotas protegidas que exigem permissão de `admin` ou `superadmin`.
- [x] `[BACK-05]` **CRUD de Usuários**: Implementar endpoints de gerenciamento de usuários:
  - `GET /api/v1/users`: Listar usuários (Somente admin).
  - `POST /api/v1/users`: Criar um novo usuário (Somente admin).
  - `PUT /api/v1/users/{id}`: Atualizar dados/role de usuário (Somente admin).
  - `DELETE /api/v1/users/{id}`: Inativar usuário (Somente admin, não pode inativar a si mesmo).

### Frontend
- [x] `[FRONT-01]` **Setup Wizard (Primeiro Acesso)**: Criar `SetupWizardPage.tsx` para guiar o usuário na criação da conta administrador quando não houver cadastros na base.
- [x] `[FRONT-02]` **Bloqueio Global (Guard)**: Atualizar `RequireAuth` que verifique o endpoint de status do sistema e redirecione para o `/setup` caso seja o primeiro acesso.
- [x] `[FRONT-03]` **Painel de Super Admin - Layout**: Adicionar link exclusivo "👑 Super Admin" no `AppLayout.tsx` (visível apenas para admins).
- [x] `[FRONT-04]` **Painel de Usuários - Listagem**: Criar `AdminUsersPage.tsx` com uma tabela para listar os usuários ativos na clínica.
- [x] `[FRONT-05]` **Painel de Usuários - Criação/Edição**: Criar um modal/formulário de cadastro de equipe.
- [x] `[FRONT-06]` **Sincronização de Sessão**: Atualizar o `AuthContext` para guardar e disponibilizar o perfil logado para a UI.

---

## 2. Feature: [SUPER_ADMIN_SAAS] (Concluída)
*Evolução para arquitetura Multi-Tenant. Um Super Admin Global (Plataforma) que gerencia múltiplas Clínicas (Tenants).*

### Backend
- [x] `[BACK-06]` **Modelagem da Clínica**: Criar tabela `clinics` e adicionar relacionamento `clinic_id` na tabela de `users`.
- [x] `[BACK-07]` **Isolamento de Tenant (CRUD de Usuários)**: Refatorar `/api/v1/users` para filtrar e criar usuários sempre vinculados ao `clinic_id` do Admin logado.
- [x] `[BACK-08]` **Endpoints de Plataforma (Clínicas)**: Criar `/api/v1/super-admin/clinics` (Listar, Criar e Inativar clínicas).
- [x] `[BACK-09]` **Endpoints de Plataforma (Usuários Globais)**: Criar `/api/v1/super-admin/users` para gerenciar todos os usuários da plataforma, podendo injetar o `clinic_id`.

### Frontend
- [x] `[FRONT-07]` **Layout Global**: Criar `SuperAdminLayout.tsx` para diferenciar visualmente o painel da Plataforma do painel da Clínica.
- [x] `[FRONT-08]` **Gestão de Clínicas (UI)**: Criar `SuperAdminClinicsPage.tsx` contendo tabela e modal de criação de novas clínicas.
- [x] `[FRONT-09]` **Gestão de Usuários Globais (UI)**: Adaptar o modal de criação de usuários para o Global Admin, adicionando um *Dropdown* de seleção de clínica alvo.
- [x] `[FRONT-10]` **Roteamento Inteligente**: Ajustar o `RequireAuth` para que logins de `GLOBAL_SUPERADMIN` sejam redirecionados para `/super-admin/clinicas` ao invés de `/dashboard`.

---

## 3. Sprint 2: Validação de Mercado e Go-to-Market (Concluída)

### Backend (100% Concluído - ver `backend/BACKLOG_SPRINT2.md`)
- [x] `[BACK-S2-01]` a `[BACK-S2-05]`: **EPIC-S2-01 — Widget de ROI (Receita Recuperada pelo Sistema)**.
- [x] `[BACK-S2-06]` a `[BACK-S2-12]`: **EPIC-S2-02 — Anti-No-Show (Lembretes D-1)**.
- [x] `[BACK-S2-13]` a `[BACK-S2-16]`: **EPIC-S2-03 — Importação em Lote de Pacientes (Quick Start)**.
- [x] `[BACK-S2-17]` a `[BACK-S2-20]`: **EPIC-S2-04 — Templates de Procedimentos (Onboarding Acelerado)**.
