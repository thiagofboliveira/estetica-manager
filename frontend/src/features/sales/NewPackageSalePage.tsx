import { PackageSaleForm } from "./PackageSaleForm";

/**
 * F-014b, venda de pacote (múltiplos itens). Separada de F-014
 * (avulso) para não atrasar o fluxo de <30s. Integrada com POST /sales
 * real (T-015). Ver frontend/BACKLOG.md F-014b.
 */
export function NewPackageSalePage() {
  return (
    <div className="page">
      <header className="page__header">
        <h1>Nova venda de pacote</h1>
      </header>
      <PackageSaleForm />
    </div>
  );
}
