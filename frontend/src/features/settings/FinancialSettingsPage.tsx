import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useFinancialSettings, useUpdateFinancialSettings } from "./hooks";
import { FinancialSettingsForm, type FinancialSettingsFormValues } from "./FinancialSettingsForm";
import type { FinancialSettings } from "./api";

/**
 * F-012a. GET sempre resolve com dado real (o backend cria o singleton
 * com defaults de mercado no primeiro acesso) — não existe estado
 * "ainda não configurado", então não há EmptyState aqui.
 */
export function FinancialSettingsPage() {
  const query = useFinancialSettings();
  const update = useUpdateFinancialSettings();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Configuração financeira</h1>
      </header>

      <AsyncBoundary query={query} skeleton={<p>Carregando…</p>} empty={null} isEmpty={() => false}>
        {(settings: FinancialSettings) => (
          <FinancialSettingsForm
            initial={settings}
            onSubmit={(values: FinancialSettingsFormValues) => update.mutateAsync(values)}
          />
        )}
      </AsyncBoundary>
    </div>
  );
}
