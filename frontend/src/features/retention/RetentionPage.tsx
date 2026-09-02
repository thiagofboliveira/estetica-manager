import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { useRetentionOpportunities, useUpdateOpportunity } from "./hooks";
import type { PatientRetention } from "./api";

const TIMING_LABEL: Record<string, string> = {
  UPCOMING: "Em breve",
  DUE: "Na data",
  OVERDUE: "Atrasado",
};

function waLink(phone: string): string {
  // Telefone chega em E.164 (+5511987654321) — wa.me quer só dígitos.
  const digits = phone.replace(/\D/g, "");
  return `https://wa.me/${digits}`;
}

/**
 * F-015/F-015a/F-015b/F-015c. Um card por PACIENTE, não por
 * oportunidade — o backend já agrupa, ordena por valor potencial
 * decrescente (F-015a) e suprime quem foi contatada nos últimos 14
 * dias. Botão de WhatsApp desabilitado quando `can_contact=false`,
 * sempre com o motivo visível ao lado (F-015b) — nunca só cinza sem
 * explicação.
 */
export function RetentionPage() {
  const query = useRetentionOpportunities();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Quem devo chamar hoje?</h1>
      </header>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={
          <EmptyState
            tone="good"
            title="Ninguém para chamar agora"
            body="Quando alguém estiver perto da data de retorno, aparece aqui."
          />
        }
        isEmpty={(cards) => cards.length === 0}
      >
        {(cards) => (
          <ul className="list">
            {cards.map((card) => (
              <RetentionCard key={card.patient_id} card={card} />
            ))}
          </ul>
        )}
      </AsyncBoundary>
    </div>
  );
}

function RetentionCard({ card }: { card: PatientRetention }) {
  const update = useUpdateOpportunity();
  // F-015c: registrar contato é por paciente, mas o backend fecha por
  // oportunidade — mandamos CONTACTED pra primeira ainda OPEN/NO_RESPONSE.
  const firstActionable = card.opportunities.find((o) => o.status === "OPEN" || o.status === "NO_RESPONSE");

  function handleWhatsAppClick() {
    if (firstActionable) {
      update.mutate({ opportunityId: firstActionable.id, payload: { status: "CONTACTED", contact_channel: "WHATSAPP" } });
    }
  }

  return (
    <li className="list__item retention-card">
      <div className="retention-card__header">
        <span className="list__item-title">{card.patient_name}</span>
        <span className="retention-card__value">{formatBRL(money(card.total_potential_value))}</span>
      </div>

      <ul className="retention-card__opportunities">
        {card.opportunities.map((o) => (
          <li key={o.id} className="retention-card__opportunity">
            {o.procedure} — {TIMING_LABEL[o.timing] ?? o.timing} ({o.due_date})
          </li>
        ))}
      </ul>

      {card.can_contact ? (
        <a
          href={waLink(card.patient_phone as string)}
          target="_blank"
          rel="noreferrer"
          className="tap-target submit"
          onClick={handleWhatsAppClick}
        >
          Chamar no WhatsApp
        </a>
      ) : (
        <p className="retention-card__blocked">
          <span aria-hidden>🚫</span> {card.cannot_contact_reason}
        </p>
      )}
    </li>
  );
}
