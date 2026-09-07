import { useState, useEffect } from "react";
import type { AnamnesisQuestion, QuestionFieldType } from "./api";
import { IconX, IconAlertTriangle } from "@/ui/icons";
import styles from "./AnamnesisPage.module.css";

type Props = {
  isOpen: boolean;
  question?: AnamnesisQuestion | null;
  onClose: () => void;
  onSave: (data: {
    title: string;
    description: string | null;
    field_type: QuestionFieldType;
    options: string[] | null;
    is_required: boolean;
    is_risk_alert: boolean;
    risk_trigger_value: string | null;
  }) => Promise<void>;
};

export function QuestionModal({ isOpen, question, onClose, onSave }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [fieldType, setFieldType] = useState<QuestionFieldType>("yes_no");
  const [optionsStr, setOptionsStr] = useState("");
  const [isRequired, setIsRequired] = useState(true);
  const [isRiskAlert, setIsRiskAlert] = useState(false);
  const [riskTriggerValue, setRiskTriggerValue] = useState("yes");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (question) {
      setTitle(question.title);
      setDescription(question.description || "");
      setFieldType(question.field_type);
      setOptionsStr(question.options ? question.options.join("\n") : "");
      setIsRequired(question.is_required);
      setIsRiskAlert(question.is_risk_alert);
      setRiskTriggerValue(question.risk_trigger_value || "yes");
    } else {
      setTitle("");
      setDescription("");
      setFieldType("yes_no");
      setOptionsStr("");
      setIsRequired(true);
      setIsRiskAlert(false);
      setRiskTriggerValue("yes");
    }
    setError(null);
  }, [question, isOpen]);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("O título da pergunta é obrigatório.");
      return;
    }

    const options =
      fieldType === "select"
        ? optionsStr
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean)
        : null;

    if (fieldType === "select" && (!options || options.length < 2)) {
      setError("Perguntas de seleção devem ter pelo menos duas opções.");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await onSave({
        title: title.trim(),
        description: description.trim() || null,
        field_type: fieldType,
        options,
        is_required: isRequired,
        is_risk_alert: isRiskAlert,
        risk_trigger_value: isRiskAlert ? riskTriggerValue : null,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || "Erro ao salvar pergunta.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <header className={styles.modalHeader}>
          <h3>{question ? "Editar Pergunta" : "Nova Pergunta de Anamnese"}</h3>
          <button type="button" className={styles.modalCloseBtn} onClick={onClose}>
            <IconX width="20" height="20" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className={styles.modalBody}>
          {error && <div className={styles.formError}>{error}</div>}

          <div className={styles.formGroup}>
            <label className={styles.label}>
              Título da Pergunta <span className={styles.requiredAsterisk}>*</span>
            </label>
            <input
              type="text"
              className={styles.input}
              placeholder="Ex: Possui alguma alergia a medicamentos ou cosméticos?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Instruções ou ajuda para o paciente (opcional)</label>
            <input
              type="text"
              className={styles.input}
              placeholder="Ex: Se sim, especifique quais substâncias no campo seguinte"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Tipo de Resposta</label>
              <select
                className={styles.select}
                value={fieldType}
                onChange={(e) => setFieldType(e.target.value as QuestionFieldType)}
              >
                <option value="yes_no">Sim / Não</option>
                <option value="text">Texto Curto</option>
                <option value="long_text">Texto Longo (parágrafo)</option>
                <option value="select">Múltipla Escolha (Seleção)</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Obrigatoriedade</label>
              <div className={styles.toggleRow}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={isRequired}
                    onChange={(e) => setIsRequired(e.target.checked)}
                  />
                  <span>Resposta obrigatória</span>
                </label>
              </div>
            </div>
          </div>

          {fieldType === "select" && (
            <div className={styles.formGroup}>
              <label className={styles.label}>Opções de Resposta (uma por linha)</label>
              <textarea
                className={styles.textarea}
                rows={3}
                placeholder={"Opção 1\nOpção 2\nOpção 3"}
                value={optionsStr}
                onChange={(e) => setOptionsStr(e.target.value)}
              />
            </div>
          )}

          <div className={styles.riskAlertSection}>
            <div className={styles.riskHeader}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={isRiskAlert}
                  onChange={(e) => setIsRiskAlert(e.target.checked)}
                />
                <span className={styles.riskLabelText}>
                  <IconAlertTriangle width="16" height="16" />
                  Pergunta de Risco ou Contraindicação
                </span>
              </label>
            </div>
            {isRiskAlert && (
              <div className={styles.riskDetails}>
                <p className={styles.riskHelp}>
                  Quando o paciente responder este valor, um badge de alerta vermelho será exibido
                  em destaque no prontuário.
                </p>
                {fieldType === "yes_no" ? (
                  <div className={styles.formGroup}>
                    <label className={styles.sublabel}>Gerar alerta quando a resposta for:</label>
                    <select
                      className={styles.select}
                      value={riskTriggerValue}
                      onChange={(e) => setRiskTriggerValue(e.target.value)}
                    >
                      <option value="yes">Sim</option>
                      <option value="no">Não</option>
                    </select>
                  </div>
                ) : (
                  <div className={styles.formGroup}>
                    <label className={styles.sublabel}>Valor que dispara o alerta:</label>
                    <input
                      type="text"
                      className={styles.input}
                      placeholder="Ex: Sim"
                      value={riskTriggerValue}
                      onChange={(e) => setRiskTriggerValue(e.target.value)}
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          <footer className={styles.modalFooter}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={onClose}
              disabled={saving}
            >
              Cancelar
            </button>
            <button type="submit" className={styles.btnPrimary} disabled={saving}>
              {saving ? "Salvando..." : question ? "Salvar Alterações" : "Adicionar Pergunta"}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}
