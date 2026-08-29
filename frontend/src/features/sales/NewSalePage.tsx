import { SaleForm } from "./SaleForm";

/**
 * PROTÓTIPO — F-014, tela de venda avulsa. Sem integração com API
 * (T-012..T-015 não existem no backend ainda) — objetivo é validar
 * layout, campos e o critério de <30s antes de codar contra a API real.
 * Ver frontend/BACKLOG.md F-014.
 */
export function NewSalePage() {
  async function handleConfirm() {
    // PROTÓTIPO: simula latência de rede para testar a sensação do fluxo.
    await new Promise((resolve) => setTimeout(resolve, 400));
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Nova venda</h1>
      </header>
      <SaleForm onConfirm={handleConfirm} />
    </div>
  );
}
