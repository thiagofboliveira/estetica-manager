import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { usePublicAnamnesisForm, useSubmitPublicAnamnesis } from "./hooks";
import { IconCheck } from "@/ui/icons";
import { SignatureCanvas } from "./SignatureCanvas";
import styles from "./PublicAnamnesisPage.module.css";

export function PublicAnamnesisPage() {
  const { token } = useParams<{ token: string }>();
  const { data: form, isLoading, error } = usePublicAnamnesisForm(token);
  const submitMut = useSubmitPublicAnamnesis();

  const [patientName, setPatientName] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [agree, setAgree] = useState(false);
  const [signatureName, setSignatureName] = useState("");
  const [signatureImage, setSignatureImage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [submittedSuccess, setSubmittedSuccess] = useState(false);

  useEffect(() => {
    if (form) {
      if (form.patient_name && !patientName) {
        setPatientName(form.patient_name);
      }
      if (form.patient_phone && !patientPhone) {
        setPatientPhone(form.patient_phone);
      }
      if (form.is_submitted) {
        setSubmittedSuccess(true);
      }
    }
  }, [form]);

  if (isLoading) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container}>
          <div style={{ textAlign: "center", padding: "60px 0", color: "#64748b" }}>
            Carregando formulário de anamnese...
          </div>
        </div>
      </div>
    );
  }

  if (error || !form) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container}>
          <div className={styles.headerCard} style={{ background: "#475569" }}>
            <h1 className={styles.formTitle}>Ficha não encontrada</h1>
            <p className={styles.formDesc}>
              Este link de anamnese é inválido ou já expirou. Entre em contato com a clínica para receber um novo link.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (submittedSuccess) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container}>
          <div className={styles.successCard}>
            <div className={styles.successIcon}>
              <IconCheck width="36" height="36" />
            </div>
            <h2 className={styles.successTitle}>Ficha Enviada com Sucesso!</h2>
            <p className={styles.successText}>
              Suas respostas foram registradas e já estão disponíveis para a profissional{" "}
              <strong>{form.professional_name}</strong> preparar o seu atendimento com total segurança.
            </p>
            <p className={styles.successText} style={{ fontSize: "0.85rem", color: "#64748b" }}>
              Muito obrigada por colaborar com a sua saúde e segurança!
            </p>
          </div>
        </div>
      </div>
    );
  }

  function handleAnswerChange(questionId: string, value: any) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;

    if (!patientName.trim()) {
      setFormError("Por favor, preencha o seu nome completo.");
      return;
    }

    // Valida perguntas obrigatórias
    for (const q of form!.questions) {
      if (q.is_required) {
        const val = answers[q.id];
        if (val === undefined || val === null || (typeof val === "string" && !val.trim())) {
          setFormError(`Por favor, responda a pergunta: "${q.title}"`);
          return;
        }
      }
    }

    if (!agree) {
      setFormError(
        "É obrigatório confirmar a leitura e aceite do Termo de Consentimento e Cuidados Pós-Procedimento para prosseguir."
      );
      return;
    }

    if (!signatureName.trim()) {
      setFormError("Por favor, digite seu nome completo no campo da assinatura.");
      return;
    }

    if (!signatureImage) {
      setFormError("Por favor, desenhe sua assinatura digital no campo indicado.");
      return;
    }

    try {
      setFormError(null);
      await submitMut.mutateAsync({
        token,
        payload: {
          patient_name: patientName.trim(),
          patient_phone: patientPhone.trim() || null,
          answers,
          signature_name: signatureName.trim() || patientName.trim(),
          signature_image: signatureImage,
          tcle_accepted: agree,
        },
      });
      setSubmittedSuccess(true);
    } catch (err: any) {
      setFormError(err?.message || "Ocorreu um erro ao enviar sua ficha. Tente novamente.");
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        <header className={styles.headerCard}>
          <div className={styles.brandBadge}>
            {form.clinic_name || form.professional_name}
          </div>
          <h1 className={styles.formTitle}>{form.template_title}</h1>
          <p className={styles.formDesc}>
            {form.template_description ||
              "Responda com atenção para garantirmos a sua segurança e os melhores resultados no seu procedimento."}
          </p>
        </header>

        <form onSubmit={handleSubmit} className={styles.formCard}>
          {formError && <div className={styles.errorBanner}>{formError}</div>}

          <div>
            <h3 className={styles.sectionHeading}>Identificação</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "10px" }}>
              <div>
                <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e293b" }}>
                  Seu Nome Completo <span className={styles.requiredAsterisk}>*</span>
                </label>
                <input
                  type="text"
                  className={styles.input}
                  placeholder="Ex: Maria dos Santos"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e293b" }}>
                  Seu WhatsApp / Telefone
                </label>
                <input
                  type="tel"
                  className={styles.input}
                  placeholder="Ex: (11) 99999-8888"
                  value={patientPhone}
                  onChange={(e) => setPatientPhone(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div>
            <h3 className={styles.sectionHeading}>Perguntas de Saúde & Histórico</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "12px" }}>
              {form.questions.map((q) => {
                const currentVal = answers[q.id];

                return (
                  <div key={q.id} className={styles.questionBlock}>
                    <h4 className={styles.questionTitle}>
                      {q.title}
                      {q.is_required && <span className={styles.requiredAsterisk}>*</span>}
                    </h4>
                    {q.description && <p className={styles.questionHelp}>{q.description}</p>}

                    {/* Resposta Sim / Não */}
                    {q.field_type === "yes_no" && (
                      <div className={styles.yesNoGroup}>
                        <button
                          type="button"
                          className={`${styles.pillBtn} ${
                            currentVal === "yes" || currentVal === true || currentVal === "sim"
                              ? styles.pillBtnActiveYes
                              : ""
                          }`}
                          onClick={() => handleAnswerChange(q.id, "yes")}
                        >
                          Sim
                        </button>
                        <button
                          type="button"
                          className={`${styles.pillBtn} ${
                            currentVal === "no" || currentVal === false || currentVal === "não"
                              ? styles.pillBtnActiveNo
                              : ""
                          }`}
                          onClick={() => handleAnswerChange(q.id, "no")}
                        >
                          Não
                        </button>
                      </div>
                    )}

                    {/* Resposta Texto Curto */}
                    {q.field_type === "text" && (
                      <input
                        type="text"
                        className={styles.input}
                        placeholder="Digite sua resposta..."
                        value={currentVal || ""}
                        onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                        required={q.is_required}
                      />
                    )}

                    {/* Resposta Texto Longo */}
                    {q.field_type === "long_text" && (
                      <textarea
                        className={styles.textarea}
                        rows={3}
                        placeholder="Descreva detalhadamente..."
                        value={currentVal || ""}
                        onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                        required={q.is_required}
                      />
                    )}

                    {/* Seleção / Múltipla Escolha */}
                    {q.field_type === "select" && (
                      <select
                        className={styles.select}
                        value={currentVal || ""}
                        onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                        required={q.is_required}
                      >
                        <option value="">Selecione uma opção...</option>
                        {q.options?.map((opt, i) => (
                          <option key={i} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Termo de Consentimento Livre e Esclarecido (TCLE) & Cuidados Pós */}
          <div className={styles.tcleCard}>
            <h4 className={styles.tcleTitle}>
              📜 Termo de Consentimento Livre e Esclarecido (TCLE) & Cuidados Pós
            </h4>
            <div className={styles.tcleTextBox}>
              {form.tcle_content ||
                `1. CIÊNCIA E OBJETIVOS:
Declaro que recebi explicações detalhadas e claras sobre os procedimentos estéticos aos quais serei submetida(o), seus objetivos, benefícios esperados e eventuais limitações técnicas individuais de resposta biológica.

2. CUIDADOS OBRIGATÓRIOS PÓS-PROCEDIMENTO:
- Proteção Solar Rigorosa: Aplicar protetor solar com FPS 30 ou superior a cada 3 horas e evitar exposição solar direta nas primeiras 48 a 72 horas.
- Não Manipular a Área: Não coçar, esfoliar, esfregar ou puxar casquinhas/películas da pele tratada.
- Procedimentos Injetáveis (ex: Botox): Não deitar ou abaixar a cabeça nas primeiras 4 horas após a aplicação e não realizar atividade física intensa nas 24 horas seguintes.
- Ácidos e Peelings: Suspender o uso de ácidos domiciliares pelo período expressamente orientado pela profissional.
- Higiene e Hidratação: Manter a região tratada limpa e utilizar apenas os produtos recomendados pela profissional responsável.

3. DECLARAÇÃO DE VERACIDADE:
Afirmo sob minha responsabilidade que todas as informações de saúde prestadas neste formulário de anamnese são verdadeiras e completas, não tendo omitido alergias, uso de medicamentos, gestação ou condições clínicas preexistentes.`}
            </div>

            <label className={styles.checkboxLabel} style={{ marginTop: "4px" }}>
              <input
                type="checkbox"
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
                style={{ marginTop: "2px" }}
                required
              />
              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e293b" }}>
                Declaro que li, compreendi e aceito integralmente o Termo de Consentimento e todas as orientações pós-procedimento acima, atestando a veracidade das minhas respostas. <span className={styles.requiredAsterisk}>*</span>
              </span>
            </label>
          </div>

          <div className={styles.agreementBlock}>
            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e293b" }}>
                Nome Completo do Declarante (Assinatura do Titular) <span className={styles.requiredAsterisk}>*</span>
              </label>
              <input
                type="text"
                className={styles.input}
                style={{ marginTop: "4px" }}
                placeholder={patientName || "Seu nome completo"}
                value={signatureName}
                onChange={(e) => setSignatureName(e.target.value)}
                required
              />
            </div>

            <div style={{ marginTop: "10px" }}>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1e293b", marginBottom: "6px", display: "block" }}>
                Assinatura Digital (Desenhe com o dedo na tela ou mouse) <span className={styles.requiredAsterisk}>*</span>
              </label>
              <SignatureCanvas onSignatureChange={setSignatureImage} />
            </div>
          </div>

          <button
            type="submit"
            className={styles.btnSubmit}
            disabled={submitMut.isPending}
          >
            {submitMut.isPending ? "Enviando Ficha..." : "Confirmar e Enviar Ficha de Anamnese"}
          </button>
        </form>
      </div>
    </div>
  );
}
