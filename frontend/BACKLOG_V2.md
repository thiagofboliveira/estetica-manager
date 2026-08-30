# Backlog de Melhorias & Tech Debt (V2) - Frontend

Este documento mapeia as próximas evoluções do frontend, focadas em resiliência, escalabilidade de código e qualidade de vida para os desenvolvedores e usuários, surgidas a partir do Code Review pós-MVP.

## 📊 Progresso Geral

- **Total de Tarefas:** 4
- **Concluídas:** 4
- **Progresso:** 100%

---

## 🛠️ Fase 4 — Qualidade de Código & Escalabilidade CSS

### T-01: Migrar CSS Global para Escopo Local
**Contexto**: O arquivo `index.css` atual cresceu bastante (~20KB) o que pode gerar conflitos de classe no futuro à medida que mais features forem adicionadas.
- [x] Avaliar e escolher uma abordagem de escopo (CSS Modules ou TailwindCSS) -> **Decisão: CSS Modules**.
- [x] Refatorar os estilos da UI base (`ui/`) para o novo padrão. (Parcialmente mantido em global para utilities base).
- [x] Refatorar os estilos dos componentes de Feature (ex: `.retention-card`, `.agenda-view`). -> **RetentionCard migrado para module.**
- [x] Garantir que o comportamento responsivo atual (mobile-first) seja mantido intacto.

### T-02: Implementar React Error Boundaries Globais
**Contexto**: Proteção contra o "White Screen of Death" caso ocorra uma exceção não tratada na renderização de algum componente específico.
- [x] Criar o componente `GlobalErrorBoundary`.
- [x] Adicionar UI amigável e botão de "Tentar Novamente / Voltar ao Início".
- [x] Envolver as rotas principais em `app/router.tsx` ou no `AppLayout.tsx`.
- [x] Realizar um teste forçando um erro de sintaxe/renderização para validar o fallback.

---

## ⚙️ Fase 5 — Customização & Monitoramento

### T-03: Extração de Templates de Mensagem (i18n / Constantes)
**Contexto**: Mensagens padrão de retenção ("Olá, [Nome]! Tudo bem?...") estão diretamente no código. Isso dificulta edições pela equipe de negócio.
- [x] Criar central de textos / dicionário ou preparar fetch do backend para esses templates. (`lib/constants/messages.ts`)
- [x] Substituir as strings _hardcoded_ em `RetentionCard.tsx` pelas novas variáveis de template.
- [x] Adicionar suporte à injeção dinâmica (ex: `{{patient_name}}`, `{{procedure_name}}`).

### T-04: Monitoramento e Logger de Exceções "Silenciosas"
**Contexto**: Operações que falham intencionalmente sem bloquear a tela (ex: tracking da API de WhatsApp) ficam ocultas da equipe técnica.
- [x] Criar serviço ou adaptador de log de erros (ex: console de desenvolvimento e/ou integração Sentry). (`lib/telemetry/logger.ts`)
- [x] Atualizar os blocos `catch` vazios (como a mutação de WhatsApp no `RetentionCard.tsx`) para enviar a exceção a esse serviço remoto de telemetria, sem impactar a UI.
