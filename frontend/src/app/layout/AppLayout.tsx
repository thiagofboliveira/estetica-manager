import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import styles from "./AppLayout.module.css";

/**
 * Ordem do menu é deliberada (MVP v6 §16.5): Dashboard e Retornos antes
 * de Agenda. Agenda é suporte ao fluxo financeiro/retenção, nunca a
 * manchete — se o produto virar "sistema de agendamento", perde o que
 * o diferencia.
 */
const NAV_ITEMS: { to: string; label: string; icon: string; end: boolean }[] = [
  { to: "/dashboard", label: "Dashboard", icon: "📊", end: true },
  { to: "/retornos", label: "Quem chamar hoje?", icon: "🎯", end: false },
  { to: "/agenda", label: "Agenda", icon: "📅", end: false },
  { to: "/pacientes", label: "Pacientes", icon: "👥", end: false },
  { to: "/procedimentos", label: "Procedimentos", icon: "💉", end: false },
  { to: "/configuracoes", label: "Configurações", icon: "⚙️", end: false },
];

export function AppLayout() {
  const navigate = useNavigate();

  function handleLogout() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("returnTo");
    navigate("/");
  }

  return (
    <div className={styles.appLayout}>
      {/* Top Navbar */}
      <header className={styles.topHeader}>
        <div className={styles.headerLeft}>
          <Link to="/dashboard" className={styles.brandLogo}>
            <div className={styles.logoBadge}>✨</div>
            <div className={styles.brandText}>
              <span className={styles.brandName}>Lumina</span>
              <span className={styles.brandSub}>Estética Manager</span>
            </div>
          </Link>

          <div className={styles.clinicSelector}>
            <span className={styles.statusDot} />
            <span className={styles.clinicName}>Clínica Lumière • Matriz</span>
          </div>
        </div>

        <div className={styles.headerRight}>
          <Link to="/vendas/nova" className={styles.btnNovaVenda}>
            <span>+</span> Nova Venda
          </Link>

          <div className={styles.userMenu}>
            <div className={styles.userAvatar}>DR</div>
            <button
              type="button"
              onClick={handleLogout}
              className={styles.btnLogout}
              title="Encerrar sessão e voltar ao site"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      {/* Main Navigation Bar */}
      <nav className={styles.mainNav} aria-label="Navegação principal">
        <div className={styles.navInner}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
              }
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Page Content */}
      <main className={styles.mainContent}>
        <div className={styles.contentContainer}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
