import { Link } from "react-router-dom";
import styles from "./LegalPages.module.css";

export function TermsOfServicePage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link to="/login" className={styles.backLink}>
          ← Voltar para o login
        </Link>
        <h1 className={styles.title}>Termos de Uso e Prestação de Serviços SaaS</h1>
        <div className={styles.meta}>
          Versão 2026-09-v1 · Última atualização: Setembro de 2026
        </div>
      </header>

      <div className={styles.content}>
        <div className={styles.callout}>
          <strong>Resumo transparente:</strong> O Estética Manager é um software de gestão financeira
          e retenção de pacientes para profissionais de estética. Não cobramos fidelidade punitiva,
          seus dados pertencem a você e nosso isolamento é absoluto por tecnologia.
        </div>

        <h2>1. Objeto e Definições</h2>
        <p>
          Estes Termos de Uso regulam o acesso e a utilização da plataforma <strong>Estética Manager</strong> ("Software" ou "Plataforma"),
          desenvolvida para profissionais autônomas e clínicas do setor de estética e bem-estar ("Usuária" ou "Contratante").
        </p>
        <p>
          A Plataforma fornece funcionalidades de: (a) registro e precificação de procedimentos; (b) cálculo de margem de contribuição e custo de insumos;
          (c) acompanhamento de fluxo de caixa e vendas; (d) fila operacional de lembrete de retornos baseada no tempo de eficácia do procedimento;
          e (e) ferramentas de confirmação de agendamentos anti-no-show.
        </p>

        <h2>2. Ausência de Interferência em Conduta Médica e Clínica</h2>
        <p>
          O Estética Manager é uma ferramenta <strong>estritamente administrativa, gerencial e financeira</strong>.
          A Plataforma não realiza diagnósticos, não prescreve tratamentos, não analisa dosagens e não substitui
          o julgamento técnico e a responsabilidade civil e ética do profissional de saúde ou estética responsável pelo atendimento.
        </p>

        <h2>3. Propriedade dos Dados e Isolamento Técnico</h2>
        <p>
          A Contratante é a única e exclusiva titular dos dados inseridos no sistema (cadastros de pacientes, histórico de atendimentos e financeiro).
          A Plataforma garante o isolamento lógico rigoroso por tenant por meio de políticas de <em>Row Level Security (RLS)</em> no banco de dados PostgreSQL.
          Em nenhum momento os dados de um cliente ou paciente serão visíveis, cruzados ou compartilhados com terceiros ou outros usuários da plataforma.
        </p>

        <h2>4. Planos, Assinatura e Ausência de Fidelidade</h2>
        <p>
          Acreditamos que o software deve se sustentar pelo valor entregue. Por isso:
        </p>
        <ul>
          <li><strong>Sem multa rescisória:</strong> Você pode cancelar sua assinatura a qualquer momento, mantendo o acesso até o fim do ciclo mensal vigente contratado.</li>
          <li><strong>Exportação garantida:</strong> Você tem o direito irrestrito de exportar a totalidade da sua base de pacientes e histórico antes ou após o encerramento da conta.</li>
        </ul>

        <h2>5. Responsabilidades da Usuária</h2>
        <p>
          A Usuária se compromete a:
        </p>
        <ol>
          <li>Manter a confidencialidade de suas credenciais de acesso e reportar imediatamente qualquer suspeita de acesso indevido.</li>
          <li>Obter o consentimento devido de seus pacientes para o envio de mensagens e contatos de acompanhamento via WhatsApp ou outros canais.</li>
          <li>Não utilizar a plataforma para envio de comunicações em massa que violem as políticas antispam das operadoras ou a legislação brasileira.</li>
        </ol>

        <h2>6. Contato e Suporte</h2>
        <p>
          Para dúvidas, suporte ou esclarecimentos sobre estes Termos de Uso, entre em contato através dos canais oficiais
          indicados na plataforma ou pelo e-mail de suporte.
        </p>
      </div>
    </div>
  );
}
