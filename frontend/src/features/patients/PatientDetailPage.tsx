import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { usePatient, useUpdatePatient } from "./hooks";

type Tab = "data" | "history";

export function PatientDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const query = usePatient(id);
  const update = useUpdatePatient(id);
  const [tab, setTab] = useState<Tab>("data");

  async function handleSubmit(values: PatientFormValues) {
    await update.mutateAsync({
      name: values.name,
      phone: values.phone || null,
      email: values.email || null,
      birth_date: values.birth_date || null,
      notes: values.notes || null,
      consent_whatsapp: values.consent_whatsapp,
    });
  }

  return (
    <div className="page">
      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando paciente…</p>}
        empty={<p>Paciente não encontrada.</p>}
        isEmpty={(p) => p == null}
      >
        {(patient) => {
          const cleanPhone = patient.phone ? patient.phone.replace(/\D/g, "") : null;
          const whatsappUrl =
            cleanPhone && patient.consent_whatsapp
              ? `https://wa.me/55${cleanPhone}?text=${encodeURIComponent(`Olá, ${patient.name}!`)}`
              : null;

          return (
            <>
              <header className="patient-header">
                <div className="patient-header__info">
                  <div className="patient-header__avatar">
                    {patient.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h1 className="patient-header__name">{patient.name}</h1>
                    <p className="patient-header__meta">
                      {patient.phone ? patient.phone : "Sem telefone"}
                      {patient.email ? ` • ${patient.email}` : ""}
                    </p>
                  </div>
                </div>

                <div className="patient-header__actions">
                  {whatsappUrl ? (
                    <a
                      href={whatsappUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="button button--whatsapp tap-target"
                    >
                      💬 Chamar no WhatsApp
                    </a>
                  ) : (
                    <button
                      type="button"
                      disabled
                      className="button button--secondary tap-target"
                      title={
                        !patient.phone
                          ? "Cadastre o telefone do paciente"
                          : "Paciente não autorizou contato por WhatsApp"
                      }
                    >
                      💬 WhatsApp desabilitado {!patient.consent_whatsapp ? "(sem consentimento)" : ""}
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => navigate(`/vendas/nova`)}
                    className="button tap-target"
                  >
                    + Registrar Venda
                  </button>
                </div>
              </header>

              <div className="tab-group" role="tablist" aria-label="Abas do paciente">
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "data"}
                  className="tab-button tap-target"
                  onClick={() => setTab("data")}
                >
                  Dados Cadastrais
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "history"}
                  className="tab-button tap-target"
                  onClick={() => setTab("history")}
                >
                  Resumo & Observações
                </button>
              </div>

              <div className="tab-content">
                {tab === "data" && (
                  <div className="card">
                    <PatientForm initial={patient} onSubmit={handleSubmit} submitLabel="Salvar alterações" />
                  </div>
                )}

                {tab === "history" && (
                  <div className="card patient-summary">
                    <div className="patient-summary__item">
                      <span className="summary-label">Consentimento LGPD (WhatsApp)</span>
                      <span className="summary-value">
                        {patient.consent_whatsapp ? (
                          <span className="badge badge--success">✓ Autorizado</span>
                        ) : (
                          <span className="badge badge--neutral">Não autorizado</span>
                        )}
                      </span>
                    </div>

                    <div className="patient-summary__item">
                      <span className="summary-label">Data de Nascimento</span>
                      <span className="summary-value">
                        {patient.birth_date ? new Date(patient.birth_date).toLocaleDateString("pt-BR") : "Não informada"}
                      </span>
                    </div>

                    <div className="patient-summary__item">
                      <span className="summary-label">Observações Clínicas</span>
                      <p className="summary-notes">
                        {patient.notes ? patient.notes : "Nenhuma anotação registrada."}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </>
          );
        }}
      </AsyncBoundary>
    </div>
  );
}
