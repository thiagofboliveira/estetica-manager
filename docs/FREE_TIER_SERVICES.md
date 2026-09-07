# Guia Consolidado: Serviços Free-Tier e Limites Gratuitos

Este documento detalha todos os serviços de infraestrutura e plataformas em nuvem utilizados na arquitetura de produção do **Lumina (Estética Manager)** operando em **Free-Tier (Custo Zero / R$ 0,00/mês)**, com seus respectivos limites operacionais, comportamentos de inatividade e estratégias de mitigação.

---

## 📊 Matriz Comparativa Rápida

| Serviço | Função na Aplicação | Limite Principal Gratuito | Comportamento de Inatividade | Ação Recomendada |
| :--- | :--- | :--- | :--- | :--- |
| **Vercel** | Hospedagem Frontend (React + Vite PWA) | 100 GB/mês tráfego, 6.000 min build | Nunca dorme (CDN Global Edge) | CDN em cache, consumo quase nulo |
| **Render** | Hospedagem Backend API (FastAPI) | 750 horas/mês (1 serviço 24/7), 512 MB RAM | Hiberna após **15 min** sem requisições | Configurar monitor UptimeRobot para ping a cada 10-14 min |
| **Supabase** | Banco PostgreSQL 16 + Auth + Storage | 500 MB disco, 50k usuários/mês | Pausa se ficar **7 dias** sem requisições | Backend no Render mantém ativo com conexões regulares |
| **Resend** | E-mails Transacionais (Convites e Reset) | 3.000 e-mails/mês (máx. 100/dia) | Sem hibernação | Adicionar domínio próprio para enviar a qualquer e-mail |
| **GitHub** | Versionamento e Automação CI/CD | Repositórios ilimitados, 2.000 min CI/CD | Sempre ativo | Gatilho automático de deploys e testes |
| **UptimeRobot** | Keep-alive e Alerta de Quedas | 50 monitores gratuitos (checagem a cada 5 min) | Sempre ativo (em execução) | **Ativo a cada 5 min** em `/health`: zera cold start e pausa do banco |

---

## 1. 🌐 Frontend: Vercel (Hobby Plan)

O frontend da aplicação é servido globalmente via rede de borda (Edge Network / CDN) da Vercel.

