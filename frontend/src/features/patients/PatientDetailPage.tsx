import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { useAnonymizePatient, useOptOutPatient, usePatient, useUpdatePatient } from "./hooks";
import { patientsApi } from "./api";

type Tab = "data" | "history";

export function PatientDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const query = usePatient(id);
  const update = useUpdatePatient(id);
  const anonymize = useAnonymizePatient(id);
  const optOut = useOptOutPatient(id);
  const [tab, setTab] = useState<Tab>("data");
  const [exporting, setExporting] = useState(false);

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

  async function handleExport() {
    setExporting(true);
    try {
      const data = await patientsApi.exportData(id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `paciente_${id}_lgpd.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Erro ao exportar dados do paciente.");
    } finally {
      setExporting(false);
    }
  }

  async function handleOptOut() {
    if (confirm("Deseja registrar o Opt-Out de comunicações por WhatsApp para esta paciente?")) {
      await optOut.mutateAsync();
    }
  }

  async function handleAnonymize() {
    if (
      confirm(
        "Atenção: A anonimização é irreversível e substituirá nome, telefone e dados pessoais por identificadores anônimos para conformidade com a LGPD. Confirmar?"
      )
    ) {
      await anonymize.mutateAsync();
      navigate("/pacientes");
    }
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
                    onClick={() => navigate(`/vendas/nova?patient_id=${patient.id}`)}
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
                  Resumo, Privacidade & LGPD
                </button>
              </div>

              <div className="tab-content">
                {tab === "data" && (
                  <div className="card">
                    <PatientForm initial={patient} onSubmit={handleSubmit} submitLabel="Salvar alterações" />
                  </div>
                )}

                {tab === "history" && (
                  <div className="card patient-summary" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
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

                    <hr style={{ borderColor: "#e2e8f0", margin: "8px 0" }} />

                    <div>
                      <h3 style={{ fontSize: "15px", fontWeight: 700, marginBottom: "8px", color: "#0f172a" }}>
                        Privacidade & Direitos do Titular (LGPD)
                      </h3>
                      <p style={{ fontSize: "13px", color: "#64748b", marginBottom: "16px" }}>
                        Ações para atender aos direitos de revogação de consentimento, portabilidade e eliminação de dados.
                      </p>

                      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                        <button
                          type="button"
                          onClick={handleExport}
                          disabled={exporting}
                          className="button button--secondary tap-target"
                          style={{ fontSize: "13px" }}
                        >
                          📦 {exporting ? "Exportando..." : "Exportar Dados (JSON)"}
                        </button>

                        {patient.consent_whatsapp && (
                          <button
                            type="button"
                            onClick={handleOptOut}
                            disabled={optOut.isPending}
                            className="button button--secondary tap-target"
                            style={{ fontSize: "13px", color: "#d97706" }}
                          >
                            🚫 Registrar Opt-Out
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={handleAnonymize}
                          disabled={anonymize.isPending}
                          className="button tap-target"
                          style={{ fontSize: "13px", background: "#ef4444", color: "#fff" }}
                        >
                          🗑️ Anonimizar Paciente
                        </button>
                      </div>
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
