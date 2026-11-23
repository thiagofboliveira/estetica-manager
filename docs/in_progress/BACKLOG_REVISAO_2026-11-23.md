# Backlog — Revisão de código de 2026-11-23

Origem: revisão de segurança, lógica e UX do repositório inteiro (leitura do código das partes críticas + `ruff`, `pytest`, `tsc`, `oxlint`, `vitest` rodados num Postgres 16 limpo).

**Como ler:** `[x]` só com teste/comando que prova (coluna Evidência). `[ ]` é trabalho aberto. A coluna Nota diz *por que* importa.

## P0 — antes de cobrar o primeiro cliente

| ID | Task | Status | Depende | Evidência / Nota |
|---|---|:--:|---|---|
| `REV-01` | Webhook Asaas fail-closed + comparação em tempo constante | `[x]` | — | `tests/test_review_2026_11_billing_anamnesis.py::TestWebhookFailClosed`. **Sem `ASAAS_WEBHOOK_SECRET` a rota aceitava qualquer um** e um "PAYMENT_CONFIRMED" forjado ativava assinatura de graça. Agora 503. **Ação de deploy: definir o segredo no ambiente e no painel do Asaas.** |
| `REV-02` | Checkout idempotente; não vazar erro do gateway; cupom só consome após o Asaas aceitar | `[x]` | — | `TestCheckoutIdempotente`. Duplo clique criava 2 assinaturas recorrentes (cobrança em duplicidade). Troca de ciclo com assinatura ativa devolve 409 em vez de criar outra. |
| `REV-03` | Ficha de anamnese enviada é imutável (409 no reenvio) | `[x]` | — | `TestAnamneseImutavelAposEnvio`. Quem tinha o link podia sobrescrever respostas, assinatura e a data do aceite do TCLE — enfraquece o valor probatório do termo. |
| `REV-04` | Rate limit por IP real atrás de proxy | `[~]` | — | Código pronto: `--proxy-headers` no uvicorn (Dockerfile e `railway.json`) e `FORWARDED_ALLOW_IPS` documentado no `.env.example`. **Falta no deploy:** definir `FORWARDED_ALLOW_IPS` com o IP do proxy (não `*`) e conferir em produção que o rate limit passa a ser por visitante. Não dá para provar isso em teste local. |
| `REV-05` | Teto de tamanho nas rotas públicas | `[x]` | — | `tests/test_review_2026_11_billing_anamnesis.py::TestRotasPublicasEndurecidas` — corpo > 2 MiB em `/api/v1/public/*` e no webhook vira 413 (middleware ASGI conta os bytes, inclusive chunked). Somado ao teto de `signature_image`/`answers` do P0. |
| `REV-06` | Tirar `management_token` da query string | `[x]` | — | Backend aceita `X-Booking-Token` (query segue aceita, marcada deprecada, p/ links já enviados); frontend passou a chamar a API com o header. Testes em `TestRotasPublicasEndurecidas`. **Limite:** a URL da página do paciente (`/agendamento/:id?token=…`) ainda leva o token, porque é o link que ele recebe; o que saiu foi o token nos logs da API. |
| `REV-07` | `ruff check .` limpo (CI estava vermelho) | `[x]` | — | `ruff check .` → "All checks passed!" (eram 67 erros). Enums `(str, Enum)` mantidos com `noqa` de propósito: `StrEnum` mudaria `str(x)`. |

## P1 — qualidade e confiança

