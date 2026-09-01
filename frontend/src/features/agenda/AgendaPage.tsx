import { useState } from "react";
import { AgendaView } from "./AgendaView";
import { OpenPackagesList } from "./OpenPackagesList";
import { NewBookingModal } from "./NewBookingModal";
import { NoShowAlert } from "./NoShowAlert";

type Tab = "agenda" | "packages";

export function AgendaPage() {
  const [tab, setTab] = useState<Tab>("agenda");
  const [showBookingModal, setShowBookingModal] = useState(false);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Agenda & Atendimentos</h1>
        <button
          type="button"
          onClick={() => setShowBookingModal(true)}
          className="button tap-target"
        >
          + Reservar Horário (Provisório)
        </button>
      </header>

      <div className="tab-group" role="tablist" aria-label="Abas da agenda">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "agenda"}
          className="tab-button tap-target"
          onClick={() => setTab("agenda")}
        >
          Agenda do Dia / Semana
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "packages"}
          className="tab-button tap-target"
          onClick={() => setTab("packages")}
        >
          Pacotes com Saldo em Aberto
        </button>
      </div>

      <div className="tab-content">
        {tab === "agenda" && (
          <>
            <NoShowAlert />
            <AgendaView />
          </>
        )}
        {tab === "packages" && <OpenPackagesList />}
      </div>

      {showBookingModal && (
        <NewBookingModal onClose={() => setShowBookingModal(false)} />
      )}
    </div>
  );
}
