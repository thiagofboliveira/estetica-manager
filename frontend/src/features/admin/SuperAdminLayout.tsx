import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { ImpersonationBanner } from "@/app/layout/ImpersonationBanner";
import { IconSparkles, IconBuilding, IconUsers, IconLogout } from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./SuperAdminLayout.module.css";

export function SuperAdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Guard clause para Super Admin Global
  if (user && user.role !== "superadmin") {
    navigate("/dashboard", { replace: true });
    return null;
  }

  return (
    <div className={styles.layout}>
      <ImpersonationBanner />
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.logoBadge}>
            <IconSparkles width="18" height="18" />
          </div>
          <div className={styles.brandText}>
            <span className={styles.brandName}>Lumina</span>
            <span className={styles.brandSub}>SaaS Platform</span>
          </div>
        </div>
        
        <nav className={styles.nav}>
          <NavLink
            to="/super-admin/clinicas"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            <IconBuilding width="18" height="18" />
            <span>Clínicas (Tenants)</span>
          </NavLink>
          <NavLink
            to="/super-admin/usuarios"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            <IconUsers width="18" height="18" />
            <span>Usuários Globais</span>
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
