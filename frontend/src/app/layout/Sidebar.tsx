import { NavLink } from "react-router-dom";
import {
  IconDashboard,
  IconBarChart,
  IconTarget,
  IconCalendar,
  IconUsers,
  IconGift,
  IconSparkles,
  IconWallet,
  IconReceipt,
  IconTrendingUp,
  IconClipboard,
  IconDroplet,
  IconWhatsApp,
  IconCrown,
} from "@/ui/icons";
import styles from "./Sidebar.module.css";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", Icon: IconDashboard, end: true },
  { to: "/agenda", label: "Agenda", Icon: IconCalendar, end: false },
  { to: "/retornos", label: "Quem chamar hoje?", Icon: IconTarget, end: false },
  { to: "/disparos-whatsapp", label: "Disparos WhatsApp", Icon: IconWhatsApp, end: false },
  { to: "/relatorios", label: "Relatórios", Icon: IconBarChart, end: false },
  { to: "/pacientes", label: "Pacientes", Icon: IconUsers, end: false },
  { to: "/catalogo-vip", label: "Catálogo VIP", Icon: IconGift, end: false },
  { to: "/anamnese", label: "Anamnese", Icon: IconClipboard, end: false },
  { to: "/procedimentos", label: "Procedimentos", Icon: IconSparkles, end: false },
  { to: "/estoque", label: "Estoque & Insumos", Icon: IconDroplet, end: false },
  { to: "/simulador", label: "Simulador de Preço", Icon: IconTrendingUp, end: false },
  { to: "/financeiro", label: "Financeiro", Icon: IconWallet, end: false },
  { to: "/despesas-fixas", label: "Despesas Fixas", Icon: IconReceipt, end: false },
  { to: "/assinatura", label: "Planos & Assinatura", Icon: IconCrown, end: false },
];



type Props = {
  onNavigate?: () => void;
};

/**
 * Lista simples de itens (sem seções colapsáveis, F6-03) — com os ~7
 * itens atuais um menu plano é mais claro que agrupar; revisitar se o
 * menu crescer muito. onNavigate fecha o drawer mobile ao clicar num link.
 */
export function Sidebar({ onNavigate }: Props) {
  return (
    <nav className={styles.sidebar} aria-label="Navegação principal">
      <ul className={styles.navList}>
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.end}
              onClick={onNavigate}
              className={({ isActive }) =>
                isActive ? `${styles.navItem} ${styles.navItemActive}` : styles.navItem
              }
            >
              <span className={styles.navIcon}>
                <item.Icon width="18" height="18" />
              </span>
              <span>{item.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
