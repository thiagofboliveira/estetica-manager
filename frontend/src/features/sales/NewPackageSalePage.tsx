import { PackageSaleForm } from "./PackageSaleForm";

/**
 * PROTÓTIPO — F-014b, venda de pacote (múltiplos itens). Separada de
 * F-014 (avulso) para não atrasar o fluxo de <30s. Sem integração com
 * API. Ver frontend/BACKLOG.md F-014b.
 */
export function NewPackageSalePage() {
  async function handleConfirm() {
    // PROTÓTIPO: simula latência de rede para testar a sensação do fluxo.
    await new Promise((resolve) => setTimeout(resolve, 400));
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Nova venda de pacote</h1>
      </header>
      <PackageSaleForm onConfirm={handleConfirm} />
    </div>
  );
}
