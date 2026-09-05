import { useMemo, useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { IconWhatsApp } from "@/ui/icons";
import { toast } from "@/ui/ToastContext";
import { formatLocalDate } from "@/lib/format/date";
import { useFreeSlots } from "./hooks";
import { NewBookingModal } from "./NewBookingModal";
import styles from "./ModoOcupadoPage.module.css";

type DayOption = "today" | "tomorrow";

function dateFor(option: DayOption): string {
  const date = new Date();
  if (option === "tomorrow") date.setDate(date.getDate() + 1);
  return formatLocalDate(date);
}

function formatSlotLabel(slot: string): string {
  const [hour, minute] = slot.split(":");
  return minute === "00" ? `${Number(hour)}h` : `${Number(hour)}h${minute}`;
}

export function ModoOcupadoPage() {
  const [day, setDay] = useState<DayOption>("today");
  const [bookingSlot, setBookingSlot] = useState<string | null>(null);
  const date = useMemo(() => dateFor(day), [day]);
  const query = useFreeSlots(date);

  const copyMessage = async () => {
    if (!query.data?.message) return;
    await navigator.clipboard.writeText(query.data.message);
    toast.success("Mensagem copiada! Já pode colar no WhatsApp.");
  };

  return (
    <div className="page">
      <header className="page__header">
        <h1 className="page__title">Modo Ocupado</h1>
        <p className="page__subtitle">
          Veja seus horários livres e responda rápido no WhatsApp, sem abrir a agenda completa.
        </p>
      </header>

      <div className="tab-group" role="tablist" aria-label="Dia">
        <button
          type="button"
          role="tab"
          aria-selected={day === "today"}
          className="tab-button tap-target"
          onClick={() => setDay("today")}
        >
          Hoje
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={day === "tomorrow"}
          className="tab-button tap-target"
          onClick={() => setDay("tomorrow")}
        >
          Amanhã
        </button>
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Calculando horários livres…</p>}
        empty={
          <EmptyState
            tone="filtered"
            title="Nenhum horário livre"
            body="A agenda deste dia já está totalmente ocupada dentro do seu horário de trabalho."
          />
        }
        isEmpty={(data) => data.slots.length === 0}
      >
        {(data) => (
          <div className={styles.container}>
            <div className={styles.slotList}>
              {data.slots.map((slot) => (
                <div key={slot} className={styles.slotItem}>
                  <span className={styles.slotTime}>{formatSlotLabel(slot)}</span>
                  <button
                    type="button"
                    className={`${styles.btnReserve} tap-target`}
                    onClick={() => setBookingSlot(`${date}T${slot}`)}
                  >
                    Reservar
                  </button>
                </div>
              ))}
            </div>

            <div className={styles.messageBox}>
              <p className={styles.messagePreview}>{data.message}</p>
              <button
                type="button"
                className={`${styles.btnCopy} tap-target`}
                onClick={copyMessage}
              >
                <IconWhatsApp width="16" height="16" />
                <span>Copiar mensagem para o WhatsApp</span>
              </button>
            </div>
          </div>
        )}
      </AsyncBoundary>

      {bookingSlot && (
        <NewBookingModal
          initialDateTime={bookingSlot}
          onClose={() => setBookingSlot(null)}
        />
      )}
    </div>
  );
}
