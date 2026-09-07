import { useEffect, useState } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import {
  publicBookingApi,
  type PublicBooking,
} from "./api";
import { anamnesisApi } from "@/features/anamnesis/api";
import styles from "./BookingManagementPage.module.css";

export function BookingManagementPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState<PublicBooking | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Estados de Remarcação
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [newDate, setNewDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split("T")[0];
  });
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [rescheduling, setRescheduling] = useState(false);
  const [rescheduleError, setRescheduleError] = useState<string | null>(null);

  // Estados de Cancelamento
  const [cancelling, setCancelling] = useState(false);
  const [copied, setCopied] = useState(false);
  const [anamnesisToken, setAnamnesisToken] = useState<string | null>(null);
  const [anamnesisSubmitted, setAnamnesisSubmitted] = useState(false);

  useEffect(() => {
    if (!id || !token) {
      setError("Link de agendamento incompleto ou inválido.");
      setLoading(false);
      return;
    }

    publicBookingApi
      .getBooking(id, token)
      .then((data) => setBooking(data))
      .catch((err) => setError(err.message || "Agendamento não encontrado."))
      .finally(() => setLoading(false));

    anamnesisApi
      .getByBooking(id, token)
      .then((res) => {
        setAnamnesisToken(res.public_token);
        setAnamnesisSubmitted(Boolean(res.submitted_at));
      })
      .catch(() => {
        // Ignora silenciosamente se o profissional não tiver anamnese
      });
  }, [id, token]);

  useEffect(() => {
    if (!isRescheduling || !booking?.professional_slug || !newDate) return;

    setLoadingSlots(true);
    setSelectedSlot(null);
    publicBookingApi
      .getSlots(booking.professional_slug, newDate)
      .then((slots) => {
        setAvailableSlots(slots);
        if (slots.length > 0) setSelectedSlot(slots[0]);
      })
      .catch(() => setAvailableSlots([]))
      .finally(() => setLoadingSlots(false));
  }, [isRescheduling, booking?.professional_slug, newDate]);

  const handleConfirmReschedule = async () => {
    if (!id || !token || !newDate || !selectedSlot) return;

    setRescheduling(true);
    setRescheduleError(null);

    try {
      const scheduledDateTime = `${newDate}T${selectedSlot}:00`;
      const updated = await publicBookingApi.rescheduleBooking(id, token, {
        scheduled_at: scheduledDateTime,
      });
      setBooking(updated);
      setIsRescheduling(false);
    } catch (err: unknown) {
      const error = err as Error;
      setRescheduleError(error.message || "Não foi possível remarcar para este horário.");
    } finally {
      setRescheduling(false);
    }
  };

  const handleCancelBooking = async () => {
    if (!id || !token) return;
    if (!window.confirm("Deseja realmente cancelar este agendamento? O horário será liberado na agenda.")) return;

    setCancelling(true);
    try {
      const updated = await publicBookingApi.cancelBooking(id, token);
      setBooking(updated);
    } catch (err: unknown) {
      const error = err as Error;
      alert(error.message || "Erro ao cancelar agendamento.");
    } finally {
      setCancelling(false);
    }
  };

  const copyShareLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const formatScheduledDateTime = (iso: string) => {
    try {
      const date = new Date(iso);
      return date.toLocaleString("pt-BR", {
        weekday: "long",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  if (loading) {
    return (
      <div className={styles.wrapper}>
        <div style={{ textAlign: "center", paddingTop: "100px" }}>
          <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>
            Localizando seu agendamento...
          </p>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className={styles.wrapper}>
        <div style={{ textAlign: "center", paddingTop: "100px", maxWidth: "480px" }}>
          <div className={styles.errorBanner}>
            {error || "Agendamento não encontrado."}
          </div>
        </div>
      </div>
    );
  }

  const isCancelled = booking.status === "CANCELLED";

  const getGoogleCalendarUrl = () => {
    const start = new Date(booking.scheduled_at);
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const formatGCal = (d: Date) => d.toISOString().replace(/-|:|\.\d\d\d/g, "");

    const title = encodeURIComponent(
      `Procedimento: ${booking.procedure_name || "Estética"} com ${booking.professional_name}`
    );
    const details = encodeURIComponent(
      `Agendamento confirmado no Lumina Estética Manager.\nPaciente: ${booking.patient_name}`
    );

    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${formatGCal(
      start
    )}/${formatGCal(end)}&details=${details}`;
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        {/* Cartão Estilo Voucher de Confirmação */}
        <div className={styles.voucherCard}>
          <div
            className={`${styles.voucherHeader} ${
              isCancelled ? styles.voucherHeaderCancelled : ""
            }`}
          >
            <div className={styles.statusIcon}>
              {isCancelled ? "✕" : "✓"}
            </div>
            <h1 className={styles.voucherTitle}>
              {isCancelled ? "Agendamento Cancelado" : "Horário Confirmado com Sucesso!"}
            </h1>
            <p className={styles.voucherSubtitle}>
              {isCancelled
                ? "Este horário foi liberado. Caso queira, você pode realizar um novo agendamento a qualquer momento."
                : `Olá, ${booking.patient_name}! Seu horário foi reservado exclusivamente com ${booking.professional_name}.`}
            </p>
          </div>

          <div className={styles.voucherBody}>
            {/* Grade de Detalhes em 2 Colunas */}
            <div className={styles.detailGrid}>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Procedimento</span>
                <span className={styles.detailValue}>
                  {booking.procedure_name || "Procedimento Estético"}
                </span>
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Profissional Responsável</span>
                <span className={styles.detailValue}>
                  {booking.professional_name}
                </span>
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Data e Horário</span>
                <span className={styles.detailValue} style={{ color: "var(--accent)" }}>
                  {formatScheduledDateTime(booking.scheduled_at)}
                </span>
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Paciente</span>
                <span className={styles.detailValue}>
                  {booking.patient_name}
                </span>
              </div>

              {booking.procedure_price && (
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Valor Previsto</span>
                  <span className={styles.detailValue} style={{ color: "var(--accent)" }}>
                    R$ {parseFloat(booking.procedure_price).toFixed(2).replace(".", ",")}
                  </span>
                </div>
              )}

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Status da Reserva</span>
                <span className={styles.detailValue}>
                  {isCancelled ? "Cancelado" : "Confirmado"}
                </span>
              </div>
            </div>

            {/* Caixa de Remarcação */}
            {isRescheduling && !isCancelled && (
              <div className={styles.rescheduleCard}>
                <h3 style={{ margin: 0, fontSize: "1.1rem", color: "var(--text-h)" }}>
                  🔄 Escolha a Nova Data e Horário
                </h3>

                <input
                  type="date"
                  style={{
                    padding: "12px 14px",
                    borderRadius: "10px",
                    border: "1.5px solid var(--border)",
                    fontSize: "1rem",
                  }}
                  value={newDate}
                  min={new Date().toISOString().split("T")[0]}
                  onChange={(e) => setNewDate(e.target.value)}
                />

                {loadingSlots ? (
                  <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                    Verificando novos horários vagos...
                  </p>
                ) : availableSlots.length === 0 ? (
                  <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                    Nenhum horário livre neste dia. Escolha outra data no campo acima.
                  </p>
                ) : (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fill, minmax(84px, 1fr))",
                      gap: "8px",
                    }}
                  >
                    {availableSlots.map((slot) => (
                      <button
                        type="button"
                        key={slot}
                        onClick={() => setSelectedSlot(slot)}
                        style={{
                          padding: "10px",
                          borderRadius: "8px",
                          border: "1.5px solid",
                          borderColor: selectedSlot === slot ? "var(--accent)" : "var(--border)",
                          background: selectedSlot === slot ? "var(--accent)" : "var(--bg-card)",
                          color: selectedSlot === slot ? "#ffffff" : "var(--text-h)",
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        {slot}
                      </button>
                    ))}
                  </div>
                )}

                {rescheduleError && <div className={styles.errorBanner}>{rescheduleError}</div>}

                <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
                  <button
                    type="button"
                    className={styles.primaryBtn}
                    style={{ flex: 1 }}
                    onClick={handleConfirmReschedule}
                    disabled={rescheduling || !selectedSlot}
                  >
                    {rescheduling ? "Salvando..." : "Confirmar Novo Horário"}
                  </button>
                  <button
                    type="button"
                    className={styles.secondaryBtn}
                    onClick={() => setIsRescheduling(false)}
                  >
                    Voltar
                  </button>
                </div>
              </div>
            )}

            {/* Card de Ficha de Anamnese */}
            {!isCancelled && !isRescheduling && anamnesisToken && (
              <div
                style={{
                  background: anamnesisSubmitted ? "#f8fafc" : "#f0fdf4",
                  border: `1px solid ${anamnesisSubmitted ? "#e2e8f0" : "#bbf7d0"}`,
                  borderRadius: "16px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  textAlign: "center",
                  gap: "10px",
                  marginBottom: "20px",
                }}
              >
                <div style={{ fontSize: "1.75rem" }}>{anamnesisSubmitted ? "✓" : "📋"}</div>
                <h3
                  style={{
                    margin: 0,
                    fontSize: "1.1rem",
                    fontWeight: 700,
                    color: anamnesisSubmitted ? "#334155" : "#166534",
                  }}
                >
                  {anamnesisSubmitted
                    ? "Ficha de Anamnese Preenchida com Sucesso!"
                    : "Agilize seu Atendimento: Ficha de Saúde"}
                </h3>
                <p
                  style={{
                    margin: 0,
                    fontSize: "0.88rem",
                    color: "#475569",
                    maxWidth: "480px",
                  }}
                >
                  {anamnesisSubmitted
                    ? "Suas respostas já foram anexadas com segurança ao seu prontuário."
                    : "Para sua segurança e melhor resultado, preencha sua ficha rápida de saúde (leva menos de 2 minutos)."}
                </p>
                <Link
                  to={`/anamnese/${anamnesisToken}`}
                  className={styles.primaryBtn}
                  style={{
                    textDecoration: "none",
                    width: "auto",
                    padding: "10px 22px",
                    fontSize: "0.95rem",
                    background: anamnesisSubmitted ? "#475569" : "var(--accent)",
                  }}
                >
                  {anamnesisSubmitted ? "Rever Minhas Respostas" : "Preencher Ficha de Anamnese Agora"}
                </Link>
              </div>
            )}

            {/* Ações */}
            {!isCancelled && !isRescheduling && (
              <div className={styles.actionGrid}>
                <a
                  href={getGoogleCalendarUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.primaryBtn}
                >
                  📅 Adicionar ao Meu Google Agenda
                </a>

                <button type="button" className={styles.secondaryBtn} onClick={copyShareLink}>
                  {copied ? "✓ Link Copiado com Sucesso!" : "🔗 Salvar Link Deste Agendamento (WhatsApp)"}
                </button>

                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={() => setIsRescheduling(true)}
                >
                  🔄 Preciso Remarcar Meu Horário
                </button>

                <button
                  type="button"
                  className={styles.dangerBtn}
                  onClick={handleCancelBooking}
                  disabled={cancelling}
                >
                  {cancelling ? "Cancelando..." : "Cancelar Agendamento"}
                </button>
              </div>
            )}

            {isCancelled && booking.professional_slug && (
              <Link
                to={`/agendar/${booking.professional_slug}`}
                className={styles.primaryBtn}
              >
                Fazer um Novo Agendamento
              </Link>
            )}
          </div>
        </div>

        <div className={styles.infoBox}>
          <span style={{ fontSize: "1.25rem" }}>💡</span>
          <div>
            <strong>Dica Importante:</strong> Guarde este link com você! Por meio dele você pode acompanhar, remarcar ou cancelar seu horário a qualquer momento sem precisar de senha ou aplicativo.
          </div>
        </div>
      </div>
    </div>
  );
}
