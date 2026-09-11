import { useState } from "react";
import { Link } from "react-router-dom";
import { usePatients } from "@/features/patients/hooks";
import { useProcedures } from "@/features/procedures/hooks";
import { useFinancialSettings, useUpdateFinancialSettings } from "@/features/settings/hooks";
import { useCampaignTemplates } from "@/features/whatsapp-campaigns/useCampaignTemplates";
import { toast } from "@/ui/ToastContext";
import {
  IconCheck,
  IconArrowRight,
  IconSparkles,
  IconTarget,
} from "@/ui/icons";
import styles from "./OnboardingChecklist.module.css";

type Props = {
  hasAnySale: boolean;
};

export function OnboardingChecklist({ hasAnySale }: Props) {
  const [dismissed, setDismissed] = useState(() => {
    return localStorage.getItem("estetica_onboarding_dismissed") === "true";
  });
  const [isMinimized, setIsMinimized] = useState(false);

  // Gamificação: Modal rápido para definição de meta
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [goalInputValue, setGoalInputValue] = useState("");
  const updateSettingsMutation = useUpdateFinancialSettings();

  const proceduresQuery = useProcedures();
  const patientsQuery = usePatients();
  const settingsQuery = useFinancialSettings();
  const templatesQuery = useCampaignTemplates();

  if (dismissed) {
    return null;
  }

  const isLoadingAny =
    proceduresQuery.isLoading ||
    patientsQuery.isLoading ||
    settingsQuery.isLoading ||
    templatesQuery.isLoading;

  if (isLoadingAny) {
    return null;
  }

  const hasProcedures = Boolean(proceduresQuery.data && proceduresQuery.data.length > 0);
  const hasPatients = Boolean(patientsQuery.data && patientsQuery.data.length > 0);
  const hasSettings = Boolean(settingsQuery.data);
  const hasGoal = Boolean(
    settingsQuery.data?.monthly_revenue_goal &&
      Number(settingsQuery.data.monthly_revenue_goal) > 0
  );
  const hasCustomOrExploredCampaigns = Boolean(
    (templatesQuery.data && templatesQuery.data.length > 0) ||
      localStorage.getItem("estetica_campaigns_viewed") === "true"
  );

  const steps = [
    {
      id: "procedures",
      label: "Cadastrar Procedimentos",
      desc: "Defina seus serviços e valores cobrados",
      done: hasProcedures,
      link: "/procedimentos/novo",
      actionText: "Cadastrar",
    },
    {
      id: "patients",
      label: "Cadastrar Pacientes",
      desc: "Cadastre ou importe sua lista de clientes",
      done: hasPatients,
      link: "/pacientes/novo",
      actionText: "Adicionar",
    },
    {
      id: "settings",
      label: "Ajustar Taxas & Despesas",
      desc: "Custos fixos para cálculo automático do ponto de equilíbrio",
      done: hasSettings,
      link: "/financeiro",
      actionText: "Configurar",
    },
    {
      id: "sales",
      label: "Primeiro Atendimento ou Venda",
      desc: "Registre uma venda para ver o lucro real no bolso",
      done: hasAnySale,
      link: "/vendas/nova",
      actionText: "Registrar",
    },
    {
      id: "campaigns",
      label: "Campanhas de WhatsApp",
      desc: "Conheça os modelos de disparo para aniversariantes e retorno",
      done: hasCustomOrExploredCampaigns,
      link: "/disparos-whatsapp",
      actionText: "Ver Modelos",
    },
    {
      id: "goals",
      label: "Definir Meta de Faturamento",
      desc: "Acompanhe o termômetro de conquista da sua clínica",
      done: hasGoal,
      link: "/financeiro",
      actionText: "Definir",
    },
  ];

  const completedCount = steps.filter((s) => s.done).length;
  const progressPct = Math.round((completedCount / steps.length) * 100);
  const allDone = completedCount === steps.length;

  function handleDismiss() {
    localStorage.setItem("estetica_onboarding_dismissed", "true");
    setDismissed(true);
  }

  function handleOpenGoalModal() {
    const currentGoal = settingsQuery.data?.monthly_revenue_goal;
    setGoalInputValue(currentGoal ? String(Number(currentGoal)) : "15000.00");
    setShowGoalModal(true);
  }

  async function handleSaveGoalModal(valueToSave?: string) {
    const val = valueToSave ?? goalInputValue;
    const clean = val.trim() ? val.replace(/[^\d.,]/g, "").replace(",", ".") : null;
    if (!clean || Number(clean) <= 0) {
      toast.error("Informe um valor de meta válido maior que zero.");
      return;
    }
    try {
      await updateSettingsMutation.mutateAsync({
        monthly_revenue_goal: clean,
      });
      toast.success("Meta financeira configurada com sucesso!");
      setShowGoalModal(false);
      settingsQuery.refetch();
    } catch {
      toast.error("Erro ao salvar meta financeira.");
    }
  }

  // Níveis de Maturidade
  let levelName = "🌱 Nível 1: Clínica Inicial";
  let levelClass = styles.levelBadgeInicial;
  if (progressPct >= 100) {
    levelName = "👑 Nível 3: Alta Performance";
    levelClass = styles.levelBadgePerformance;
  } else if (progressPct >= 34) {
    levelName = "⚡ Nível 2: Clínica Digital";
    levelClass = styles.levelBadgeDigital;
  }

  if (allDone) {
    return (
      <section
        className={`${styles.onboardingCard} ${styles.onboardingCardSuccess}`}
        aria-label="Certificado de Ativação da Clínica"
      >
        <div className={styles.celebrationContent}>
          <div className={styles.celebrationHeader}>
            <div className={styles.trophyCircle}>
              🏆
            </div>
            <div className={styles.celebrationTextGroup}>
              <div className={styles.badgeRow}>
                <span className={`${styles.levelBadge} ${styles.levelBadgePerformance}`}>
                  Maturidade 100% • Alta Performance
                </span>
              </div>
              <h2 className={styles.celebrationTitle}>
                Sua clínica está 100% pronta para faturar com alta previsibilidade!
              </h2>
              <p className={styles.celebrationSubtitle}>
                Você completou todas as etapas essenciais de ativação: procedimentos, pacientes, taxas, metas e campanhas.
              </p>
            </div>
          </div>

          <div className={styles.celebrationActions}>
            <Link to="/planos" className={styles.primaryCtaBtn}>
              <IconSparkles width="15" height="15" />
              <span>Ver Planos & Benefícios Ativos</span>
            </Link>
            <button
              type="button"
              onClick={handleDismiss}
              className={styles.toggleBtn}
            >
              Concluir e Ocultar
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.onboardingCard} aria-label="Maturidade e Primeiros Passos da Clínica">
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <div className={styles.badgeRow}>
            <span className={`${styles.levelBadge} ${levelClass}`}>
              {levelName}
            </span>
            <span style={{ fontSize: "11.5px", color: "var(--text-muted)", fontWeight: 600 }}>
              {completedCount} de {steps.length} etapas concluídas
            </span>
          </div>
          <h2 className={styles.title}>Maturidade da sua Clínica ({progressPct}%)</h2>
          <p className={styles.subtitle}>
            Complete as etapas de ativação para operar no nível de Alta Performance.
          </p>
        </div>

        <div className={styles.headerActions}>
          <button
            type="button"
            onClick={() => setIsMinimized((prev) => !prev)}
            className={styles.toggleBtn}
          >
            {isMinimized ? "Expandir" : "Minimizar"}
          </button>
          <button
            type="button"
            onClick={handleDismiss}
            className={styles.toggleBtn}
            title="Ocultar checklist permanentemente"
          >
            Dispensar
          </button>
        </div>
      </header>

      <div className={styles.progressContainer}>
        <div className={styles.progressBarTrack}>
          <div className={styles.progressBarFill} style={{ width: `${Math.max(4, progressPct)}%` }} />
        </div>
        <div className={styles.progressLabelsRow}>
          <span>Inicial (0%)</span>
          <span>Digital (34%)</span>
          <span>Alta Performance (100% 👑)</span>
        </div>
      </div>

      {!isMinimized && (
        <>
          <div className={styles.stepsGrid}>
            {steps.map((step) => (
              <div
                key={step.id}
                className={`${styles.stepCard} ${step.done ? styles.stepCardDone : ""}`}
              >
                <div className={styles.stepLeft}>
                  {step.done ? (
                    <div className={styles.stepIconCheck}>
                      <IconCheck width="13" height="13" />
                    </div>
                  ) : (
                    <div className={styles.stepIconPending}>
                      ○
                    </div>
                  )}
                  <div className={styles.stepTextGroup}>
                    <h3 className={styles.stepLabel}>{step.label}</h3>
                    <p className={styles.stepDesc}>{step.desc}</p>
                  </div>
                </div>

                {!step.done ? (
                  step.id === "goals" ? (
                    <button
                      type="button"
                      onClick={handleOpenGoalModal}
                      className={styles.stepActionBtn}
                      style={{ background: "#f0fdf4", border: "1px solid #86efac", color: "#166534" }}
                    >
                      <span>Definir</span>
                      <IconArrowRight width="13" height="13" />
                    </button>
                  ) : (
                    <Link to={step.link} className={styles.stepActionBtn}>
                      <span>{step.actionText}</span>
                      <IconArrowRight width="13" height="13" />
                    </Link>
                  )
                ) : (
                  <span style={{ fontSize: "11.5px", fontWeight: 700, color: "#16a34a" }}>
                    Pronto ✓
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className={styles.rewardBox}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <IconTarget width="16" height="16" color="var(--accent)" />
              <span>
                <strong>Dica de Alta Performance:</strong> Complete 100% do setup durante seus 14 dias de teste e aproveite as condições de inauguração da plataforma.
              </span>
            </div>
            <Link
              to="/planos"
              style={{
                fontSize: "12px",
                fontWeight: 700,
                color: "var(--accent)",
                textDecoration: "none",
                whiteSpace: "nowrap",
              }}
            >
              Conhecer Planos →
            </Link>
          </div>
        </>
      )}

      {/* Modal Ágil de Meta Financeira Mensal */}
      {showGoalModal && (
        <div
          className={styles.modalOverlay}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-meta-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowGoalModal(false);
          }}
        >
          <div className={styles.modalDialog}>
            <header className={styles.modalHeader}>
              <h3 id="modal-meta-title" className={styles.modalTitle}>
                <span>🎯</span>
                <span>Definir Meta do Mês</span>
              </h3>
              <p className={styles.modalDesc}>
                Defina um objetivo financeiro para sua clínica faturar este mês e ative o termômetro de conquista do Dashboard.
              </p>
            </header>

            <div className={styles.modalInputGroup}>
              <span className={styles.modalInputPrefix}>R$</span>
              <input
                type="text"
                inputMode="decimal"
                value={goalInputValue}
                onChange={(e) => setGoalInputValue(e.target.value)}
                placeholder="ex: 20000.00"
                className={styles.modalInput}
                autoFocus
              />
            </div>

            <div>
              <span style={{ fontSize: "12px", fontWeight: 600, color: "#475569", display: "block", marginBottom: "6px" }}>
                Valores sugeridos:
              </span>
              <div className={styles.chipRow}>
                {[
                  { label: "R$ 5.000", val: "5000.00" },
                  { label: "R$ 10.000", val: "10000.00" },
                  { label: "R$ 20.000", val: "20000.00" },
                  { label: "R$ 30.000", val: "30000.00" },
                  { label: "R$ 50.000", val: "50000.00" },
                ].map((sug) => (
                  <button
                    key={sug.val}
                    type="button"
                    className={styles.chipBtn}
                    onClick={() => {
                      setGoalInputValue(sug.val);
                      handleSaveGoalModal(sug.val);
                    }}
                  >
                    {sug.label}
                  </button>
                ))}
              </div>
            </div>

            <footer className={styles.modalFooter}>
              <div className={styles.modalFooterLeft}>
                <Link
                  to="/financeiro"
                  onClick={() => setShowGoalModal(false)}
                  style={{ fontSize: "12px", color: "var(--primary, #0284c7)", textDecoration: "none", fontWeight: 500 }}
                >
                  Abrir Financeiro Completo →
                </Link>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  type="button"
                  className={styles.cancelBtn}
                  onClick={() => setShowGoalModal(false)}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className={styles.saveBtn}
                  disabled={updateSettingsMutation.isPending}
                  onClick={() => handleSaveGoalModal()}
                >
                  {updateSettingsMutation.isPending ? "Salvando…" : "Salvar Meta"}
                </button>
              </div>
            </footer>
          </div>
        </div>
      )}
    </section>
  );
}
