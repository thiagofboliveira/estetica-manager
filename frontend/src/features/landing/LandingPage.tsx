import { Link } from "react-router-dom";
import styles from "./LandingPage.module.css";

export function LandingPage() {
  return (
    <div className={styles.landingContainer}>
      {/* Header / Navbar */}
      <header className={styles.navbar}>
        <div className={styles.navBrand}>
          <div className={styles.logoBadge}>✨</div>
          <span className={styles.brandTitle}>
            Lumina <span className={styles.brandSubtitle}>Estética</span>
          </span>
        </div>

        <nav className={styles.navLinks}>
          <a href="#recursos">Recursos</a>
          <a href="#como-funciona">Como Funciona</a>
          <a href="#retencao">Régua de Retorno</a>
          <a href="#depoimentos">Resultados</a>
        </nav>

        <div className={styles.navActions}>
          <Link to="/login" className={styles.btnSecondary}>
            Entrar
          </Link>
          <Link to="/login" className={styles.btnPrimary}>
            Começar Grátis →
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className={styles.heroSection}>
        <div className={styles.heroBadge}>
          <span className={styles.heroBadgeIcon}>🚀</span>
          <span>A plataforma inteligente para clínicas de estética de alta performance</span>
        </div>

        <h1 className={styles.heroTitle}>
          Recupere pacientes esquecidos e blinde seu{" "}
          <span className={styles.gradientText}>Lucro Real</span>
        </h1>

        <p className={styles.heroSubtitle}>
          Chega de perder faturamento com retornos atrasados e planilhas confusas. 
          O sistema com régua ativa no WhatsApp, controle rigoroso de sessões de pacotes 
          e cálculo financeiro de alta precisão.
        </p>

        <div className={styles.heroCtaGroup}>
          <Link to="/login" className={styles.heroBtnMain}>
            Acessar Sistema Agora
          </Link>
          <Link to="/dashboard" className={styles.heroBtnDemo}>
            Ver Demonstração ao Vivo ↗
          </Link>
        </div>

        {/* Live Interactive Preview / Mockup */}
        <div className={styles.previewCardWrapper}>
          <div className={styles.previewCard}>
            <div className={styles.previewHeader}>
              <div className={styles.previewDots}>
                <span className={styles.dotRed} />
                <span className={styles.dotYellow} />
                <span className={styles.dotGreen} />
              </div>
              <div className={styles.previewAddress}>
                app.luminaestetica.com.br/retornos
              </div>
            </div>

            <div className={styles.previewBody}>
              <div className={styles.previewStatsGrid}>
                <div className={styles.previewStatCard}>
                  <span className={styles.statLabel}>Potencial a Recuperar Hoje</span>
                  <span className={styles.statValue}>R$ 14.850,00</span>
                  <span className={styles.statTrend}>↑ +28% vs mês anterior</span>
                </div>
                <div className={styles.previewStatCard}>
                  <span className={styles.statLabel}>Pacientes na Janela Ideal</span>
                  <span className={styles.statValue}>18 pacientes</span>
                  <span className={styles.statBadge}>⏰ Ação Imediata</span>
                </div>
                <div className={styles.previewStatCard}>
                  <span className={styles.statLabel}>Lucro Real Executado</span>
                  <span className={styles.statValue}>R$ 42.190,00</span>
                  <span className={styles.statSub}>100% livre de flutuação</span>
                </div>
              </div>

              {/* Mini Item Demo */}
              <div className={styles.previewDemoCard}>
                <div className={styles.demoAvatar}>CS</div>
                <div className={styles.demoInfo}>
                  <strong>Dra. Camila Silveira</strong>
                  <span>Toxina Botulínica (Venceu há 5 dias) • Tel: (11) 98765-4321</span>
                </div>
                <div className={styles.demoValue}>
                  <span>Potencial</span>
                  <strong>R$ 1.400,00</strong>
                </div>
                <div className={styles.demoAction}>
                  <span className={styles.zapBadge}>💬 Chamar WhatsApp</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Bento Grid */}
      <section id="recursos" className={styles.featuresSection}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionCategory}>Funcionalidades Essenciais</span>
          <h2 className={styles.sectionTitle}>
            Desenvolvido sob medida para a rotina da estética
          </h2>
          <p className={styles.sectionDesc}>
            Eliminamos a complexidade para focar no que realmente move o caixa da sua clínica.
          </p>
        </div>

        <div className={styles.bentoGrid}>
          {/* Card 1 */}
          <div className={`${styles.bentoCard} ${styles.bentoHighlight}`}>
            <div className={styles.cardIcon}>🎯</div>
            <h3>Régua Ativa de Retorno ("Quem chamar hoje?")</h3>
            <p>
              O algoritmo rastreia o tempo de durabilidade de cada procedimento (Botox 4 a 6 meses, 
              Bioestimuladores 1 ano) e avisa exatamente o dia de mandar mensagem personalizada 
              pelo WhatsApp com 1 clique.
            </p>
            <div className={styles.cardFooterTag}>Aumento de até 40% em recompra</div>
          </div>

          {/* Card 2 */}
          <div className={styles.bentoCard}>
            <div className={styles.cardIcon}>💎</div>
            <h3>Lucro Real vs. Lucro Provisório</h3>
            <p>
              Vendeu um pacote de 10 sessões? O sistema reconhece o lucro proporcionalmente à medida 
              que as sessões são executadas, protegendo seu fluxo de caixa contra retiradas ilusórias.
            </p>
            <div className={styles.cardFooterTag}>Conformidade Contábil Invariante I7</div>
          </div>

          {/* Card 3 */}
          <div className={styles.bentoCard}>
            <div className={styles.cardIcon}>🗓️</div>
            <h3>Agenda Fluída com Conversão em Venda</h3>
            <p>
              Agende contatos provisórios e, assim que a paciente sentar na maca, transforme a 
              sessão em venda e baixa de estoque de insumos instantaneamente.
            </p>
            <div className={styles.cardFooterTag}>Sem retrabalho na recepção</div>
          </div>

          {/* Card 4 */}
          <div className={styles.bentoCard}>
            <div className={styles.cardIcon}>🔒</div>
            <h3>Blindagem LGPD & Consentimento</h3>
            <p>
              Controle estrito de consentimento de contato por paciente. Se o paciente não optou por 
              receber avisos no WhatsApp, o sistema protege sua clínica bloqueando envios indevidos.
            </p>
            <div className={styles.cardFooterTag}>Segurança Jurídica Total</div>
          </div>
        </div>
      </section>

      {/* Social Proof / Numbers */}
      <section id="depoimentos" className={styles.statsSection}>
        <div className={styles.statsWrapper}>
          <div className={styles.statBigItem}>
            <h3>+R$ 4.8M</h3>
            <p>Em faturamento reativado de retornos</p>
          </div>
          <div className={styles.statDivider} />
          <div className={styles.statBigItem}>
            <h3>98.5%</h3>
            <p>De precisão em conciliação de sessões</p>
          </div>
          <div className={styles.statDivider} />
          <div className={styles.statBigItem}>
            <h3>1-Click</h3>
            <p>Contato direto via WhatsApp oficial</p>
          </div>
        </div>
      </section>

      {/* Testimonial Quote */}
      <section className={styles.testimonialSection}>
        <div className={styles.testimonialCard}>
          <p className={styles.quoteText}>
            “Antes do Lumina, nossa secretária gastava horas folheando fichas para descobrir quem 
            precisava retocar o Botox. Hoje, a tela 'Quem devo chamar hoje' é a primeira coisa que 
            abrimos de manhã. Recuperamos mais de R$ 12.000 já na primeira quinzena.”
          </p>
          <div className={styles.authorInfo}>
            <div className={styles.authorAvatar}>👩‍⚕️</div>
            <div>
              <strong>Dra. Mariana Vasconcelos</strong>
              <span>Clínica Essence • São Paulo / SP</span>
            </div>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaContent}>
          <h2>Pronto para transformar a retenção da sua clínica?</h2>
          <p>
            Acesse o sistema agora mesmo e veja a lista de oportunidades de retorno 
            já prontas para serem contatadas.
          </p>
          <div className={styles.ctaButtons}>
            <Link to="/login" className={styles.heroBtnMain}>
              Acessar Minha Conta →
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerTop}>
          <div className={styles.navBrand}>
            <div className={styles.logoBadge}>✨</div>
            <span className={styles.brandTitle}>Lumina Estética</span>
          </div>
          <p className={styles.footerTagline}>
            Software de gestão e inteligência de retorno para clínicas estéticas.
          </p>
        </div>
        <div className={styles.footerBottom}>
          <span>© {new Date().getFullYear()} Lumina Estética Manager. Todos os direitos reservados.</span>
          <div className={styles.footerLinks}>
            <Link to="/login">Entrar</Link>
            <Link to="/dashboard">Painel</Link>
            <a href="#recursos">Termos</a>
            <a href="#recursos">Privacidade</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
