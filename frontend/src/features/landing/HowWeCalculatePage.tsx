import { Link } from "react-router-dom";
import landingStyles from "./LandingPage.module.css";
import styles from "./HowWeCalculatePage.module.css";

const RULES = [
  {
    title: "Só contamos quem estava atrasada",
    body: "Se a paciente ainda estava dentro do prazo esperado de retorno, ela não entra na conta — mesmo que ela tenha voltado. Só contamos quem já tinha passado da data.",
  },
  {
    title: "Precisa ter um contato registrado por você",
    body: "Só contamos quando você mesma registrou que ligou ou mandou mensagem para aquela paciente. Sem esse registro, não entra na conta — mesmo que ela tenha comprado de novo.",
  },
  {
    title: "A compra precisa acontecer em até 21 dias depois do contato",
    body: "Se ela comprou muito tempo depois do seu contato, não contamos como resultado do contato — pode ter sido por outro motivo.",
  },
  {
    title: "Cada compra conta uma vez só",
    body: "Se a paciente tinha mais de um procedimento em atraso, uma única compra não é contada duas vezes.",
  },
  {
    title: "Pacote conta pelo valor total — e isso deixa o número mais instável",
    body: "Se o contato levou a paciente a comprar um pacote de 10 sessões, contamos o valor do pacote inteiro, não de uma sessão. Isso é justo (o contato gerou a venda toda), mas também significa que uma única venda grande pode dominar o número de um mês — por isso sempre mostramos ao lado quantas vendas formam aquele valor.",
  },
];

export function HowWeCalculatePage() {
  return (
    <div className={landingStyles.landingContainer}>
      <header className={landingStyles.navbar}>
        <Link to="/" className={landingStyles.navBrand}>
          <div className={landingStyles.logoBadge}>✨</div>
          <span className={landingStyles.brandTitle}>
            Lumina <span className={landingStyles.brandSubtitle}>Estética</span>
          </span>
        </Link>

        <div className={landingStyles.navActions}>
          <Link to="/login" className={landingStyles.btnSecondary}>
            Entrar
          </Link>
          <Link to="/login" className={landingStyles.btnPrimary}>
            Começar Grátis →
          </Link>
        </div>
      </header>

      <main className={styles.content}>
        <h1 className={styles.title}>Como calculamos a receita de pacientes contatadas</h1>
        <p className={styles.intro}>
          A maioria dos sistemas mostra um número de "receita recuperada" que conta qualquer
          paciente que voltou — inclusive quem voltaria sozinha, sem seu esforço. Isso infla o
          número e não serve pra decisão nenhuma. Aqui a régua é mais dura: só contamos o que
          provavelmente não teria acontecido sem você ter contatado a paciente.
        </p>

        <div className={styles.rules}>
          {RULES.map((rule) => (
            <div key={rule.title} className={styles.rule}>
              <h2 className={styles.ruleTitle}>{rule.title}</h2>
              <p className={styles.ruleBody}>{rule.body}</p>
            </div>
          ))}
        </div>

        <p className={styles.footer}>
          Por isso chamamos de "receita de pacientes contatadas pelo sistema" — não de "receita
          recuperada". É um número menor, mas é um número em que você pode confiar.
        </p>
      </main>
    </div>
  );
}
