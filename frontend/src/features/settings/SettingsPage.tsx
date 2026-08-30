import { NavLink } from "react-router-dom";

/**
 * Hub mínimo — só o suficiente para tornar /configuracoes/despesas
 * alcançável (F-012b). A config financeira em si (F-012a: split, taxas,
 * forma de pagamento padrão) ainda não tem tela; ver frontend/BACKLOG.md
 * — "Ver F-021 para a linguagem" antes de construir aquele form.
 */
export function SettingsPage() {
  return (
    <div className="page">
      <header className="page__header">
        <h1>Configurações</h1>
      </header>
      <ul className="list">
        <li className="list__item">
          <NavLink to="despesas" className="list__item-btn tap-target">
            <span className="list__item-title">Despesas fixas</span>
            <span className="list__item-sub">Aluguel, assinaturas e outros custos recorrentes</span>
          </NavLink>
        </li>
      </ul>
    </div>
  );
}
