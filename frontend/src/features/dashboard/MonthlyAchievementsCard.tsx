import { useState } from "react";
import { useDashboard, useProcedureRanking } from "./hooks";
import { useUpdateFinancialSettings } from "@/features/settings/hooks";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { toast } from "@/ui/ToastContext";
import {
  IconSparkles,
  IconCopy,
  IconCheck,
  IconWhatsApp,
  IconX,
  IconEdit,
} from "@/ui/icons";
import styles from "./MonthlyAchievementsCard.module.css";

interface MonthlyAchievementsCardProps {
  scope?: "me" | "clinic";
  professionalId?: string;
}

export function MonthlyAchievementsCard({
  scope = "me",
  professionalId,
}: MonthlyAchievementsCardProps) {
  const [period, setPeriod] = useState<"this_month" | "last_month">("this_month");
  const [showShareModal, setShowShareModal] = useState(false);
  const [copied, setCopied] = useState(false);

  // Gamificação: Estado de edição da Meta
  const [isEditingGoal, setIsEditingGoal] = useState(false);
  const [goalInput, setGoalInput] = useState("");

  const updateSettingsMutation = useUpdateFinancialSettings();

  const dashboardQuery = useDashboard({
    period,
    scope,
    professional_id: professionalId,
  });

  const rankingQuery = useProcedureRanking({
    period,
    scope,
    professional_id: professionalId,
    page: 1,
    page_size: 1,
  });

  const data = dashboardQuery.data;
  if (!data || !data.has_any_data) {
    return null;
  }

  const championProcedure = rankingQuery.data?.rows?.[0];

  const netProfitInPocket =
    data.net_profit_after_fixed_expenses != null
      ? data.net_profit_after_fixed_expenses
      : data.net_profit;

  const isBreakevenAchieved =
    data.breakeven_remaining_amount != null
      ? !(Number(data.breakeven_remaining_amount) > 0)
      : null;

  const isBreakevenBeaten = Boolean(data.breakeven_beaten);
  const breakevenDateFormatted = data.breakeven_beaten_date
    ? new Date(data.breakeven_beaten_date + "T12:00:00").toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
      })
    : null;

  // Gamificação: Metas Financeiras
  const hasGoal = data.monthly_revenue_goal != null && Number(data.monthly_revenue_goal) > 0;
  const goalAmount = hasGoal ? Number(data.monthly_revenue_goal) : 0;
  const grossRevenueNum = Number(data.gross_revenue) || 0;
  const goalPercent = hasGoal ? Math.min(100, Math.round((grossRevenueNum / goalAmount) * 100)) : 0;
  const isGoalBeaten = hasGoal && grossRevenueNum >= goalAmount;
  const remainingToGoal = hasGoal ? Math.max(0, goalAmount - grossRevenueNum) : 0;

  const handleStartEditGoal = () => {
    setGoalInput(data.monthly_revenue_goal ? String(Number(data.monthly_revenue_goal)) : "");
    setIsEditingGoal(true);
  };

  const handleSaveGoal = async () => {
    try {
      const cleanVal = goalInput.trim() ? goalInput.replace(/[^\d.,]/g, "").replace(",", ".") : null;
      await updateSettingsMutation.mutateAsync({
        monthly_revenue_goal: cleanVal,
      });
      toast.success("Meta financeira mensal atualizada!");
      setIsEditingGoal(false);
      dashboardQuery.refetch();
    } catch {
      toast.error("Erro ao salvar a meta.");
    }
  };

  const periodLabel = period === "this_month" ? "Deste Mês" : "Do Mês Anterior";

  const motivationalMessage = isGoalBeaten
    ? `Incrível! 🏆 Você já atingiu 100% da sua meta de faturamento e colocou ${formatBRL(
        money(netProfitInPocket)
      )} líquidos no bolso!`
    : isBreakevenAchieved
    ? `Parabéns! Todas as contas e custos fixos já foram cobertos e você já colocou ${formatBRL(
        money(netProfitInPocket)
      )} limpos no bolso!`
    : data.breakeven_remaining_amount
    ? `Você já realizou ${data.session_count} atendimentos este mês. Faltam apenas ${formatBRL(
        money(data.breakeven_remaining_amount)
      )} para cobrir todas as despesas fixas!`
    : `Excelente trabalho! Você acumulou ${formatBRL(
        money(netProfitInPocket)
      )} de lucro líquido em ${data.session_count} atendimentos realizados.`;

  const shareText = `✨ *Seu Mês no Bolso (${periodLabel})* ✨
━━━━━━━━━━━━━━━━━━━━
💰 *Faturamento:* ${formatBRL(money(data.gross_revenue))}
💵 *Lucro Real no Bolso:* ${formatBRL(money(netProfitInPocket))}
${
  hasGoal
    ? `🎯 *Meta do Mês:* ${formatBRL(money(String(goalAmount)))} (${goalPercent}% batida ${isGoalBeaten ? "🏆" : ""})\n`
    : ""
}🎯 *Ponto de Equilíbrio:* ${
    isBreakevenAchieved
      ? `Custos fixos 100% cobertos! 🎉${breakevenDateFormatted ? ` (batido em ${breakevenDateFormatted})` : ""}`
      : data.breakeven_remaining_amount
      ? `Faltam ${formatBRL(money(data.breakeven_remaining_amount))}`
      : "Em dia"
  }
💆‍♀️ *Atendimentos:* ${data.session_count} clientes atendidas
${
  championProcedure
    ? `⭐ *Procedimento Campeão:* ${championProcedure.procedure_name} (${championProcedure.session_count} sessões)`
    : ""
}
━━━━━━━━━━━━━━━━━━━━
🚀 Gestão inteligente com Estética Manager`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      toast.success("Resumo copiado para o clipboard!");
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // fallback
    }
  };

  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`;

  return (
    <div className={styles.card}>
      <div className={styles.topBar}>
        <div className={styles.badge}>
          <IconSparkles width="14" height="14" />
          <span>Seu Mês no Bolso</span>
        </div>

        <div className={styles.periodToggle}>
          <button
            type="button"
            className={`${styles.toggleBtn} ${
              period === "this_month" ? styles.toggleBtnActive : ""
            }`}
            onClick={() => setPeriod("this_month")}
          >
            Mês Atual
          </button>
          <button
            type="button"
            className={`${styles.toggleBtn} ${
              period === "last_month" ? styles.toggleBtnActive : ""
            }`}
            onClick={() => setPeriod("last_month")}
          >
            Mês Anterior
          </button>
        </div>
      </div>

      <div className={styles.headerText}>
        <h3 className={styles.title}>Conquistas & Lucro Real {periodLabel}</h3>
        <p className={styles.motivationalText}>{motivationalMessage}</p>
      </div>

      {/* GAMIFICAÇÃO 1: CELEBRAÇÃO DE PONTO DE EQUILÍBRIO BATIDO */}
      {isBreakevenBeaten && (
        <div className={styles.breakevenCelebration}>
          <div className={styles.breakevenIconCircle}>
            <IconCheck width="20" height="20" />
          </div>
          <div className={styles.breakevenTextGroup}>
            <h4 className={styles.breakevenTitle}>
              🎉 Ponto de Equilíbrio Conquistado{breakevenDateFormatted ? ` no dia ${breakevenDateFormatted}` : ""}!
            </h4>
            <p className={styles.breakevenSubtitle}>
              Todas as contas e custos fixos já foram 100% cobertos neste mês. A partir de agora, cada novo atendimento é lucro limpo no seu bolso.
            </p>
          </div>
        </div>
      )}

      {/* GAMIFICAÇÃO 2: META DE FATURAMENTO MENSAL */}
      <div className={styles.goalSection}>
        <div className={styles.goalHeader}>
          <div className={styles.goalTitleGroup}>
            <h4 className={styles.goalTitle}>🎯 Meta de Faturamento Mensal</h4>
            {hasGoal && (
              <span className={`${styles.goalBadge} ${isGoalBeaten ? styles.goalBadgeBeaten : ""}`}>
                {isGoalBeaten ? "🏆 Meta Batida!" : `${goalPercent}% Atingido`}
              </span>
            )}
          </div>

          {!isEditingGoal && (
            <button
              type="button"
              className={styles.goalEditBtn}
              onClick={handleStartEditGoal}
            >
              <IconEdit width="13" height="13" />
              <span>{hasGoal ? "Alterar Meta" : "Definir Meta"}</span>
            </button>
          )}
        </div>

        {isEditingGoal ? (
          <div className={styles.goalInputRow}>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text)" }}>R$</span>
            <input
              type="number"
              step="500"
              placeholder="Ex: 20000"
              className={styles.goalInput}
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              autoFocus
            />
            <button
              type="button"
              className={styles.goalSaveBtn}
              onClick={handleSaveGoal}
              disabled={updateSettingsMutation.isPending}
            >
              {updateSettingsMutation.isPending ? "Salvando..." : "Salvar Meta"}
            </button>
            <button
              type="button"
              className={styles.goalCancelBtn}
              onClick={() => setIsEditingGoal(false)}
            >
              Cancelar
            </button>
          </div>
        ) : hasGoal ? (
          <>
            <div className={styles.progressBarContainer}>
              <div
                className={`${styles.progressBarFill} ${isGoalBeaten ? styles.progressBarFillComplete : ""}`}
                style={{ width: `${Math.min(100, Math.max(3, goalPercent))}%` }}
              />
            </div>

            <div className={styles.goalMarkersRow}>
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100% 🏁</span>
            </div>

            <div className={styles.goalSummaryRow}>
              <span>
                <strong>Faturado:</strong> {formatBRL(money(data.gross_revenue))} de{" "}
                <strong>{formatBRL(money(String(goalAmount)))}</strong>
              </span>
              <span>
                {isGoalBeaten
                  ? "✨ Parabéns pelo resultado extraordinário!"
                  : `Faltam ${formatBRL(money(String(remainingToGoal)))} para a meta`}
              </span>
            </div>
          </>
        ) : (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
            <span style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
              Defina sua meta mensal para acompanhar o termômetro de conquista da clínica.
            </span>
            <button
              type="button"
              className={styles.goalSaveBtn}
              onClick={handleStartEditGoal}
            >
              + Definir Meta
            </button>
          </div>
        )}
      </div>

      <div className={styles.metricsGrid}>
        <div className={styles.metricBox}>
          <span className={styles.metricLabel}>Faturamento Bruto</span>
          <span className={styles.metricValue}>
            {formatBRL(money(data.gross_revenue))}
          </span>
          <span className={styles.metricSubtext}>
            {data.sale_count} venda(s) registrada(s)
          </span>
        </div>

        <div className={styles.metricBox}>
          <span className={styles.metricLabel}>Lucro Limpo no Bolso</span>
          <span className={`${styles.metricValue} ${styles.metricValueHighlight}`}>
            {formatBRL(money(netProfitInPocket))}
          </span>
          <span className={styles.metricSubtext}>
            Livre de insumos, taxas e despesas fixas
          </span>
        </div>

        <div className={styles.metricBox}>
          <span className={styles.metricLabel}>Custos Fixos & Breakeven</span>
          <span className={styles.metricValue} style={{ fontSize: "15px" }}>
            {isBreakevenAchieved
              ? "100% Cobertos! 🎉"
              : data.breakeven_remaining_amount
              ? `Faltam ${formatBRL(money(data.breakeven_remaining_amount))}`
              : "Sem despesas fixas"}
          </span>
          <span className={styles.metricSubtext}>
            {isBreakevenAchieved
              ? "Tudo que entrar agora é lucro puro"
              : "Necessário para pagar contas fixas"}
          </span>
        </div>

        {championProcedure && (
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Procedimento Campeão</span>
            <span className={styles.metricValue} style={{ fontSize: "14px" }}>
              {championProcedure.procedure_name}
            </span>
            <span className={styles.metricSubtext}>
              {championProcedure.session_count} sessões •{" "}
              {formatBRL(money(championProcedure.gross_revenue))}
            </span>
          </div>
        )}
      </div>

      <div className={styles.footerActions}>
        <button
          type="button"
          className={styles.shareBtn}
          onClick={() => setShowShareModal(true)}
        >
          <IconSparkles width="14" height="14" />
          <span>Ver Resumo de Compartilhamento</span>
        </button>
      </div>

      {showShareModal && (
        <div className={styles.modalOverlay} role="dialog" aria-modal="true">
          <div className={styles.modalBox}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h4 style={{ margin: 0, fontSize: "16px", fontWeight: 700 }}>
                Resumo Conquistas {periodLabel}
              </h4>
              <button
                type="button"
                style={{ background: "none", border: "none", cursor: "pointer" }}
                onClick={() => setShowShareModal(false)}
              >
                <IconX width="18" height="18" />
              </button>
            </div>

            <div className={styles.previewPaper}>
              {shareText}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button
                type="button"
                className={styles.shareBtn}
                onClick={handleCopy}
              >
                {copied ? <IconCheck width="14" height="14" color="#16a34a" /> : <IconCopy width="14" height="14" />}
                <span>{copied ? "Copiado!" : "Copiar Texto"}</span>
              </button>
              <a
                href={whatsappUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`${styles.shareBtn} ${styles.shareBtnWhatsApp}`}
              >
                <IconWhatsApp width="14" height="14" />
                <span>Enviar pelo WhatsApp</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
