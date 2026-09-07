import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { ImpersonationBanner } from "@/app/layout/ImpersonationBanner";
import { IconSparkles, IconBuilding, IconUsers, IconLogout, IconMenu, IconX } from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./SuperAdminLayout.module.css";

export function SuperAdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Guard clause para Super Admin Global
  if (user && user.role !== "superadmin") {
    navigate("/dashboard", { replace: true });
    return null;
  }

  return (
    <div className={styles.layout}>
      <ImpersonationBanner />

      {/* Header Mobile com botão de menu e identidade */}
      <header className={styles.mobileHeader}>
        <button
          type="button"
          className={styles.mobileMenuBtn}
          onClick={() => setDrawerOpen(true)}
          aria-label="Abrir menu de navegação"
        >
          <IconMenu width="22" height="22" />
        </button>

        <div className={styles.mobileBrand}>
          <div className={styles.logoBadgeSmall}>
            <IconSparkles width="15" height="15" />
          </div>
          <span className={styles.mobileBrandTitle}>Lumina SaaS</span>
        </div>

        <div className={styles.mobileUserAvatar}>
          {user?.name?.[0]?.toUpperCase() ?? "S"}
        </div>
      </header>

      {/* Backdrop para fechar drawer no mobile */}
      {drawerOpen && (
        <div
          className={styles.backdrop}
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar: fixa em desktop, drawer deslizante no mobile */}
      <aside className={`${styles.sidebar} ${drawerOpen ? styles.sidebarOpen : ""}`}>
        <div className={styles.brand}>
          <div className={styles.logoBadge}>
            <IconSparkles width="18" height="18" />
          </div>
          <div className={styles.brandText}>
            <span className={styles.brandName}>Lumina</span>
            <span className={styles.brandSub}>SaaS Platform</span>
          </div>
          <button
            type="button"
            className={styles.closeBtn}
            onClick={() => setDrawerOpen(false)}
            aria-label="Fechar menu"
          >
            <IconX width="20" height="20" />
          </button>
        </div>
        
        <nav className={styles.nav}>
          <NavLink
            to="/super-admin/clinicas"
            onClick={() => setDrawerOpen(false)}
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            <IconBuilding width="18" height="18" />
            <span>Clínicas (Tenants)</span>
          </NavLink>
          <NavLink
            to="/super-admin/usuarios"
            onClick={() => setDrawerOpen(false)}
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            <IconUsers width="18" height="18" />
            <span>Usuários Globais</span>
          </NavLink>
          <NavLink
            to="/dashboard"
            onClick={() => setDrawerOpen(false)}
            className={styles.navLink}
            title="Acessar painel de atendimento da clínica"
          >
            <IconSparkles width="18" height="18" />
            <span>Visão da Clínica</span>
          </NavLink>
        </nav>

        <div className={styles.userSection}>
          <ThemeToggle showLabel />
          <div className={styles.userInfo}>
            <div className={styles.avatar}>{user?.name?.[0]?.toUpperCase() ?? "S"}</div>
            <div className={styles.userMeta}>
              <span className={styles.userName}>{user?.name}</span>
              <span className={styles.userRole}>Super Admin</span>
            </div>
          </div>
          <button className={styles.btnLogout} onClick={logout} title="Encerrar sessão">
            <IconLogout width="16" height="16" />
            <span>Sair</span>
          </button>
        </div>
      </aside>

      <main className={styles.main}>
        <div className={styles.mainContainer}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
