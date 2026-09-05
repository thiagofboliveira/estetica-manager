import { cmp, money } from "@/lib/money/money";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { useRetentionCards } from "./hooks";
import { RetentionCard } from "./RetentionCard";
import { ReengagementSection } from "./ReengagementSection";

export function RetentionPage() {
  const query = useRetentionCards();

  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1>Quem devo chamar hoje?</h1>
          <p className="page__subtitle">
            Pacientes na janela ideal de retorno clínico ou preventivo para reativar faturamento.
          </p>
        </div>
      </header>

      <AsyncBoundary
        query={query}
        skeleton={<p>Buscando oportunidades de retorno…</p>}
        empty={
          <EmptyState
            tone="good"
            title="Ninguém para chamar hoje!"
            body="Todos os retornos estão em dia ou os pacientes já têm agendamentos futuros."
          />
        }
        isEmpty={(cards) => cards.length === 0}
      >
        {(cards) => {
          // F-015a: Ordenação por valor financeiro potencial decrescente usando o comparador puro cmp
          const sortedCards = cards
            .slice()
            .sort((a, b) => cmp(money(b.total_potential_value), money(a.total_potential_value)));

          return (
            <div className="retention-list">
              {sortedCards.map((card) => (
                <RetentionCard key={card.patient_id} card={card} />
              ))}
            </div>
          );
        }}
      </AsyncBoundary>

      <ReengagementSection />
    </div>
  );
}
