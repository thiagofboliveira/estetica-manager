import { NavLink } from "react-router-dom";

export function SettingsPage() {
  return (
    <div className="page">
      <header className="page__header">
        <h1>Configurações</h1>
      </header>
      <ul className="list">
        <li className="list__item">
          <NavLink to="financeiro" className="list__item-btn tap-target">
            <span className="list__item-title">Configuração financeira</span>
            <span className="list__item-sub">Quem paga a taxa do cartão, split e forma de pagamento padrão</span>
          </NavLink>
        </li>
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