| ID | Task | Status | Depende | Evidência / Nota |
|---|---|:--:|---|---|
| `REV-08` | Tornar a suíte de testes hermética | `[x]` | — | `tests/conftest.py` cria o tenant admin base; teste de dashboard cria o próprio histórico; teste de backup usa a URL do owner. **Banco novo: 395 passam, 0 falham, duas execuções seguidas** (eram 15 falhas). |
| `REV-09` | Testes de componente/fluxo no frontend | `[~]` | — | 10 testes de componente novos (diálogo de confirmação, acessibilidade de modal, teclado no seletor de template): 28 → 38 no frontend. **Falta** cobrir os fluxos de venda, agenda e agendamento público ponta a ponta. |
| `REV-10` | Cupom: limite de tentativas em `/billing/coupons/validate` | `[x]` | — | `TestCupomRateLimit` — 30 validações/hora por profissional; a 31ª devolve 429. |
| `REV-11` | Webhook Asaas: deduplicar por id de evento e usar o fim do período do Asaas | `[x]` | REV-01 | Migração `0037` (`subscriptions.last_payment_id`) + `TestWebhookDedupe`: CONFIRMED e RECEIVED do mesmo pagamento contam uma vez. **Ainda aproximado:** o fim do período é `agora + 30×meses`, não a data do Asaas. |
| `REV-12` | `alembic upgrade head` no `CMD` do container | `[~]` | — | `CMD` roda a migração só se `RUN_MIGRATIONS=1` (default, p/ hosts sem etapa de release) e `railway.json` passou a usar `preDeployCommand`. **Falta** validar num deploy real que o Railway executa o pre-deploy antes de subir; com mais de uma réplica, defina `RUN_MIGRATIONS=0`. |
| `REV-13` | Remover o identificador do projeto Supabase fixo em `core/config.py` | `[x]` | — | `tests/test_config_supabase_url.py` (5 testes): o ref vem da URL/`SUPABASE_URL`, o host do pooler é configurável (`SUPABASE_POOLER_HOST`) e o identificador antigo não existe mais no código. **Ação sua:** o ref antigo continua no histórico do Git; trate-o como público (e privatize o repositório, REV-14). |
| `REV-14` | Repositório privado (ou limpar `ENTREVISTA.md` e a apresentação) | `[ ]` | — | O repositório é público e a pasta de docs tem dados financeiros reais da cliente zero. Não encontrei CPF, nome ou chave. |

## P2 — UX/UI

| ID | Task | Status | Depende | Evidência / Nota |
|---|---|:--:|---|---|
| `REV-15` | `PackageSaleForm`: efeitos colaterais saíram de `useMemo` para `useEffect` | `[x]` | — | `npx tsc -b` limpo; os 2 avisos `void-use-memo` do lint sumiram. `setState` dentro de `useMemo` roda no render e pode gerar aviso/loop. |
| `REV-16` | Agendamento público: `label` ligados aos campos, `autoComplete`/`inputMode` no telefone, rodapé com o nome da profissional | `[x]` | — | `tsc` limpo. Leitor de tela e toque no rótulo não funcionavam; o rodapé fixava "Lumina Estética" na página de todas as profissionais. **Não validado visualmente no navegador.** |
| `REV-17` | Trocar os `alert()`/`confirm()` por aviso na tela | `[x]` | — | 0 `alert()`/`confirm()` restantes. Novo `confirmDialog()` (alertdialog com foco em Cancelar, Esc, Tab preso, botão ≥ 48 px) e `toast.error()` nos avisos; 6 testes do diálogo. `tsc` limpo. **Não validado clicando no app.** |
| `REV-18` | Uniformizar o nome do produto e registrar o domínio | `[ ]` | — | "Lumina" (cobrança, landing, mensagens) vs "Estética Manager" (repositório). Decidir um, **depois** registrar o `.com.br` no Registro.br (o público é brasileiro; ~R$40/ano, confirmar preço). Candidatos: `usalumina.com.br`, `luminaestetica.com.br`, `esteticamanager.com.br`. Antes de comprar: checar disponibilidade e busca de marca no INPI. Depois de comprar: apontar o DNS (frontend e API), atualizar `CORS`/URLs públicas, link do agendamento e e-mails, e ajustar o webhook no painel do Asaas. Desligar renovação automática do que não for usado. |
| `REV-19` | 17 `div` com `onClick` → `button` | `[x]` | — | Cartão de template virou botão acessível (Enter/Espaço, testado). Os outros 16 `div onClick` eram fundos de modal: agora levam foco ao abrir, `Esc` fecha e o conteúdo tem `role=dialog`/`aria-modal` (`modalA11y`, 3 testes). |
| `REV-20` | Consentimento específico para dado de saúde no campo de observação do agendamento | `[~]` | — | Placeholder não pede mais alergias e a tela avisa para não escrever dados de saúde no campo de observação. **Falta** decisão jurídica sobre um consentimento específico para dado sensível (LGPD) — com advogado/contador, não é código. |
