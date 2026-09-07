import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { PatientForm, type PatientFormValues } from "./PatientForm";
import { useAnonymizePatient, useOptOutPatient, usePatient, useUpdatePatient } from "./hooks";
import { usePatientAnamnesis, useGenerateSubmissionToken } from "@/features/anamnesis/hooks";
import { IconAlertTriangle, IconCheck, IconCopy } from "@/ui/icons";
import { patientsApi } from "./api";

type Tab = "data" | "history" | "anamnesis";

export function PatientDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const query = usePatient(id);
  const update = useUpdatePatient(id);
  const anonymize = useAnonymizePatient(id);
  const optOut = useOptOutPatient(id);
  const anamnesisQuery = usePatientAnamnesis(id);
  const generateTokenMut = useGenerateSubmissionToken();

  const [tab, setTab] = useState<Tab>("data");
  const [exporting, setExporting] = useState(false);
  const [copiedAnamnesis, setCopiedAnamnesis] = useState(false);

  async function handleSubmit(values: PatientFormValues) {
    await update.mutateAsync({
      name: values.name,
      phone: values.phone || null,
      email: values.email || null,
      birth_date: values.birth_date || null,
      notes: values.notes || null,
      consent_whatsapp: values.consent_whatsapp,
      gender: values.gender || null,
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

          const anamnesisList = anamnesisQuery.data || [];
          const allRiskAlerts = Array.from(
            new Set(
              anamnesisList
                .filter((s) => s.has_risk_alerts)
                .flatMap((s) => s.risk_alerts_summary)
            )
          );

          async function handleCopyAnamnesis() {
            try {
              const res = await generateTokenMut.mutateAsync({
                patient_id: patient.id,
                patient_name: patient.name,
                patient_phone: patient.phone || undefined,
              });
              const url = `${window.location.origin}/anamnese/${res.public_token}`;
              await navigator.clipboard.writeText(url);
              setCopiedAnamnesis(true);
              setTimeout(() => setCopiedAnamnesis(false), 2500);
            } catch {
              alert("Não foi possível gerar o link de anamnese no momento.");
            }
          }

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

              {allRiskAlerts.length > 0 && (
                <div
                  style={{
                    background: "#fef2f2",
                    border: "1px solid #fecaca",
                    borderRadius: "12px",
                    padding: "12px 18px",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    color: "#991b1b",
                    margin: "16px 0",
                    fontSize: "0.95rem",
                  }}
                >
                  <IconAlertTriangle width="22" height="22" />
                  <div>
                    <strong>Atenção Clínica / Contraindicações Identificadas:</strong>{" "}
                    {allRiskAlerts.join(" • ")}
                  </div>
                </div>
              )}

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
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "anamnesis"}
                  className="tab-button tap-target"
                  onClick={() => setTab("anamnesis")}
                >
                  Ficha de Anamnese {anamnesisList.length > 0 ? `(${anamnesisList.length})` : ""}
                  {allRiskAlerts.length > 0 && " ⚠️"}
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

                {tab === "anamnesis" && (
                  <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                      <div>
                        <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "var(--text-h)" }}>
                          Histórico de Anamnese & Saúde
                        </h3>
                        <p style={{ margin: "2px 0 0", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          Fichas respondidas pela paciente com respostas e histórico de saúde
                        </p>
                      </div>
                      <button
                        type="button"
                        className="button button--secondary tap-target"
                        onClick={handleCopyAnamnesis}
                      >
                        {copiedAnamnesis ? <IconCheck width="16" height="16" /> : <IconCopy width="16" height="16" />}
                        <span>{copiedAnamnesis ? "Link Copiado!" : "Copiar Link para Paciente Preencher"}</span>
                      </button>
                    </div>

                    {anamnesisList.length === 0 ? (
                      <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)" }}>
                        <p style={{ margin: 0 }}>Nenhuma ficha de anamnese respondida por esta paciente ainda.</p>
                        <p style={{ margin: "6px 0 16px", fontSize: "0.85rem" }}>
                          Copie o link acima e envie pelo WhatsApp para a paciente preencher antes do procedimento.
                        </p>
                        <button
                          type="button"
                          className="button tap-target"
                          onClick={handleCopyAnamnesis}
                        >
                          Copiar Link da Anamnese
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        {anamnesisList.map((sub, idx) => (
                          <div
                            key={sub.id}
                            style={{
                              border: "1px solid var(--border)",
                              borderRadius: "12px",
                              padding: "16px",
                              background: "var(--bg-card)",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px", marginBottom: "12px" }}>
                              <div>
                                <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>
                                  Preenchimento #{anamnesisList.length - idx}
                                </span>
                                <span style={{ marginLeft: "8px", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                  {sub.submitted_at ? new Date(sub.submitted_at).toLocaleString("pt-BR") : "Pendente"}
                                </span>
                              </div>
                              {sub.has_risk_alerts ? (
                                <span style={{
                                  background: "#fef2f2",
                                  color: "#dc2626",
                                  border: "1px solid #fecaca",
                                  padding: "3px 8px",
                                  borderRadius: "6px",
                                  fontSize: "0.8rem",
                                  fontWeight: 600,
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "4px",
                                }}>
                                  <IconAlertTriangle width="13" height="13" />
                                  {sub.risk_alerts_summary?.length || 1} Alerta(s) Clínico(s)
                                </span>
                              ) : (
                                <span style={{
                                  background: "#f0fdf4",
                                  color: "#16a34a",
                                  border: "1px solid #bbf7d0",
                                  padding: "3px 8px",
                                  borderRadius: "6px",
                                  fontSize: "0.8rem",
                                  fontWeight: 500,
                                }}>
                                  ✓ Sem Riscos Declarados
                                </span>
                              )}
                            </div>

                            {sub.has_risk_alerts && (
                              <div style={{
                                background: "#fffbeb",
                                border: "1px solid #fef3c7",
                                borderRadius: "8px",
                                padding: "10px 14px",
                                marginBottom: "14px",
                                color: "#92400e",
                                fontSize: "0.85rem",
                              }}>
                                <strong>Alertas apontados:</strong> {sub.risk_alerts_summary?.join(", ")}
                              </div>
                            )}

                            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                              {Object.entries(sub.answers || {}).map(([key, val]) => (
                                <div key={key} style={{ fontSize: "0.88rem", padding: "6px 0", borderBottom: "1px solid var(--border-light, #f1f5f9)" }}>
                                  <span style={{ fontWeight: 500, color: "var(--text)" }}>
                                    {val !== undefined && val !== null ? String(val) : "—"}
                                  </span>
                                </div>
                              ))}
                            </div>

                            {sub.signature_name && (
                              <div style={{ marginTop: "12px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                                Declaração assinada por: <strong>{sub.signature_name}</strong>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
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
