import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { FinancialSettingsForm } from "./FinancialSettingsForm";
import { useFinancialSettings } from "./hooks";
import { FixedExpensesList } from "@/features/fixed-expenses/FixedExpensesList";

type Tab = "financial" | "fixed_expenses";

export function SettingsPage() {
  const [tab, setTab] = useState<Tab>("financial");
  const financialQuery = useFinancialSettings();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Configurações</h1>
      </header>

      <div className="tab-group" role="tablist" aria-label="Abas de configuração">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "financial"}
          className="tab-button tap-target"
          onClick={() => setTab("financial")}
        >
          Financeiro & Taxas
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "fixed_expenses"}
          className="tab-button tap-target"
          onClick={() => setTab("fixed_expenses")}
        >
          Despesas Fixas
        </button>
      </div>

      <div className="tab-content">
        {tab === "financial" && (
          <AsyncBoundary
            query={financialQuery}
            skeleton={<p>Carregando configurações financeiras…</p>}
            empty={<p>Não foi possível carregar as configurações.</p>}
          >
            {(settings) => <FinancialSettingsForm initial={settings} />}
          </AsyncBoundary>
        )}

        {tab === "fixed_expenses" && <FixedExpensesList />}
      </div>
    </div>
  );
}
