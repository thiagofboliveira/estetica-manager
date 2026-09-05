import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { FinancialSettingsForm } from "./FinancialSettingsForm";
import { useFinancialSettings } from "./hooks";

export function FinancialSettingsPage() {
  const financialQuery = useFinancialSettings();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Financeiro &amp; Taxas</h1>
      </header>

      <AsyncBoundary
        query={financialQuery}
        skeleton={<p>Carregando configurações financeiras…</p>}
        empty={<p>Não foi possível carregar as configurações.</p>}
      >
        {(settings) => <FinancialSettingsForm initial={settings} />}
      </AsyncBoundary>
    </div>
  );
}
