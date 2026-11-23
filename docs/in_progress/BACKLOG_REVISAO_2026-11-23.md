# Backlog — Revisão de código de 2026-11-23

Origem: revisão de segurança, lógica e UX do repositório inteiro (leitura do código das partes críticas + `ruff`, `pytest`, `tsc`, `oxlint`, `vitest` rodados num Postgres 16 limpo).

**Como ler:** `[x]` só com teste/comando que prova (coluna Evidência). `[ ]` é trabalho aberto. A coluna Nota diz *por que* importa.

## P0 — antes de cobrar o primeiro cliente

| ID | Task | Status | Depende | Evidência / Nota |
|---|---|:--:|---|---|
| `REV-01` | Webhook Asaas fail-closed + comparação em tempo constante | `[x]` | — | `tests/test_review_2026_11_billing_anamnesis.py::TestWebhookFailClosed`. **Sem `ASAAS_WEBHOOK_SECRET` a rota aceitava qualquer um** e um "PAYMENT_CONFIRMED" forjado ativava assinatura de graça. Agora 503. **Ação de deploy: definir o segredo no ambiente e no painel do Asaas.** |
| `REV-02` | Checkout idempotente; não vazar erro do gateway; cupom só consome após o Asaas aceitar | `[x]` | — | `TestCheckoutIdempotente`. Duplo clique criava 2 assinaturas recorrentes (cobrança em duplicidade). Troca de ciclo com assinatura ativa devolve 409 em vez de criar outra. |
| `REV-03` | Ficha de anamnese enviada é imutável (409 no reenvio) | `[x]` | — | `TestAnamneseImutavelAposEnvio`. Quem tinha o link podia sobrescrever respostas, assinatura e a data do aceite do TCLE — enfraquece o valor probatório do termo. |
| `REV-04` | Rate limit por IP real atrás de proxy | `[ ]` | — | O Dockerfile sobe o `uvicorn` sem `--forwarded-allow-ips`; atrás de Railway/Render todo visitante pode parecer o mesmo IP (limite global em vez de por pessoa). **Inferência, não testado em produção.** Configurar `FORWARDED_ALLOW_IPS` com o IP do proxy (não `*`, que permite forjar o cabeçalho). |
| `REV-05` | Teto de tamanho nas rotas públicas | `[~]` | — | Feito: `signature_image` ≤ 400 mil caracteres, ≤ 200 respostas, ≤ 5000 caracteres por resposta (`test_assinatura_gigante_e_rejeitada`). **Falta** limite global de corpo (middleware/proxy) para as demais rotas públicas. |
| `REV-06` | Tirar `management_token` da query string | `[ ]` | — | Token na URL vai para log de acesso, histórico e `Referer`. Mover para header ou corpo; manter link de e-mail/WhatsApp compatível. |
| `REV-07` | `ruff check .` limpo (CI estava vermelho) | `[x]` | — | `ruff check .` → "All checks passed!" (eram 67 erros). Enums `(str, Enum)` mantidos com `noqa` de propósito: `StrEnum` mudaria `str(x)`. |

## P1 — qualidade e confiança

| ID | Task | Status | Depende | Evidência / Nota |
|---|---|:--:|---|---|
| `REV-08` | Tornar a suíte de testes hermética | `[ ]` | — | Num banco novo: 15 falhas; algumas passam isoladas e falham na suíte (`test_billing_api`), outras dependem de qual usuário o banco já tem (`/dev/login` pega o primeiro) ou colidem em `ix_professionals_slug`. `test_backup_restore` assume Postgres na porta 5432. Cada teste deve criar o próprio tenant. |
| `REV-09` | Testes de componente/fluxo no frontend | `[ ]` | — | Hoje são 28 testes, todos de utilitário (money, whatsapp, imagem). Nenhuma tela de venda, agenda ou agendamento público é testada. |
| `REV-10` | Cupom: limite de tentativas em `/billing/coupons/validate` | `[ ]` | — | Autenticado, mas sem rate limit: dá para enumerar códigos. |
| `REV-11` | Webhook Asaas: deduplicar por id de evento e usar o fim do período do Asaas | `[ ]` | REV-01 | `current_period_end = now + 30*meses` é aproximação; reentrega do mesmo evento reestende o período. |
| `REV-12` | `alembic upgrade head` no `CMD` do container | `[ ]` | — | Com mais de uma réplica, duas sobem migração ao mesmo tempo. Mover para etapa de release. |
| `REV-13` | Remover o identificador do projeto Supabase fixo em `core/config.py` | `[ ]` | — | O ref `ckgnn…` e a regra de reescrita de URL estão no código; vira variável de ambiente. |
| `REV-14` | Repositório privado (ou limpar `ENTREVISTA.md` e a apresentação) | `[ ]` | — | O repositório é público e a pasta de docs tem dados financeiros reais da cliente zero. Não encontrei CPF, nome ou chave. |

## P2 — UX/UI

| ID | Task | Status | Depende | Evidência / Nota |
|---|---|:--:|---|---|
| `REV-15` | `PackageSaleForm`: efeitos colaterais saíram de `useMemo` para `useEffect` | `[x]` | — | `npx tsc -b` limpo; os 2 avisos `void-use-memo` do lint sumiram. `setState` dentro de `useMemo` roda no render e pode gerar aviso/loop. |
| `REV-16` | Agendamento público: `label` ligados aos campos, `autoComplete`/`inputMode` no telefone, rodapé com o nome da profissional | `[x]` | — | `tsc` limpo. Leitor de tela e toque no rótulo não funcionavam; o rodapé fixava "Lumina Estética" na página de todas as profissionais. **Não validado visualmente no navegador.** |
| `REV-17` | Trocar os `alert()`/`confirm()` por aviso na tela | `[~]` | — | 1 de 39 feito (importação de pacientes, que dizia "Verifique o console"). Restam 38; usar `toast` e um diálogo de confirmação do próprio produto. |
| `REV-18` | Uniformizar o nome do produto | `[ ]` | — | "Lumina" (cobrança, landing, mensagens) vs "Estética Manager" (repositório). Decidir um. |
| `REV-19` | 17 `div` com `onClick` → `button` | `[ ]` | — | Não recebem foco nem teclado. |
| `REV-20` | Consentimento específico para dado de saúde no campo de observação do agendamento | `[ ]` | — | O placeholder convida a informar alergias; o consentimento atual cobre só lembretes por WhatsApp (LGPD trata saúde como dado sensível). |
