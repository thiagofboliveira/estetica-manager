import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { ImpersonationBanner } from "./ImpersonationBanner";
import {
  IconDashboard,
  IconTarget,
  IconCalendar,
  IconUsers,
  IconSparkles,
  IconSettings,
  IconPlus,
  IconShield,
  IconCrown,
  IconLogout,
} from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./AppLayout.module.css";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", Icon: IconDashboard, end: true },
  { to: "/retornos", label: "Quem chamar hoje?", Icon: IconTarget, end: false },
  { to: "/agenda", label: "Agenda", Icon: IconCalendar, end: false },
  { to: "/pacientes", label: "Pacientes", Icon: IconUsers, end: false },
  { to: "/procedimentos", label: "Procedimentos", Icon: IconSparkles, end: false },
  { to: "/configuracoes", label: "Configurações", Icon: IconSettings, end: false },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";
  const isGlobalAdmin = user?.role === "superadmin";

  return (
    <div className={styles.appLayout}>
      <ImpersonationBanner />
      {/* Top Navbar */}
      <header className={styles.topHeader}>
        <div className={styles.headerLeft}>
          <Link to="/dashboard" className={styles.brandLogo}>
            <div className={styles.logoBadge}>
              <IconSparkles width="18" height="18" />
            </div>
            <div className={styles.brandText}>
              <span className={styles.brandName}>Lumina</span>
              <span className={styles.brandSub}>Estética Manager</span>
            </div>
          </Link>

          <div className={styles.clinicSelector}>
            <span className={styles.statusDot} />
            <span className={styles.clinicName}>{user?.clinic_name || "Clínica Principal"}</span>
          </div>
        </div>

        <div className={styles.headerRight}>
          <Link to="/vendas/nova" className={styles.btnNovaVenda}>
            <IconPlus width="16" height="16" />
            <span>Nova Venda</span>
          </Link>

          <div className={styles.userMenu}>
            <ThemeToggle />
            {isAdmin && (
              <Link to="/admin" className={styles.adminLink} title="Painel da Clínica">
                <IconShield width="15" height="15" />
                <span>Admin</span>
              </Link>
            )}
            {isGlobalAdmin && (
              <Link to="/super-admin" className={styles.superAdminLink} title="Painel Plataforma SaaS">
                <IconCrown width="15" height="15" />
                <span>Painel SaaS</span>
              </Link>
            )}
            <div className={styles.userAvatar}>{user?.name?.[0]?.toUpperCase() ?? "U"}</div>
            <button
              type="button"
              onClick={logout}
              className={styles.btnLogout}
              title="Encerrar sessão"
            >
              <IconLogout width="16" height="16" />
              <span>Sair</span>
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
                isActive ? `${styles.navItem} ${styles.navItemActive}` : styles.navItem
              }
            >
              <span className={styles.navIcon}>
                <item.Icon width="17" height="17" />
              </span>
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
