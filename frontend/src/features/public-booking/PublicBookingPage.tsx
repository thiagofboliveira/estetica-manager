import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  publicBookingApi,
  type PublicProfessionalInfo,
  type PublicProcedure,
} from "./api";
import { getProcedurePhoto } from "./procedureImages";
import styles from "./PublicBookingPage.module.css";

export function PublicBookingPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [profile, setProfile] = useState<PublicProfessionalInfo | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [selectedProcedure, setSelectedProcedure] = useState<PublicProcedure | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    const today = new Date();
    today.setDate(today.getDate() + 1);
    return today.toISOString().split("T")[0];
  });

  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slots, setSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);

  const [patientName, setPatientName] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [note, setNote] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Carrega informações públicas da profissional
  useEffect(() => {
    if (!slug) return;
    setLoadingProfile(true);
    publicBookingApi
      .getAgendaInfo(slug)
      .then((data) => {
        setProfile(data);
        if (data.procedures.length > 0) {
          setSelectedProcedure(data.procedures[0]);
        }
      })
      .catch((err) => {
        setProfileError(err.message || "Agenda não encontrada.");
      })
      .finally(() => setLoadingProfile(false));
  }, [slug]);

  // Carrega horários disponíveis para a data selecionada
  useEffect(() => {
    if (!slug || !selectedDate) return;
    setLoadingSlots(true);
    setSelectedSlot(null);
    publicBookingApi
      .getSlots(slug, selectedDate)
      .then((data) => {
        setSlots(data);
        if (data.length > 0) {
          setSelectedSlot(data[0]);
        }
      })
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false));
  }, [slug, selectedDate]);

  // Gera os próximos 6 dias para seleção rápida
  const quickDays = useMemo(() => {
    const days = [];
    const base = new Date();
    for (let i = 1; i <= 6; i++) {
      const d = new Date();
      d.setDate(base.getDate() + i);
      const iso = d.toISOString().split("T")[0];
      const weekday = d.toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "");
      const dayNum = d.toLocaleDateString("pt-BR", { day: "2-digit" });
      const monthNum = d.toLocaleDateString("pt-BR", { month: "short" }).replace(".", "");
      days.push({ iso, weekday, dayNum, monthNum });
    }
    return days;
  }, []);

  const formatPhone = (val: string) => {
    const cleaned = val.replace(/\D/g, "").slice(0, 11);
    if (cleaned.length <= 2) return cleaned;
    if (cleaned.length <= 7) return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2)}`;
    return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPatientPhone(formatPhone(e.target.value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slug || !selectedProcedure || !selectedDate || !selectedSlot) {
      setSubmitError("Por favor, selecione um procedimento, data e horário.");
      return;
    }

    if (!patientName.trim()) {
      setSubmitError("Informe seu nome completo.");
      return;
    }

    const cleanPhone = patientPhone.replace(/\D/g, "");
    if (cleanPhone.length < 10) {
      setSubmitError("Informe um número de WhatsApp válido com DDD.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const scheduledDateTime = `${selectedDate}T${selectedSlot}:00Z`;

      const booking = await publicBookingApi.createBooking(slug, {
        procedure_id: selectedProcedure.id,
        scheduled_at: scheduledDateTime,
        patient_name: patientName.trim(),
        patient_phone: cleanPhone,
        note: note.trim() || null,
      });

      navigate(`/agendamento/${booking.id}?token=${encodeURIComponent(booking.management_token)}`);
    } catch (err: unknown) {
      const error = err as Error;
      setSubmitError(error.message || "Não foi possível confirmar o agendamento. Tente novamente.");
    } finally {
      setSubmitting(false);
    }
  };

  const formattedSelectedDate = useMemo(() => {
    if (!selectedDate) return "";
    try {
      const [year, month, day] = selectedDate.split("-");
      const d = new Date(Number(year), Number(month) - 1, Number(day));
      return d.toLocaleDateString("pt-BR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
      });
    } catch {
      return selectedDate;
    }
  }, [selectedDate]);

  if (loadingProfile) {
    return (
      <div className={styles.wrapper}>
        <div style={{ textAlign: "center", paddingTop: "100px" }}>
          <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>
            Carregando agenda profissional...
          </p>
        </div>
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <div className={styles.wrapper}>
        <div style={{ textAlign: "center", paddingTop: "100px", maxWidth: "480px" }}>
          <div className={styles.errorBanner}>
            {profileError || "Esta agenda não está disponível no momento."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.mainContainer}>
        <form className={styles.layoutGrid} onSubmit={handleSubmit}>
          {/* COLUNA ESQUERDA: Perfil e Resumo em Tempo Real */}
          <aside className={styles.sidebarCol}>
            <div className={styles.profileCard}>
              <div className={styles.profileCover} />
              <div className={styles.profileContent}>
                <div className={styles.avatar}>
                  {profile.name.charAt(0).toUpperCase()}
                </div>
                <h1 className={styles.profName}>{profile.name}</h1>
                <div className={styles.verifiedBadge}>
                  ✓ Agenda Verificada Lumina
                </div>
                {profile.bio && <p className={styles.bio}>{profile.bio}</p>}
              </div>
            </div>

            {/* Resumo do Agendamento */}
            <div className={styles.summaryCard}>
              <h3 className={styles.summaryTitle}>
                📋 Resumo da Reserva
              </h3>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Procedimento</span>
                <span className={styles.summaryValue}>
                  {selectedProcedure?.name || "Nenhum selecionado"}
                </span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Data e Horário</span>
                <span className={styles.summaryValue}>
                  {selectedSlot
                    ? `${formattedSelectedDate} às ${selectedSlot}`
                    : "Escolha uma data e horário"}
                </span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Investimento</span>
                <span className={styles.summaryPrice}>
                  {selectedProcedure
                    ? `R$ ${parseFloat(selectedProcedure.price).toFixed(2).replace(".", ",")}`
                    : "R$ --"}
                </span>
              </div>
            </div>
          </aside>

          {/* COLUNA DIREITA: Fluxo de Agendamento Harmonizado */}
          <main className={styles.contentCol}>
            {/* 1. Seleção de Procedimento com Fotos */}
            <section className={styles.sectionCard}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.stepBadge}>1</span>
                  Selecione o Procedimento
                </h2>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  {profile.procedures.length} procedimentos disponíveis
                </span>
              </div>

              <div className={styles.procedureGrid}>
                {profile.procedures.map((proc) => {
                  const isSelected = selectedProcedure?.id === proc.id;
                  const photoUrl = getProcedurePhoto(proc.name);

                  return (
                    <div
                      key={proc.id}
                      className={`${styles.procedureCard} ${
                        isSelected ? styles.procedureCardSelected : ""
                      }`}
                      onClick={() => setSelectedProcedure(proc)}
                    >
                      <div className={styles.procImageWrapper}>
                        <img
                          src={photoUrl}
                          alt={proc.name}
                          className={styles.procImage}
                          loading="lazy"
                        />
                        <span className={styles.planTag}>
                          {proc.session_plan === "SINGLE" ? "Sessão Única" : "Plano de Sessões"}
                        </span>
                      </div>

                      <div className={styles.procBody}>
                        <h3 className={styles.procName}>{proc.name}</h3>

                        <div className={styles.procFooter}>
                          <span className={styles.procPrice}>
                            R$ {parseFloat(proc.price).toFixed(2).replace(".", ",")}
                          </span>
                          <span className={styles.selectIndicator}>
                            {isSelected ? "● Selecionado" : "Selecionar"}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* 2. Seleção de Data e Horário */}
            <section className={styles.sectionCard}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.stepBadge}>2</span>
                  Data e Horário
                </h2>
                {formattedSelectedDate && (
                  <span style={{ fontSize: "0.9rem", color: "var(--accent)", fontWeight: 600 }}>
                    {formattedSelectedDate}
                  </span>
                )}
              </div>

              <div className={styles.dateContainer}>
                {/* Abas Rápidas de Dias */}
                <div className={styles.dateQuickPick}>
                  {quickDays.map((d) => {
                    const isSelected = selectedDate === d.iso;
                    return (
                      <button
                        type="button"
                        key={d.iso}
                        className={`${styles.quickDayBtn} ${
                          isSelected ? styles.quickDayBtnSelected : ""
                        }`}
                        onClick={() => setSelectedDate(d.iso)}
                      >
                        <span className={styles.quickDayName}>{d.weekday}</span>
                        <span className={styles.quickDayNumber}>{d.dayNum}</span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          {d.monthNum}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {/* Selecionar Outra Data */}
                <div className={styles.dateInputGroup}>
                  <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    Ou escolha no calendário:
                  </span>
                  <input
                    type="date"
                    className={styles.dateInput}
                    value={selectedDate}
                    min={new Date().toISOString().split("T")[0]}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Grade de Horários Livres */}
              <div className={styles.slotsSection}>
                <span className={styles.periodLabel}>Horários Livres Disponíveis</span>

                {loadingSlots ? (
                  <p style={{ color: "var(--text-muted)", padding: "16px 0", margin: 0 }}>
                    Verificando disponibilidade em tempo real...
                  </p>
                ) : slots.length === 0 ? (
                  <div className={styles.emptyNotice}>
                    Não encontramos horários livres para esta data. Por favor selecione outro dia.
                  </div>
                ) : (
                  <div className={styles.slotsGrid}>
                    {slots.map((slot) => {
                      const isSelected = selectedSlot === slot;
                      return (
                        <button
                          type="button"
                          key={slot}
                          className={`${styles.slotBtn} ${
                            isSelected ? styles.slotBtnSelected : ""
                          }`}
                          onClick={() => setSelectedSlot(slot)}
                        >
                          {slot}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </section>

            {/* 3. Dados da Paciente */}
            <section className={styles.sectionCard}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.stepBadge}>3</span>
                  Seus Dados para Contato
                </h2>
              </div>

              <div className={styles.formGrid}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>Nome Completo *</label>
                  <input
                    type="text"
                    className={styles.input}
                    placeholder="Ex: Mariana Ferreira"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    required
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>WhatsApp / Celular *</label>
                  <input
                    type="tel"
                    className={styles.input}
                    placeholder="(11) 99999-9999"
                    value={patientPhone}
                    onChange={handlePhoneChange}
                    required
                  />
                </div>

                <div className={`${styles.formGroup} ${styles.fullWidth}`}>
                  <label className={styles.label}>Alguma observação ou dúvida? (Opcional)</label>
                  <textarea
                    className={styles.input}
                    rows={2}
                    placeholder="Conte-nos se você tem alguma alergia ou é a sua primeira vez no procedimento..."
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                </div>
              </div>
            </section>

            {submitError && <div className={styles.errorBanner}>{submitError}</div>}

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={submitting || !selectedSlot}
            >
              {submitting ? "Reservando horário..." : "✓ Confirmar Agendamento Agora"}
            </button>

            <div className={styles.footer}>
              Lumina Estética • Agendamento Seguro e Sem Fricção
            </div>
          </main>
        </form>
      </div>
    </div>
  );
}
