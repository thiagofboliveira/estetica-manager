import { useState } from "react";
import { Link } from "react-router-dom";
import { usePatients } from "@/features/patients/hooks";
import { useProcedures } from "@/features/procedures/hooks";
import { useFinancialSettings } from "@/features/settings/hooks";
import { useCampaignTemplates } from "@/features/whatsapp-campaigns/useCampaignTemplates";
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
                  <Link to={step.link} className={styles.stepActionBtn}>
                    <span>{step.actionText}</span>
                    <IconArrowRight width="13" height="13" />
                  </Link>
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
    </section>
  );
}
