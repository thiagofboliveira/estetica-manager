import { useState } from "react";
import {
  useAnamnesisTemplate,
  useUpdateTemplate,
  useCreateQuestion,
  useUpdateQuestion,
  useDeleteQuestion,
  useReorderQuestions,
  useAnamnesisSubmissions,
  useGenerateSubmissionToken,
} from "./hooks";
import type { AnamnesisQuestion, AnamnesisSubmission } from "./api";
import { QuestionModal } from "./QuestionModal";
import {
  IconPlus,
  IconCopy,
  IconAlertTriangle,
  IconTrash,
  IconArrowUp,
  IconArrowDown,
  IconCheck,
  IconUsers,
  IconX,
} from "@/ui/icons";
import styles from "./AnamnesisPage.module.css";

export function AnamnesisPage() {
  const [activeTab, setActiveTab] = useState<"questions" | "submissions">("questions");
  const [editingQuestion, setEditingQuestion] = useState<AnamnesisQuestion | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<AnamnesisSubmission | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const { data: template, isLoading } = useAnamnesisTemplate();
  const { data: submissions = [] } = useAnamnesisSubmissions();

  const updateTemplateMut = useUpdateTemplate();
  const createQuestionMut = useCreateQuestion();
  const updateQuestionMut = useUpdateQuestion();
  const deleteQuestionMut = useDeleteQuestion();
  const reorderQuestionsMut = useReorderQuestions();
  const generateTokenMut = useGenerateSubmissionToken();

  const questions = template?.questions ?? [];

  async function handleCopyGeneralLink() {
    try {
      const res = await generateTokenMut.mutateAsync({});
      const url = `${window.location.origin}/anamnese/${res.public_token}`;
      await navigator.clipboard.writeText(url);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    } catch {
      alert("Não foi possível gerar o link no momento.");
    }
  }

  async function handleToggleAutoRequest() {
    if (!template) return;
    await updateTemplateMut.mutateAsync({
      auto_request_on_booking: !template.auto_request_on_booking,
    });
  }

  async function handleSaveQuestion(data: any) {
    if (editingQuestion) {
      await updateQuestionMut.mutateAsync({
        id: editingQuestion.id,
        payload: data,
      });
    } else {
      await createQuestionMut.mutateAsync(data);
    }
  }

  async function handleDeleteQuestion(id: string) {
    if (confirm("Tem certeza que deseja remover esta pergunta da ficha de anamnese?")) {
      await deleteQuestionMut.mutateAsync(id);
    }
  }

  async function handleMove(index: number, direction: "up" | "down") {
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= questions.length) return;

    const newQuestions = [...questions];
    const [moved] = newQuestions.splice(index, 1);
    newQuestions.splice(targetIndex, 0, moved);

    const reorderPayload = newQuestions.map((q, idx) => ({
      question_id: q.id,
      order_index: idx + 1,
    }));

    await reorderQuestionsMut.mutateAsync(reorderPayload);
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <h1 className={styles.title}>Fichas de Anamnese</h1>
          <p className={styles.subtitle}>
            Questionários de saúde digitais para preenchimento ágil da paciente e prevenção de contraindicações
          </p>
        </div>

        <div className={styles.headerActions}>
          <button
            type="button"
            className={styles.btnSecondary}
            onClick={handleCopyGeneralLink}
            title="Gera um link compartilhável para qualquer paciente preencher"
          >
            {copiedLink ? <IconCheck width="16" height="16" /> : <IconCopy width="16" height="16" />}
            <span>{copiedLink ? "Link Copiado!" : "Copiar Link da Ficha"}</span>
          </button>

          <button
            type="button"
            className={styles.btnPrimary}
            onClick={() => {
              setEditingQuestion(null);
              setIsModalOpen(true);
            }}
          >
            <IconPlus width="16" height="16" />
            <span>Adicionar Pergunta</span>
          </button>
        </div>
      </header>

      {/* Card de Automação de Agendamento */}
      {template && (
        <div className={styles.automationCard}>
          <div className={styles.automationInfo}>
            <h3 className={styles.automationTitle}>
              Solicitação Automática após Agendamento Online
            </h3>
            <p className={styles.automationDesc}>
              Ao agendar pelo link público da clínica, a paciente é automaticamente convidada a preencher a anamnese na tela de confirmação e no WhatsApp.
            </p>
          </div>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={template.auto_request_on_booking}
              onChange={handleToggleAutoRequest}
            />
            <span style={{ fontWeight: 600 }}>Ativado</span>
          </label>
        </div>
      )}

      {/* Tabs */}
      <nav className={styles.tabsNav} role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "questions"}
          className={`${styles.tabBtn} ${activeTab === "questions" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("questions")}
        >
          <span>Perguntas da Ficha ({questions.length})</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "submissions"}
          className={`${styles.tabBtn} ${activeTab === "submissions" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("submissions")}
        >
          <span>Respostas Recebidas ({submissions.length})</span>
        </button>
      </nav>

      {isLoading ? (
        <div className={styles.emptyState}>Carregando ficha de anamnese...</div>
      ) : activeTab === "questions" ? (
        <div className={styles.questionsContainer}>
          {questions.map((q, idx) => (
            <div key={q.id} className={styles.questionCard}>
              <div className={styles.questionLeft}>
                <div className={styles.questionOrderBadge}>#{idx + 1}</div>
                <div className={styles.questionDetails}>
                  <h4 className={styles.questionTitle}>{q.title}</h4>
                  {q.description && <p className={styles.questionDesc}>{q.description}</p>}
                  <div className={styles.badgesRow}>
                    <span className={styles.badgeType}>
                      {q.field_type === "yes_no"
                        ? "Sim / Não"
                        : q.field_type === "text"
                        ? "Texto Curto"
                        : q.field_type === "long_text"
                        ? "Texto Longo"
                        : "Seleção"}
                    </span>
                    {q.is_required && <span className={styles.badgeRequired}>Obrigatória</span>}
                    {q.is_risk_alert && (
                      <span className={styles.badgeRisk}>
                        <IconAlertTriangle width="13" height="13" />
                        Alerta de Risco
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className={styles.questionActions}>
                <button
                  type="button"
                  className={styles.iconBtn}
                  disabled={idx === 0}
                  onClick={() => handleMove(idx, "up")}
                  title="Subir ordem"
                >
                  <IconArrowUp width="16" height="16" />
                </button>
                <button
                  type="button"
                  className={styles.iconBtn}
                  disabled={idx === questions.length - 1}
                  onClick={() => handleMove(idx, "down")}
                  title="Descer ordem"
                >
                  <IconArrowDown width="16" height="16" />
                </button>
                <button
                  type="button"
                  className={styles.iconBtn}
                  onClick={() => {
                    setEditingQuestion(q);
                    setIsModalOpen(true);
                  }}
                  title="Editar pergunta"
                >
                  Editar
                </button>
                <button
                  type="button"
                  className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                  onClick={() => handleDeleteQuestion(q.id)}
                  title="Excluir pergunta"
                >
                  <IconTrash width="16" height="16" />
                </button>
              </div>
            </div>
          ))}

          <button
            type="button"
            className={styles.addQuestionDashedBtn}
            onClick={() => {
              setEditingQuestion(null);
              setIsModalOpen(true);
            }}
          >
            <IconPlus width="18" height="18" />
            <span>Adicionar Mais uma Pergunta</span>
          </button>
        </div>
      ) : (
        /* Aba de Respostas Recebidas */
        <div className={styles.submissionsTableCard}>
          {submissions.length === 0 ? (
            <div className={styles.emptyState}>
              <IconUsers width="32" height="32" />
              <p>Nenhuma ficha de anamnese respondida até o momento.</p>
              <button
                type="button"
                className={styles.btnSecondary}
                onClick={handleCopyGeneralLink}
              >
                Copiar Link da Ficha para Enviar à Paciente
              </button>
            </div>
          ) : (
            <table className={styles.submissionsTable}>
              <thead>
                <tr>
                  <th>Paciente</th>
                  <th>Telefone</th>
                  <th>Status de Risco</th>
                  <th>Preenchido em</th>
                  <th style={{ textAlign: "right" }}>Ações</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((sub) => (
                  <tr key={sub.id}>
                    <td>
                      <strong>{sub.patient_name}</strong>
                    </td>
                    <td>{sub.patient_phone || "—"}</td>
                    <td>
                      {sub.has_risk_alerts ? (
                        <span className={styles.submissionAlertBadge}>
                          <IconAlertTriangle width="14" height="14" />
                          {sub.risk_alerts_summary?.length || 1} Alerta(s) Clínico(s)
                        </span>
                      ) : (
                        <span className={styles.submissionOkBadge}>
                          <IconCheck width="14" height="14" />
                          Sem Riscos Declarados
                        </span>
                      )}
                    </td>
                    <td>
                      {sub.submitted_at
                        ? new Date(sub.submitted_at).toLocaleDateString("pt-BR", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "Pendente"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        type="button"
                        className={styles.btnSecondary}
                        style={{ padding: "6px 12px", fontSize: "0.85rem" }}
                        onClick={() => setSelectedSubmission(sub)}
                      >
                        Ver Respostas
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Modal de Criação / Edição de Pergunta */}
      <QuestionModal
        isOpen={isModalOpen}
        question={editingQuestion}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveQuestion}
      />

      {/* Modal de Visualização de Respostas da Paciente */}
      {selectedSubmission && (
        <div className={styles.modalOverlay} onClick={() => setSelectedSubmission(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <header className={styles.modalHeader}>
              <div>
                <h3>Respostas de {selectedSubmission.patient_name}</h3>
                <p className={styles.questionDesc}>
                  Preenchido em:{" "}
                  {selectedSubmission.submitted_at
                    ? new Date(selectedSubmission.submitted_at).toLocaleString("pt-BR")
                    : "—"}
                </p>
              </div>
              <button
                type="button"
                className={styles.modalCloseBtn}
                onClick={() => setSelectedSubmission(null)}
              >
                <IconX width="20" height="20" />
              </button>
            </header>

            <div className={styles.modalBody}>
              {selectedSubmission.has_risk_alerts && (
                <div className={styles.riskAlertSection}>
                  <span className={styles.riskLabelText}>
                    <IconAlertTriangle width="16" height="16" />
                    Alertas Clínicos Identificados:
                  </span>
                  <ul style={{ margin: "4px 0 0 18px", padding: 0, color: "#b45309", fontSize: "0.9rem" }}>
                    {selectedSubmission.risk_alerts_summary.map((alertItem, i) => (
                      <li key={i}>{alertItem}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {questions.map((q) => {
                  const ans = selectedSubmission.answers?.[q.id];
                  return (
                    <div
                      key={q.id}
                      style={{
                        padding: "12px",
                        border: "1px solid var(--border, #e5e7eb)",
                        borderRadius: "8px",
                      }}
                    >
                      <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-h, #111827)" }}>
                        {q.title}
                      </div>
                      <div
                        style={{
                          marginTop: "6px",
                          fontSize: "0.95rem",
                          color: ans ? "var(--text, #1f2937)" : "#94a3b8",
                          fontWeight: ans ? 500 : 400,
                        }}
                      >
                        {ans !== undefined && ans !== null && ans !== ""
                          ? String(ans)
                          : "Não informado / Sem resposta"}
                      </div>
                    </div>
                  );
                })}
              </div>

              {selectedSubmission.signature_name && (
                <div style={{ marginTop: "10px", fontSize: "0.85rem", color: "var(--text-muted, #64748b)" }}>
                  Declaração confirmada por: <strong>{selectedSubmission.signature_name}</strong>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
