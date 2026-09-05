import { Link } from "react-router-dom";
import styles from "./LegalPages.module.css";

export function PrivacyPolicyPage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link to="/login" className={styles.backLink}>
          ← Voltar para o login
        </Link>
        <h1 className={styles.title}>Política de Privacidade e Contrato de Operador (DPA / LGPD)</h1>
        <div className={styles.meta}>
          Versão 2026-09-v1 · Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)
        </div>
      </header>

      <div className={styles.content}>
        <div className={styles.callout}>
          <strong>Compromisso Fundamental LGPD:</strong> Você (profissional ou clínica) é a <strong>Controladora</strong> dos dados dos seus pacientes.
          Nós (Estética Manager) atuamos estritamente como <strong>Operadora</strong>, processando os dados única e exclusivamente sob as suas instruções
          e com isolamento criptográfico e lógico forçado no banco de dados.
        </div>

        <h2>1. Qualificação das Partes no Tratamento de Dados</h2>
        <ul>
          <li><strong>Controladora dos Dados:</strong> A profissional de estética autônoma ou clínica que coleta e insere os dados de seus pacientes/clientes na plataforma.</li>
          <li><strong>Operadora dos Dados:</strong> A plataforma <em>Estética Manager</em>, que fornece a infraestrutura e o software para processamento dos dados por conta e ordem da Controladora.</li>
        </ul>

        <h2>2. Quadro de Bases Legais e Finalidades (Arts. 7º e 11 da LGPD)</h2>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Finalidade</th>
                <th>Titular</th>
                <th>Base Legal</th>
                <th>Medidas Técnicas</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Autenticação e faturamento</td>
                <td>Profissional</td>
                <td>Execução de Contrato (Art. 7º, V)</td>
                <td>Tokens JWT com JWKS, criptografia em trânsito (HTTPS/TLS)</td>
              </tr>
              <tr>
                <td>Registro de atendimentos e financeiro</td>
                <td>Paciente</td>
                <td>Execução de Contrato e Legítimo Interesse (Art. 7º, V e IX)</td>
                <td>Isolamento rígido por Row Level Security (RLS) forçado</td>
              </tr>
              <tr>
                <td>Lembretes de retorno via WhatsApp</td>
                <td>Paciente</td>
                <td>Consentimento (Art. 7º, I)</td>
                <td>Flag explícita de consentimento gravada com timestamp</td>
              </tr>
              <tr>
                <td>Revogação de contato (Opt-out)</td>
                <td>Paciente</td>
                <td>Direito do Titular (Art. 18, IX)</td>
                <td>Bloqueio automático na fila de contato com registro de opt-out</td>
              </tr>
              <tr>
                <td>Guarda contábil e fiscal de vendas</td>
                <td>Paciente/Profissional</td>
                <td>Obrigação Legal (Art. 7º, II e Art. 16, I)</td>
                <td>Retenção mínima de 5 anos para fins fiscais e tributários</td>
              </tr>
              <tr>
                <td>Anonimização / Eliminação</td>
                <td>Paciente</td>
                <td>Direito do Titular (Art. 18, VI)</td>
                <td>Anonimização irreversível de PII preservando dados financeiros agregados</td>
              </tr>
              <tr>
                <td>Portabilidade de Dados</td>
                <td>Paciente</td>
                <td>Direito de Portabilidade (Art. 18, V)</td>
                <td>Exportação estruturada de todo o histórico do titular em JSON</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2>3. Garantias Técnicas e de Segurança da Informação</h2>
        <h3>3.1. Isolamento Multi-tenant via Row Level Security (RLS)</h3>
        <p>
          O banco de dados da aplicação opera com políticas ativas e forçadas de segurança em nível de linha (<code>ENABLE ROW LEVEL SECURITY</code> + <code>FORCE ROW LEVEL SECURITY</code>).
          A credencial de conexão da aplicação possui privilégio restrito <code>NOBYPASSRLS</code>. É tecnicamente e fisicamente impossível que um usuário visualize ou acesse registros de outro cliente.
        </p>

        <h3>3.2. Minimização de Dados Sensíveis</h3>
        <p>
          O sistema não coleta nem exige dados biométricos, fotos íntimas, nem prontuários médicos estruturados. O sistema limita-se aos dados necessários para agendamento, comunicação e conciliação financeira.
        </p>

        <h2>4. Gestão de Incidentes e Resposta a Titulares</h2>
        <p>
          A Operadora compromete-se a notificar a Controladora e a Autoridade Nacional de Proteção de Dados (ANPD)
          imediatamente caso seja identificado qualquer incidente relevante de segurança que possa acarretar risco ou dano aos titulares.
        </p>
        <p>
          Disponibilizamos endpoints e controles diretos na tela para que a profissional atenda instantaneamente
          a qualquer requisição de paciente referente a acesso, correção, anonimização, opt-out ou portabilidade.
        </p>
      </div>
    </div>
  );
}
