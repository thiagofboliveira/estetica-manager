import { useState } from "react";
import { useDashboard, useProcedureRanking } from "./hooks";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import {
  IconSparkles,
  IconCopy,
  IconCheck,
  IconWhatsApp,
  IconX,
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

  const periodLabel = period === "this_month" ? "Deste Mês" : "Do Mês Anterior";

  const motivationalMessage =
    isBreakevenAchieved
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
🎯 *Ponto de Equilíbrio:* ${
    isBreakevenAchieved
      ? "Custos fixos 100% cobertos! 🎉"
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
