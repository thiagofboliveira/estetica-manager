import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { ImpersonationBanner } from "./ImpersonationBanner";
import { Sidebar } from "./Sidebar";
import {
  IconSparkles,
  IconPlus,
  IconShield,
  IconCrown,
  IconLogout,
  IconWhatsApp,
  IconMenu,
  IconX,
} from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./AppLayout.module.css";

export function AppLayout() {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";
  const isGlobalAdmin = user?.role === "superadmin";
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className={styles.appLayout}>
      <ImpersonationBanner />

      {/* Sidebar — fixa no desktop, drawer retrátil no mobile (F6-04) */}
      <aside className={`${styles.sidebarRail} ${drawerOpen ? styles.sidebarRailOpen : ""}`}>
        <div className={styles.sidebarHeader}>
          <Link to="/dashboard" className={styles.brandLogo} onClick={() => setDrawerOpen(false)}>
            <div className={styles.logoBadge}>
              <IconSparkles width="18" height="18" />
            </div>
            <div className={styles.brandText}>
              <span className={styles.brandName}>Lumina</span>
              <span className={styles.brandSub}>Estética Manager</span>
            </div>
          </Link>
          <button
            type="button"
            className={styles.drawerCloseBtn}
            onClick={() => setDrawerOpen(false)}
            aria-label="Fechar menu"
          >
            <IconX width="20" height="20" />
          </button>
        </div>

        <Sidebar onNavigate={() => setDrawerOpen(false)} />

        <div className={styles.sidebarFooter}>
          <div className={styles.userAvatar}>{user?.name?.[0]?.toUpperCase() ?? "U"}</div>
          <div className={styles.sidebarFooterInfo}>
            <span className={styles.sidebarFooterName}>{user?.name ?? "Usuária"}</span>
            <span className={styles.sidebarFooterClinic}>{user?.clinic_name || "Clínica Principal"}</span>
          </div>
          <button
            type="button"
            onClick={logout}
            className={styles.btnLogout}
            title="Encerrar sessão"
          >
            <IconLogout width="16" height="16" />
          </button>
        </div>
      </aside>

      {drawerOpen && (
        <div
          className={styles.drawerOverlay}
          onClick={() => setDrawerOpen(false)}
          aria-hidden
        />
      )}

      <div className={styles.contentColumn}>
        {/* Top bar fina — ações rápidas, tema, atalhos admin (F6-02) */}
        <header className={styles.topHeader}>
          <button
            type="button"
            className={styles.hamburgerBtn}
            onClick={() => setDrawerOpen(true)}
            aria-label="Abrir menu"
          >
            <IconMenu width="22" height="22" />
          </button>

          <div className={styles.headerRight}>
            <Link
              to="/agenda/rapido"
              className={styles.btnNovaVenda}
              title="Ver horários livres e responder rápido no WhatsApp"
            >
              <IconWhatsApp width="16" height="16" />
              <span>Modo Ocupado</span>
            </Link>

            <Link to="/vendas/nova" className={styles.btnNovaVenda}>
              <IconPlus width="16" height="16" />
              <span>Nova Venda</span>
            </Link>

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
          </div>
        </header>

        {/* Page Content */}
        <main className={styles.mainContent}>
          <div className={styles.contentContainer}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
