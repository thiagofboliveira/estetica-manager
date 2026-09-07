import { useState } from "react";
import { IconCalendar, IconSparkles, IconWhatsApp } from "@/ui/icons";
import { formatDateToLocalInput } from "@/lib/format/date";
import { NewBookingModal } from "@/features/agenda/NewBookingModal";
import styles from "./PostSaleRebookingPrompt.module.css";

interface PostSaleRebookingPromptProps {
  patient: {
    name: string;
    phone?: string | null;
  };
  procedureName: string;
  returnIntervalDays?: number | null;
}

export function PostSaleRebookingPrompt({
  patient,
  procedureName,
  returnIntervalDays,
}: PostSaleRebookingPromptProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [booked, setBooked] = useState(false);

  const days = returnIntervalDays && returnIntervalDays > 0 ? returnIntervalDays : 30;
  const targetDate = new Date();
  targetDate.setDate(targetDate.getDate() + days);
  targetDate.setHours(14, 0, 0, 0);

  const formattedDate = targetDate.toLocaleDateString("pt-BR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const weekday = targetDate.toLocaleDateString("pt-BR", { weekday: "long" });

  const rawPhone = patient.phone?.replace(/\D/g, "") || "";
  const phoneFormatted = rawPhone.length >= 10 && !rawPhone.startsWith("55") ? `55${rawPhone}` : rawPhone;

  const whatsappMessage = `Oi ${patient.name}! Foi um prazer te atender hoje ✨ Para manter os resultados impecáveis do seu ${procedureName}, sua próxima sessão ideal será em torno de ${formattedDate}. Já quer deixar reservado o seu horário para garantir a vaga?`;
  const whatsappUrl = `https://api.whatsapp.com/send?phone=${phoneFormatted}&text=${encodeURIComponent(
    whatsappMessage
  )}`;

  return (
    <div className={styles.card} role="region" aria-label="Loop de Reagendamento">
      <div className={styles.header}>
        <div className={styles.badge}>
          <IconSparkles width="13" height="13" />
          <span>Próxima Sessão na Saída</span>
        </div>
        <span style={{ fontSize: "12px", color: "#6366f1", fontWeight: 600 }}>
          Retorno em ~{days} dias
        </span>
      </div>

      <div>
        <h3 className={styles.title}>
          Garantir o próximo agendamento de {patient.name}?
        </h3>
        <p className={styles.bodyText}>
          A cliente ainda está na recepção ou finalizando o atendimento. Aproveite este momento para garantir a continuidade do tratamento de <strong>{procedureName}</strong> antes que a rotina tome conta!
        </p>
      </div>

      <div className={styles.highlightDate}>
        <IconCalendar width="16" height="16" color="#4f46e5" />
        <span>
          Sugestão: <strong>{weekday}, {formattedDate}</strong>
        </span>
      </div>

      <div className={styles.actions}>
        {booked ? (
          <span style={{ color: "#16a34a", fontWeight: 600, fontSize: "13.5px" }}>
            ✅ Próxima sessão agendada com sucesso!
          </span>
        ) : (
          <button
            type="button"
            className={styles.primaryBtn}
            onClick={() => setIsModalOpen(true)}
          >
            <IconCalendar width="15" height="15" />
            <span>Agendar Retorno Agora</span>
          </button>
        )}

        {rawPhone && (
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`${styles.secondaryBtn} ${styles.whatsappBtn}`}
          >
            <IconWhatsApp width="15" height="15" />
            <span>Enviar Convite no WhatsApp</span>
          </a>
        )}
      </div>

      {isModalOpen && (
        <NewBookingModal
          initialDateTime={formatDateToLocalInput(targetDate)}
          patientNameHint={patient.name}
          noteHint={`Próxima sessão sugerida (${procedureName})`}
          onClose={() => {
            setIsModalOpen(false);
            setBooked(true);
          }}
        />
      )}
    </div>
  );
}
