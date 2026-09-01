import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import type { OpenPackage } from "./api";
import { useOpenPackages } from "./hooks";
import { ScheduleSessionModal } from "./ScheduleSessionModal";

export function OpenPackagesList() {
  const query = useOpenPackages();
  const [selectedPkg, setSelectedPkg] = useState<OpenPackage | null>(null);

  return (
    <div className="packages-open">
      <div className="section-header">
        <h2>Pacotes com Saldo em Aberto</h2>
        <p className="section-desc">
          Pacientes que adquiriram pacotes e possuem sessões restantes para agendamento.
        </p>
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando pacotes em aberto…</p>}
        empty={
          <EmptyState
            tone="good"
            title="Nenhum pacote pendente de agendamento"
            body="Todas as sessões de pacotes já foram realizadas ou estão com horário marcado."
          />
        }
        isEmpty={(packages) => packages.length === 0}
      >
        {(packages) => (
          <div className="packages-grid">
            {packages.map((pkg) => {
              const progressPct = Math.round((pkg.used_sessions / pkg.total_sessions) * 100);

              return (
                <article key={pkg.sale_item_id} className="card package-card">
                  <div className="package-card__header">
                    <div className="package-card__avatar">
                      {pkg.patient_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="package-card__patient">{pkg.patient_name}</h3>
                      <span className="package-card__proc">{pkg.procedure_name}</span>
                    </div>
                  </div>

                  <div className="package-card__progress">
                    <div className="package-card__progress-info">
                      <span>Progresso do Pacote</span>
                      <strong>
                        {pkg.used_sessions} de {pkg.total_sessions} sessões ({pkg.pending_sessions} restantes)
                      </strong>
                    </div>
                    <div className="progress-bar-track">
                      <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
                    </div>
                  </div>

                  {pkg.last_session_completed_at && (
                    <p className="package-card__last-session">
                      Última sessão: {new Date(pkg.last_session_completed_at).toLocaleDateString("pt-BR")}
                    </p>
                  )}

                  <div className="package-card__footer">
                    <button
                      type="button"
                      onClick={() => setSelectedPkg(pkg)}
                      className="button tap-target"
                      disabled={pkg.pending_sessions === 0}
                    >
                      🗓️ Agendar próxima sessão
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </AsyncBoundary>

      {selectedPkg && (
        <ScheduleSessionModal
          pkg={selectedPkg}
          onClose={() => setSelectedPkg(null)}
        />
      )}
    </div>
  );
}