### Limites Gratuitos Oferecidos:
* **Tráfego de Saída (Bandwidth):** 100 GB por mês.
* **Tempo de Build:** 6.000 minutos de compilação por mês.
* **Deploys Diários:** Até 100 deploys por dia.
* **Domínio Personalizado:** Gratuito (com emissão e renovação automática de certificado SSL HTTPS pela Let's Encrypt).
* **Serverless Functions:** 100 GB-horas / 1.000.000 de invocações (o Lumina é uma SPA estática, portanto consome 0 funções serverless).

### Como afeta o Lumina:
* O pacote de produção gerado pelo Vite (HTML + CSS + JS) é totalmente estático e tem em torno de **350 KB a 1.4 MB comprimido**.
* Com 100 GB de cota mensal, a aplicação suporta confortavelmente mais de **250.000 acessos/páginas por mês** sem qualquer cobrança.

---

## 2. ⚙️ Backend API: Render (Free Web Service)

A API do Lumina roda em Python 3.12 com FastAPI, Uvicorn e SQLAlchemy.

### Limites Gratuitos Oferecidos:
* **Horas de Execução:** 750 horas gratuitas de instâncias por mês.
  > 💡 *Um mês de 31 dias tem 744 horas. Ou seja, 1 único serviço no Render pode ficar ligado 24 horas por dia, 7 dias por semana durante o mês inteiro.*
* **Hardware:** 512 MB de Memória RAM compartilhada e 0.1 vCPU.
* **Tráfego de Saída:** 100 GB por mês.
* **Certificado SSL:** HTTPS automático em `*.onrender.com` ou domínio próprio.
* **Armazenamento:** Sistema de arquivos efêmero (arquivos salvos no disco local são descartados no restart — o que não é problema, pois todos os dados residem no banco de dados Supabase).

### Particularidades e Alertas:
* **Cold Start (Spin-down por inatividade):** Após 15 minutos consecutivos sem receber requisições HTTP, o Render desativa a instância para poupar recursos. Ao chegar uma nova requisição, o Render reativa o container, levando de **30 a 50 segundos** para responder à primeira chamada.
* **Mitigação:** Você pode cadastrar a URL de saúde `https://estetica-manager.onrender.com/health` em um monitor gratuito como o [UptimeRobot](https://uptimerobot.com) ou [cron-job.org](https://cron-job.org), disparando um GET a cada 10 a 14 minutos. Isso mantém o container sempre aquecido em horário comercial.

---

## 3. 🗄️ Banco de Dados & Autenticação: Supabase (Free Tier)

O Supabase fornece o banco de dados PostgreSQL 16 relacional gerenciado e o serviço de autenticação com tokens JWT.

### Limites Gratuitos Oferecidos:
* **Armazenamento de Dados:** 500 MB de armazenamento em disco PostgreSQL dedicado.
* **Conexões Simultâneas:**
  * Modo Direto: ~60 conexões.
  * Modo Connection Pooler (Supavisor): Porta 6543 (Transaction Mode IPv4) suporta centenas de clientes simultâneos.
* **Usuários Ativos (Supabase Auth):** Até 50.000 Usuários Ativos Mensais (MAU).
* **Storage de Arquivos (Fotos/Anexos):** 1 GB de espaço e 2 GB de download/mês.
* **Egress (Transferência de Saída):** 2 GB por mês.

### Particularidades e Alertas:
* **Pausa por Inatividade de 7 Dias:** Se um projeto no plano Free passar 7 dias seguidos sem nenhuma atividade no banco ou no dashboard, o Supabase pausa o projeto automaticamente (exigindo clicar em "Restore" no painel).
  > 💡 *Como a API no Render e você estarão acessando o sistema regularmente, o projeto não atinge os 7 dias de inatividade.*
* **Limite de Disparo de E-mail padrão (Built-in SMTP):** O servidor de e-mail comunitário padrão do Supabase possui uma cota restrita a cerca de **3 a 4 e-mails por hora** (`rate limit exceeded`).
  > 💡 *Por este motivo, para disparar recuperação de senhas e convites em escala, configuramos o Custom SMTP (Resend).*

---

## 4. 📧 Disparador de E-mails: Resend (Free Plan)

O Resend é utilizado como provedor SMTP transacional conectado ao Supabase para envio de links de convite e recuperação de senha.

### Limites Gratuitos Oferecidos:
* **Volume Mensal:** 3.000 e-mails por mês gratuitos.
* **Volume Diário:** Limite de 100 e-mails por dia.
* **Domínios Verificados:** 1 domínio próprio gratuito (com validação DNS via SPF, DKIM e DMARC).
* **Histórico de Logs:** 3 dias de retenção de auditoria de entregas.

### Particularidades e Alertas:
* **Modo de Teste (Sem Domínio Próprio):** Caso ainda não tenha configurado um domínio próprio, o Resend opera em modo Sandbox (`onboarding@resend.dev`), permitindo enviar e-mails de teste exclusivamente para o endereço do titular cadastrado na conta do Resend.
* **Produção:** Ao registrar um domínio (ex: `clinica.com.br` ou `luminaestetica.com.br`), você pode disparar para qualquer destinatário dentro da cota de 100 e-mails/dia.

---

## 5. 🐙 Versionamento e CI/CD: GitHub (Free Plan)

Repositório central do código-fonte e automação de integração contínua.

### Limites Gratuitos Oferecidos:
* **Repositórios:** Ilimitados (públicos e privados).
* **Colaboradores:** Ilimitados em repositórios públicos e privados.
* **GitHub Actions:** 2.000 minutos de execução gratuita por mês para repositórios privados (e ilimitado para públicos).
* **Armazenamento de Pacotes / Releases:** 500 MB.

---

## 6. 🩺 Monitoramento: Sentry (Developer Free Plan - Opcional)

Configurado opcionalmente para rastreamento de erros e exceções não tratadas no frontend e backend.

### Limites Gratuitos Oferecidos:
* **Eventos de Erro:** 5.000 erros registrados por mês.
* **Performance Transactions:** 10.000 transações de monitoramento de performance por mês.
* **Retenção:** 30 dias de histórico de erros.

---

## 7. ⏱️ Monitoramento de Disponibilidade & Keep-Alive: UptimeRobot (Configurado e Ativo)

O UptimeRobot é a peça-chave de confiabilidade operacional da arquitetura gratuita, responsável por manter a API e as conexões de banco permanentemente aquecidas.

### Limites Gratuitos Oferecidos (Free Plan):
* **Quantidade de Monitores:** Até 50 monitores HTTP(s), Ping ou Port.
* **Intervalo Mínimo de Checagem:** A cada **5 minutos** (o plano gratuito não permite checagens menores que 5 min, tornando essa a frequência máxima e ótima).
* **Canais de Alerta:** Notificações instantâneas gratuitas via **E-mail**, **Webhooks** e **Push Notification** no aplicativo mobile do UptimeRobot.
* **Histórico de Logs / Uptime:** Retenção de **2 meses (60 dias)** de métricas e histórico de incidentes.
* **Páginas de Status Públicas:** Até 1 página de status pública gratuita (ex: `status.lumina.com`).
* **Custo:** **R$ 0,00/mês vitalício**.

### Configuração em Produção no Lumina:
* **Monitor:** `Lumina Backend Health`
* **Tipo:** HTTP(s) (Método `GET`)
* **URL:** `https://estetica-manager.onrender.com/health` (ou domínio próprio da API)
* **Frequência Ativa:** **A cada 5 minutos**.

### Impacto e Benefícios Concretos na Arquitetura:
1. **Fim do Cold Start no Render:** Como o limite de inatividade do Render é de 15 minutos, a checagem a cada 5 minutos impede completamente que a instância entre em modo de suspensão (*spin-down*). A Cliente 0 sempre obtém respostas imediatas (latência < 100ms), sem os 40-50 segundos de espera do primeiro acesso.
2. **Prevenção de Pausa no Supabase:** Como o endpoint `/health` realiza um `SELECT 1` leve no PostgreSQL, o banco registra atividade constante, eliminando o risco da regra de pausa do Supabase (que congela projetos após 7 dias de inatividade).
3. **Consumo de Horas no Render:** O Render oferece 750 horas de runtime gratuito por mês. Um mês de 31 dias possui 744 horas. O monitoramento mantém o backend ligado 24/7 consumindo exatamente a cota mensal sem exceder.
4. **Alerta Proativo de Falhas:** Caso o banco fique inacessível ou ocorra erro fatal na API, o `/health` retorna `503 Service Unavailable`, acionando o UptimeRobot para enviar um e-mail de alerta imediatamente ao responsável técnico.

---

## 📈 Resumo de Escala: Quando será necessário migrar para planos pagos?

A arquitetura atual com este stack gratuito suporta com folga:
* **Até 50 a 100 clínicas pequenas cadastradas** (ou centenas de usuários ativos mensais).
* **Mais de 10.000 atendimentos e sessões no banco** (ocupa menos de 50 MB dos 500 MB disponíveis no Supabase).
* **Milhares de visitas diárias no frontend** pela CDN da Vercel.

**Primeiro gargalo provável:**
Quando a operação ultrapassar o limite de 512 MB de RAM do Render (muitos acessos simultâneos) ou quando a hibernação do Render for inaceitável para uma operação comercial 24h sem keep-alive (o upgrade do Render custa US$ 7/mês). Até lá, o custo de infraestrutura é **zero**.
