import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { IconClock, IconAlertTriangle, IconArrowRight, IconSparkles } from "@/ui/icons";
import { getSubscriptionStatus } from "./billingApi";
import styles from "./TrialCountdownBanner.module.css";

export function TrialCountdownBanner() {
  const { data: status, isLoading, isError } = useQuery({
    queryKey: ["billing-status"],
    queryFn: getSubscriptionStatus,
    staleTime: 1000 * 60 * 5, // 5 min
  });

  if (isLoading || isError || !status) return null;

  // Se já tem assinatura ativa paga, não precisa exibir o countdown de trial
  if (status.is_subscription_active && !status.is_trial_active) {
    return null;
  }

  // Caso: Período de Teste Grátis Ativo (14 dias)
  if (status.is_trial_active) {
    return (
      <div className={styles.banner} role="status">
        <div className={styles.content}>
          <div className={styles.iconWrapper}>
            <IconClock width="16" height="16" />
          </div>
          <div className={styles.message}>
            <strong>Período de Degustação Grátis:</strong> Restam{" "}
            <strong>{status.days_left_in_trial} {status.days_left_in_trial === 1 ? "dia" : "dias"}</strong>.
            <span className={styles.badge}>
              <IconSparkles width="12" height="12" style={{ display: "inline", verticalAlign: "-2px", marginRight: "3px" }} />
              Inauguração a partir de R$ 50/mês
            </span>
          </div>
        </div>
        <Link to="/assinatura" className={styles.ctaBtn}>
          <span>Garantir Preço Travado</span>
          <IconArrowRight width="14" height="14" />
        </Link>
      </div>
    );
  }

  // Caso: Trial Expirado sem Assinatura Ativa
  if (!status.is_subscription_active) {
    return (
      <div className={`${styles.banner} ${styles.bannerWarning}`} role="alert">
        <div className={styles.content}>
          <div className={`${styles.iconWrapper} ${styles.iconWarning}`}>
            <IconAlertTriangle width="16" height="16" />
          </div>
          <div className={styles.message}>
            <strong>Período de degustação encerrado.</strong> Ative seu plano para continuar acessando todos os recursos da Lumina sem interrupções.
          </div>
        </div>
        <Link to="/assinatura" className={`${styles.ctaBtn} ${styles.ctaWarning}`}>
          <span>Escolher Plano</span>
          <IconArrowRight width="14" height="14" />
        </Link>
      </div>
    );
  }

  return null;
}
