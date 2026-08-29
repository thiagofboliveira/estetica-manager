import { SaleForm } from "./SaleForm";

/**
 * F-014, tela de venda avulsa. Integrada com POST /sales real (T-015).
 * Ver frontend/BACKLOG.md F-014.
 */
export function NewSalePage() {
  return (
    <div className="page">
      <header className="page__header">
        <h1>Nova venda</h1>
      </header>
      <SaleForm />
    </div>
  );
}
