import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { IconInfo, IconWhatsApp } from "@/ui/icons";
import { MESSAGES, fillTemplate } from "@/lib/constants/messages";
import { toWhatsAppUrl } from "@/lib/whatsapp";
import { useReengagement } from "./hooks";
import { retentionApi, type ReengagementKind, type ReengagementPatient } from "./api";
import { useDraftComposer } from "./useDraftComposer";
import { IconSparkles } from "@/ui/icons";
import styles from "./ReengagementSection.module.css";

function daysSince(isoDate: string): number {
  const diffMs = Date.now() - new Date(isoDate).getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

function ReengagementRow({ patient }: { patient: ReengagementPatient }) {
  const kind: ReengagementKind = patient.last_treated_at ? "inactive" : "never_treated";
  const composer = useDraftComposer(
    () => retentionApi.draftReengagementMessage(patient.patient_id, kind),
    { patientId: patient.patient_id },
  );
  const defaultMessage = fillTemplate(MESSAGES.RETENTION.WHATSAPP_REENGAGEMENT, {
    patient_name: patient.patient_name,
  });
  const whatsappUrl = patient.consent_whatsapp
    ? toWhatsAppUrl(patient.patient_phone, composer.message ?? defaultMessage)
    : null;

  return (
    <div className={styles.row}>
      <div className={styles.rowInfo}>
        <span className={styles.rowName}>{patient.patient_name}</span>
        <span className={styles.rowMeta}>
          {patient.last_treated_at
            ? `Sem tratamento há ${daysSince(patient.last_treated_at)} dias`
            : "Nunca fez um tratamento"}
          {!patient.patient_phone && " • Sem telefone"}
        </span>
      </div>
      {whatsappUrl ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", alignItems: "flex-end" }}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
            <button
              type="button"
              onClick={composer.generate}
              disabled={composer.pending}
              className="button button--secondary tap-target"
            >
              <IconSparkles width="16" height="16" />
              <span>{composer.pending ? "Gerando…" : "Sugerir mensagem"}</span>
            </button>
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noreferrer"
              onClick={composer.reportSent}
              className="button button--whatsapp tap-target"
            >
              <IconWhatsApp width="16" height="16" />
              <span>Chamar</span>
            </a>
          </div>
          {composer.message !== null && (
            <textarea
              aria-label={`Mensagem para ${patient.patient_name}`}
              value={composer.message}
              onChange={(e) => composer.setMessage(e.target.value)}
              rows={4}
              style={{ width: "100%", fontSize: "16px" }}
            />
          )}
          {composer.notice && <span style={{ fontSize: "12px" }}>{composer.notice}</span>}
        </div>
      ) : (
        <button
          type="button"
          disabled
          className="button button--secondary tap-target"
          title={!patient.patient_phone ? "Sem telefone cadastrado" : "Sem consentimento de WhatsApp"}
        >
          <IconWhatsApp width="16" height="16" />
          <span>Indisponível</span>
        </button>
      )}
    </div>
  );
}

/**
 * F4-05: seções de reengajamento (nunca tratou / parado há X dias) —
 * fonte SEPARADA do motor de retorno real acima na mesma página (E4,
 * decisão do usuário). Não é oportunidade de retorno "prevista" (I7):
 * são candidatos a reengajamento (captação de paciente frio), sem
 * data de vencimento calculada por fórmula.
 */
const PAGE_SIZE = 20;

export function ReengagementSection() {
  const [inactiveDays, setInactiveDays] = useState(60);
  const [inputValue, setInputValue] = useState("60");
  const [page, setPage] = useState(1);
  const query = useReengagement(inactiveDays, page, PAGE_SIZE);

  function applyDays() {
    const parsed = Number(inputValue);
    if (Number.isFinite(parsed) && parsed >= 1) {
      setInactiveDays(Math.floor(parsed));
      setPage(1);
    } else {
      setInputValue(String(inactiveDays));
    }
  }

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Reengajamento</h2>
          <p className={styles.subtitle}>
            <IconInfo width="12" height="12" style={{ verticalAlign: "-1px", marginRight: "4px" }} />
            Diferente das oportunidades acima: aqui não há previsão de retorno calculada — são
            pacientes frios que talvez valha a pena chamar de volta.
          </p>
        </div>
        <div className={styles.controls}>
          <label htmlFor="inactive-days">Parado há mais de</label>
          <input
            id="inactive-days"
            type="number"
            min={1}
            className={styles.daysInput}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onBlur={applyDays}
            onKeyDown={(e) => e.key === "Enter" && applyDays()}
          />
          <span>dias</span>
        </div>
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Buscando pacientes…</p>}
        isEmpty={(data) => data.never_treated.length === 0 && data.inactive.length === 0}
        empty={<p className={styles.subtitle}>Nenhum paciente frio no momento.</p>}
      >
        {(data) => {
          const totalPages = Math.max(
            1,
            Math.ceil(
              Math.max(data.never_treated_total_count, data.inactive_total_count) / PAGE_SIZE,
            ),
          );

          return (
            <>
              <div className={styles.groups}>
                {data.never_treated.length > 0 && (
                  <div className={styles.group}>
                    <span className={styles.groupLabel}>
                      Nunca fizeram um tratamento ({data.never_treated_total_count})
                    </span>
                    <div className={styles.list}>
                      {data.never_treated.map((p) => (
                        <ReengagementRow key={p.patient_id} patient={p} />
                      ))}
                    </div>
                  </div>
                )}

                {data.inactive.length > 0 && (
                  <div className={styles.group}>
                    <span className={styles.groupLabel}>
                      Parados há mais de {data.inactive_days_threshold} dias (
                      {data.inactive_total_count})
                    </span>
                    <div className={styles.list}>
                      {data.inactive.map((p) => (
                        <ReengagementRow key={p.patient_id} patient={p} />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {totalPages > 1 && (
                <nav className="pagination" aria-label="Páginas de reengajamento">
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    ← Anterior
                  </button>
                  <span className="pagination__status">
                    Página {page} de {totalPages}
                  </span>
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Próxima →
                  </button>
                </nav>
              )}
            </>
          );
        }}
      </AsyncBoundary>
    </section>
  );
}
