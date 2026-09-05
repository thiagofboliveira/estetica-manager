import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  publicBookingApi,
  type PublicProfessionalInfo,
  type PublicProcedure,
} from "./api";
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
    // Default para o dia seguinte para evitar horários expirados
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
      // Monta data/hora combinada no formato ISO com UTC
      const scheduledDateTime = `${selectedDate}T${selectedSlot}:00Z`;

      const booking = await publicBookingApi.createBooking(slug, {
        procedure_id: selectedProcedure.id,
        scheduled_at: scheduledDateTime,
        patient_name: patientName.trim(),
        patient_phone: cleanPhone,
        note: note.trim() || null,
      });

      // Redireciona para a página de confirmação e gestão com o token privado
      navigate(`/agendamento/${booking.id}?token=${encodeURIComponent(booking.management_token)}`);
    } catch (err: unknown) {
      const error = err as Error;
      setSubmitError(error.message || "Não foi possível confirmar o agendamento. Tente novamente.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingProfile) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container} style={{ textAlign: "center", paddingTop: "80px" }}>
          <p style={{ color: "var(--text-muted)" }}>Carregando agenda...</p>
        </div>
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container} style={{ textAlign: "center", paddingTop: "80px" }}>
          <div className={styles.errorBanner}>
            {profileError || "Esta agenda não está disponível no momento."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <form className={styles.container} onSubmit={handleSubmit}>
        {/* Cabeçalho de Perfil */}
        <div className={styles.profileCard}>
          <div className={styles.avatar}>
            {profile.name.charAt(0).toUpperCase()}
          </div>
          <h1 className={styles.profName}>{profile.name}</h1>
          <div className={styles.badge}>Agenda Online Oficial</div>
          {profile.bio && <p className={styles.bio}>{profile.bio}</p>}
        </div>

        {/* 1. Seleção de Procedimento */}
        <div className={styles.sectionCard}>
          <h2 className={styles.sectionTitle}>
            <span className={styles.stepNumber}>1</span>
            Escolha o Procedimento
          </h2>

          <div className={styles.procedureList}>
            {profile.procedures.map((proc) => {
              const isSelected = selectedProcedure?.id === proc.id;
              return (
                <div
                  key={proc.id}
                  className={`${styles.procedureCard} ${
                    isSelected ? styles.procedureCardSelected : ""
                  }`}
                  onClick={() => setSelectedProcedure(proc)}
                >
                  <div className={styles.procInfo}>
                    <span className={styles.procName}>{proc.name}</span>
                    <span className={styles.procMeta}>
                      {proc.session_plan === "SINGLE" ? "Sessão individual" : "Plano de sessões"}
                    </span>
                  </div>
                  <div className={styles.procPrice}>
                    R$ {parseFloat(proc.price).toFixed(2).replace(".", ",")}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 2. Seleção de Data */}
        <div className={styles.sectionCard}>
          <h2 className={styles.sectionTitle}>
            <span className={styles.stepNumber}>2</span>
            Escolha o Dia
          </h2>

          <input
            type="date"
            className={styles.dateInput}
            value={selectedDate}
            min={new Date().toISOString().split("T")[0]}
            onChange={(e) => setSelectedDate(e.target.value)}
            required
          />
        </div>

        {/* 3. Seleção de Horário */}
        <div className={styles.sectionCard}>
          <h2 className={styles.sectionTitle}>
            <span className={styles.stepNumber}>3</span>
            Escolha o Horário
          </h2>

          {loadingSlots ? (
            <p style={{ color: "var(--text-muted)", textAlign: "center", margin: "10px 0" }}>
              Buscando horários disponíveis...
            </p>
          ) : slots.length === 0 ? (
            <div className={styles.emptySlots}>
              Nenhum horário livre encontrado para este dia. Por favor escolha outra data.
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

        {/* 4. Dados da Paciente */}
        <div className={styles.sectionCard}>
          <h2 className={styles.sectionTitle}>
            <span className={styles.stepNumber}>4</span>
            Seus Dados
          </h2>

          <div className={styles.formGroup}>
            <label className={styles.label}>Seu Nome Completo *</label>
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

          <div className={styles.formGroup}>
            <label className={styles.label}>Observações ou dúvidas (opcional)</label>
            <textarea
              className={styles.input}
              rows={2}
              placeholder="Alguma alergia ou detalhe importante?"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
        </div>

        {submitError && <div className={styles.errorBanner}>{submitError}</div>}

        <button
          type="submit"
          className={styles.submitBtn}
          disabled={submitting || !selectedSlot}
        >
          {submitting ? "Confirmando agendamento..." : "Confirmar Agendamento"}
        </button>

        <div className={styles.footer}>
          Lumina Estética • Agendamento Seguro e Sem Senha
        </div>
      </form>
    </div>
  );
}
