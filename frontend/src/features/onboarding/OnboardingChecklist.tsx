import { useState } from "react";
import { Link } from "react-router-dom";
import { usePatients } from "@/features/patients/hooks";
import { useProcedures } from "@/features/procedures/hooks";
import { useFinancialSettings } from "@/features/settings/hooks";

type Props = {
  hasAnySale: boolean;
};

export function OnboardingChecklist({ hasAnySale }: Props) {
  const [dismissed, setDismissed] = useState(() => {
    return localStorage.getItem("estetica_onboarding_dismissed") === "true";
  });

  const proceduresQuery = useProcedures();
  const patientsQuery = usePatients();
  const settingsQuery = useFinancialSettings();

  if (dismissed) {
    return null;
  }

  const hasProcedures = Boolean(proceduresQuery.data && proceduresQuery.data.length > 0);
  const hasPatients = Boolean(patientsQuery.data && patientsQuery.data.length > 0);
  const hasConfiguredSettings = Boolean(settingsQuery.data);

  const steps = [
    {
      id: "procedures",
      label: "Cadastrar serviços e procedimentos",
      done: hasProcedures,
      link: "/procedimentos/novo",
      actionText: "Cadastrar procedimento",
    },
    {
      id: "patients",
      label: "Cadastrar sua primeira paciente",
      done: hasPatients,
      link: "/pacientes/novo",
      actionText: "Cadastrar paciente",
    },
    {
      id: "import",
      label: "Importar suas pacientes existentes (opcional)",
      done: hasPatients,
      link: "/pacientes/importar",
      actionText: "Importar lista",
    },
    {
      id: "sales",
      label: "Registrar a primeira venda e ver o lucro real",
      done: hasAnySale,
      link: "/vendas/nova",
      actionText: "Registrar venda",
    },
    {
      id: "settings",
      label: "Ajustar taxas e despesas fixas da clínica",
      done: hasConfiguredSettings,
      link: "/configuracoes",
      actionText: "Ver configurações",
    },
  ];

  const completedCount = steps.filter((s) => s.done).length;
  const allDone = completedCount === steps.length;

  if (allDone) {
    return null;
  }

  function handleDismiss() {
    localStorage.setItem("estetica_onboarding_dismissed", "true");
    setDismissed(true);
  }

  const progressPct = Math.round((completedCount / steps.length) * 100);

  return (
    <section className="card onboarding-card" aria-label="Checklist de primeiros passos">
      <header className="onboarding-card__header">
        <div>
          <h2 className="onboarding-card__title">Primeiros passos no Estética Manager</h2>
          <p className="onboarding-card__subtitle">
            Configure seu catálogo e registre seus primeiros dados ({completedCount} de {steps.length} concluídos)
          </p>
        </div>
        <button
          type="button"
          onClick={handleDismiss}
          className="button--text button--secondary"
          style={{ minHeight: "36px", padding: "4px 10px" }}
          title="Ocultar checklist"
        >
          Ocultar
        </button>
      </header>

      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
      </div>

      <ul className="onboarding-list">
        {steps.map((step) => (
          <li key={step.id} className={`onboarding-item ${step.done ? "onboarding-item--done" : ""}`}>
            <div className="onboarding-item__info">
              <span className="onboarding-item__check">{step.done ? "✓" : "○"}</span>
              <span className="onboarding-item__label">{step.label}</span>
            </div>
            {!step.done && (
              <Link to={step.link} className="button button--secondary tap-target" style={{ minHeight: "40px", fontSize: "14px" }}>
                {step.actionText} →
              </Link>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
