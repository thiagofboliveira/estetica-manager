import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  publicBookingApi,
  type PublicProfessionalInfo,
  type PublicProcedure,
} from "./api";
import { getProcedurePhoto } from "./procedureImages";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./PublicBookingPage.module.css";

type Step = 1 | 2 | 3;

export function PublicBookingPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>(1);

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
  // A-02: opt-in explícito de contato por WhatsApp — sem isso o
  // paciente vira lead que opportunity_rules.py se recusa a contatar.
  const [consentWhatsapp, setConsentWhatsapp] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Busca, Dropdown e Paginação de Procedimentos
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 6;

  // Carrega informações públicas da profissional
  useEffect(() => {
    if (!slug) return;
    setLoadingProfile(true);
    publicBookingApi
      .getAgendaInfo(slug)
      .then((data) => {
        setProfile(data);
      })
      .catch((err) => {
        setProfileError(err.message || "Agenda não encontrada.");
      })
      .finally(() => setLoadingProfile(false));
  }, [slug]);

  // Lista filtrada por busca
  const filteredProcedures = useMemo(() => {
    if (!profile) return [];
    const term = searchTerm.trim().toLowerCase();
    if (!term) return profile.procedures;
    return profile.procedures.filter((p) =>
      p.name.toLowerCase().includes(term)
    );
  }, [profile, searchTerm]);

  // Total de páginas
  const totalPages = Math.max(1, Math.ceil(filteredProcedures.length / ITEMS_PER_PAGE));

  // Itens da página atual
  const paginatedProcedures = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredProcedures.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredProcedures, currentPage]);

  // Ao alterar a busca, reinicia para página 1
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  const handleDropdownSelect = (procId: string) => {
    if (!procId) return;
    const found = profile?.procedures.find((p) => p.id === procId);
    if (found) {
      setSelectedProcedure(found);
      const index = filteredProcedures.findIndex((p) => p.id === procId);
      if (index !== -1) {
        setCurrentPage(Math.floor(index / ITEMS_PER_PAGE) + 1);
      }
    }
  };

  // Carrega horários disponíveis ao entrar na etapa 2 ou mudar data
  useEffect(() => {
    if (!slug || !selectedDate || step !== 2) return;
    setLoadingSlots(true);
    setSelectedSlot(null);
    publicBookingApi
      .getSlots(slug, selectedDate)
      .then((data) => {
        setSlots(data);
        if (data.length > 0) setSelectedSlot(data[0]);
      })
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, selectedDate, step]);

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
      const scheduledDateTime = `${selectedDate}T${selectedSlot}:00`;

      const booking = await publicBookingApi.createBooking(slug, {
        procedure_id: selectedProcedure.id,
        scheduled_at: scheduledDateTime,
        patient_name: patientName.trim(),
        patient_phone: cleanPhone,
        note: note.trim() || null,
        patient_consent_whatsapp: consentWhatsapp,
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

  const goToStep = (target: Step) => {
    if (target === 2 && !selectedProcedure) return;
    if (target === 3 && (!selectedProcedure || !selectedSlot)) return;
    setStep(target);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

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

  const stepLabels = ["Procedimento", "Data e Hora", "Seus Dados"];

  return (
    <div className={styles.wrapper}>
      <div className={styles.mainContainer}>
        <div className={styles.layoutGrid}>
          {/* COLUNA ESQUERDA: Perfil e Resumo em Tempo Real */}
          <aside className={styles.sidebarCol}>
            <div className={styles.profileCard}>
              <div className={styles.profileCover} />
              <div className={styles.profileContent}>
                <div className={styles.avatar}>
                  {profile.avatar_url ? (
                    <img
                      src={profile.avatar_url}
                      alt={profile.name}
                      className={styles.avatarImg}
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = "none";
                      }}
                    />
                  ) : null}
                  {!profile.avatar_url && profile.name.charAt(0).toUpperCase()}
                </div>
                <h1 className={styles.profName}>{profile.name}</h1>
                <div className={styles.specialtyBadge}>
                  {profile.specialty || "Especialista em Estética Avançada"}
                </div>
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
                    ? formatBRL(money(selectedProcedure.price))
                    : "R$ --"}
                </span>
              </div>
            </div>
          </aside>

          {/* COLUNA DIREITA: Wizard de 3 Etapas */}
          <main className={styles.contentCol}>
            {/* Barra de Progresso */}
            <div className={styles.stepperBar}>
              <div className={styles.stepperTrack}>
                <div
                  className={styles.stepperProgress}
                  style={{ width: `${((step - 1) / 2) * 100}%` }}
                />
              </div>
              {([1, 2, 3] as Step[]).map((num) => {
                const isActive = step === num;
                const isDone = step > num;
                return (
                  <button
                    key={num}
                    type="button"
                    className={`${styles.stepperItem} ${
                      isActive
                        ? styles.stepperActive
                        : isDone
                        ? styles.stepperDone
                        : styles.stepperPending
                    }`}
                    onClick={() => { if (isDone) goToStep(num); }}
                    disabled={!isDone && !isActive}
                  >
                    <span className={styles.stepperCircle}>
                      {isDone ? "✓" : num}
                    </span>
                    <span className={styles.stepperLabel}>{stepLabels[num - 1]}</span>
                  </button>
                );
              })}
            </div>

            {/* ── ETAPA 1: Selecionar Procedimento ── */}
            {step === 1 && (
              <section className={styles.sectionCard}>
                <div className={styles.sectionHeader}>
                  <h2 className={styles.sectionTitle}>
                    <span className={styles.stepBadge}>1</span>
                    Selecione o Procedimento
                  </h2>
                  <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    {filteredProcedures.length}{" "}
                    {filteredProcedures.length === 1 ? "serviço" : "serviços"} disponíveis
                  </span>
                </div>

                {/* Barra de Busca e Dropdown */}
                <div className={styles.procedureFilterBar}>
                  <div className={styles.searchBox}>
                    <span className={styles.searchIcon}>🔍</span>
                    <input
                      type="text"
                      className={styles.searchInput}
                      placeholder="Pesquisar por nome do procedimento..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    {searchTerm && (
                      <button
                        type="button"
                        onClick={() => setSearchTerm("")}
                        style={{
                          position: "absolute",
                          right: "10px",
                          top: "50%",
                          transform: "translateY(-50%)",
                          background: "none",
                          border: "none",
                          color: "var(--text-muted)",
                          cursor: "pointer",
                          fontSize: "0.85rem",
                        }}
                        title="Limpar pesquisa"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  <select
                    className={styles.filterSelect}
                    value={selectedProcedure?.id || ""}
                    onChange={(e) => handleDropdownSelect(e.target.value)}
                    aria-label="Selecionar procedimento pelo menu"
                  >
                    <option value="">-- Ou escolha na lista suspensa --</option>
                    {profile.procedures.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({formatBRL(money(p.price))})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Grid de Procedimentos Paginados */}
                {paginatedProcedures.length > 0 ? (
                  <div className={styles.procedureGrid}>
                    {paginatedProcedures.map((proc) => {
                      const isSelected = selectedProcedure?.id === proc.id;
                      const photoUrl = proc.image_url || getProcedurePhoto(proc.name);

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
                                {formatBRL(money(proc.price))}
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
                ) : (
                  <div className={styles.emptySearch}>
                    <p>Nenhum procedimento encontrado para "<strong>{searchTerm}</strong>".</p>
                    <button
                      type="button"
                      className={styles.clearSearchBtn}
                      onClick={() => setSearchTerm("")}
                    >
                      Limpar pesquisa
                    </button>
                  </div>
                )}

                {/* Paginação */}
                {totalPages > 1 && (
                  <div className={styles.paginationRow}>
                    <span className={styles.paginationInfo}>
                      Página {currentPage} de {totalPages} ({filteredProcedures.length} procedimentos)
                    </span>
                    <div className={styles.paginationControls}>
                      <button
                        type="button"
                        className={styles.pageBtn}
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        ← Anterior
                      </button>
                      {Array.from({ length: totalPages }).map((_, idx) => {
                        const pageNum = idx + 1;
                        return (
                          <button
                            key={pageNum}
                            type="button"
                            className={`${styles.pageNumber} ${
                              pageNum === currentPage ? styles.pageNumberActive : ""
                            }`}
                            onClick={() => setCurrentPage(pageNum)}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      <button
                        type="button"
                        className={styles.pageBtn}
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Próxima →
                      </button>
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  className={styles.nextBtn}
                  disabled={!selectedProcedure}
                  onClick={() => goToStep(2)}
                >
                  Continuar → Escolher Data e Horário
                </button>
              </section>
            )}

            {/* ── ETAPA 2: Data e Horário ── */}
            {step === 2 && (
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
                    />
                  </div>
                </div>

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
                      {slots.map((slot) => (
                        <button
                          type="button"
                          key={slot}
                          className={`${styles.slotBtn} ${
                            selectedSlot === slot ? styles.slotBtnSelected : ""
                          }`}
                          onClick={() => setSelectedSlot(slot)}
                        >
                          {slot}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className={styles.stepNavRow}>
                  <button type="button" className={styles.backBtn} onClick={() => goToStep(1)}>
                    ← Voltar
                  </button>
                  <button
                    type="button"
                    className={styles.nextBtn}
                    disabled={!selectedSlot}
                    onClick={() => goToStep(3)}
                  >
                    Continuar → Meus Dados
                  </button>
                </div>
              </section>
            )}

            {/* ── ETAPA 3: Dados da Paciente ── */}
            {step === 3 && (
              <form className={styles.sectionCard} onSubmit={handleSubmit}>
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

                <label className={styles.consentRow}>
                  <input
                    type="checkbox"
                    checked={consentWhatsapp}
                    onChange={(e) => setConsentWhatsapp(e.target.checked)}
                  />
                  <span>
                    Aceito receber lembretes e confirmações deste agendamento pelo
                    WhatsApp. Veja como tratamos seus dados na nossa{" "}
                    <Link to="/privacidade" target="_blank" rel="noopener noreferrer">
                      Política de Privacidade
                    </Link>
                    .
                  </span>
                </label>

                {submitError && <div className={styles.errorBanner}>{submitError}</div>}

                <div className={styles.stepNavRow}>
                  <button type="button" className={styles.backBtn} onClick={() => goToStep(2)}>
                    ← Voltar
                  </button>
                  <button type="submit" className={styles.submitBtn} disabled={submitting}>
                    {submitting ? "Reservando horário..." : "✓ Confirmar Agendamento Agora"}
                  </button>
                </div>

                <div className={styles.footer}>
                  Lumina Estética • Agendamento Seguro e Sem Fricção
                </div>
              </form>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
