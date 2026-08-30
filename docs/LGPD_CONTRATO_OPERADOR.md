# Instrumento Jurídico de Tratamento de Dados (DPA — Data Processing Agreement) e Base Legal LGPD

**Plataforma:** Estética Manager (Micro-SaaS para Gestão Financeira e Retenção em Estética)
**Fundamento:** Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 — LGPD, especialmente Arts. 7º, 11, 16, 18 e 39)

---

## 1. Qualificação dos Papéis no Tratamento de Dados

1. **Controladora dos Dados:** A profissional de estética autônoma ou clínica usuária da plataforma que coleta os dados de seus pacientes/clientes.
2. **Operadora dos Dados:** A plataforma *Estética Manager*, que realiza o tratamento de dados pessoais estritamente sob as instruções e em benefício da Controladora.

---

## 2. Bases Legais Aplicáveis (Arts. 7º e 11)

| Finalidade do Tratamento | Categoria de Titular | Base Legal (LGPD) | Medidas de Conformidade |
|---|---|---|---|
| Autenticação, gestão de assinatura e faturamento da conta | Profissional / Usuária | **Execução de Contrato** (Art. 7º, V) | Tokens JWT, criptografia HTTPS, isolamento por tenant |
| Registro de atendimentos, procedimentos e controle financeiro | Paciente / Cliente | **Execução de Contrato** (Art. 7º, V) e **Legítimo Interesse** (Art. 7º, IX) | Segregação estrita via Row Level Security (RLS) |
| Lembretes de retorno e mensagens de WhatsApp | Paciente / Cliente | **Consentimento** (Art. 7º, I e Art. 11, I) | Campo explícito `consent_whatsapp` + data de consentimento `consent_at` |
| Revogação de contato (Opt-out) | Paciente / Cliente | **Direito do Titular** (Art. 18, IX) | Endpoint `POST /api/v1/patients/{id}/opt-out` com timestamp `opted_out_at` |
| Guarda contábil e fiscal de vendas e notas | Paciente e Profissional | **Obrigação Legal / Fiscal** (Art. 7º, II e Art. 16, I) | Retenção por 5 anos (Código Tributário e Civil) |
| Anonimização / Eliminação a pedido do titular | Paciente / Cliente | **Direito de Eliminação / Anonimização** (Art. 18, VI e Art. 16, II) | Endpoint `POST /api/v1/patients/{id}/anonymize` (mascara PII e mantém registros fiscais agregados) |
| Portabilidade de Dados | Paciente / Cliente | **Direito de Portabilidade** (Art. 18, V) | Endpoint `GET /api/v1/patients/{id}/export` em formato JSON estruturado |

---

## 3. Obrigações e Garantias do Operador (Estética Manager)

1. **Isolamento de Dados (Multi-tenancy):**
   - O banco de dados PostgreSQL opera com políticas de segurança em nível de linha (*Row Level Security — RLS*) ativadas e forçadas (`ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`).
   - A role da aplicação (`estetica_app`) possui privilégio restrito `NOBYPASSRLS`. É tecnicamente impossível que uma profissional acesse pacientes, vendas ou agendas de outro tenant.

2. **Minimização de Dados Sensíveis:**
   - O sistema não coleta dados biométricos, dados de saúde estruturados ou prontuários complexos na versão padrão de gestão financeira. O campo `notes` é reservado para orientações operacionais simples.

3. **Notificação de Incidentes:**
   - O Operador comunicará imediatamente a Controladora e a Autoridade Nacional de Proteção de Dados (ANPD) caso tome conhecimento de qualquer incidente relevante de segurança.

4. **Direitos dos Titulares:**
   - O sistema fornece mecanismos diretos via API e interface para atender tempestivamente a todas as requisições de titulares (confirmação, acesso, correção, anonimização, portabilidade e revogação de consentimento).

---

*Documento revisado para o lançamento e validação do cliente zero (Fase 4).*
