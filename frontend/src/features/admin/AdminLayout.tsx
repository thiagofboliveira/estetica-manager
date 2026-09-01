import { Link, NavLink, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import styles from "./AdminLayout.module.css";

export function AdminLayout() {
  const { user } = useAuth();
  
  // Guard clause extra para garantir que só admins de clínica acessam
  if (user && user.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <Link to="/admin" className={styles.brand}>
          <div className={styles.title}>Lumina</div>
          <div className={styles.badge}>Admin Local</div>
        </Link>
        
        <nav className={styles.nav}>
          <NavLink 
            to="/admin/usuarios" 
            className={({isActive}) => isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink}
          >
            Usuários
          </NavLink>
        </nav>

        <div>
          <Link to="/dashboard" className={styles.btnBack}>
            Sair do Painel Admin
          </Link>
        </div>
      </header>
      
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
