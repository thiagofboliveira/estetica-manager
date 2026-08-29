import { NavLink, Outlet } from "react-router-dom";

/**
 * Ordem do menu é deliberada (MVP v6 §16.5): Dashboard e Retornos antes
 * de Agenda. Agenda é suporte ao fluxo financeiro/retenção, nunca a
 * manchete — se o produto virar "sistema de agendamento", perde o que
 * o diferencia.
 */
const NAV_ITEMS: { to: string; label: string; end: boolean }[] = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/vendas/nova", label: "Nova venda", end: false },
  { to: "/retornos", label: "Retornos", end: false },
  { to: "/pacientes", label: "Pacientes", end: false },
  { to: "/procedimentos", label: "Procedimentos", end: false },
  { to: "/agenda", label: "Agenda", end: false },
  { to: "/configuracoes", label: "Configurações", end: false },
];

export function AppLayout() {
  return (
    <div className="app-layout">
      <nav className="app-layout__nav" aria-label="Navegação principal">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className="tap-target">
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="app-layout__main">
        <Outlet />
      </main>
    </div>
  );
}
