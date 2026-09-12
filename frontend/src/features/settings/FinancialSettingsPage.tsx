import { Link, useSearchParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { FinancialSettingsForm } from "./FinancialSettingsForm";
import { PaymentFeeRulesManager } from "./PaymentFeeRulesManager";
import { WeeklySummarySection } from "./WeeklySummarySection";
import { LoyaltyRewardsManager } from "@/features/loyalty/LoyaltyRewardsManager";
import { useFinancialSettings } from "./hooks";
import { IconSettings, IconCreditCard, IconWhatsApp } from "@/ui/icons";
import styles from "./FinancialSettingsPage.module.css";

type Tab = "general" | "credit-card" | "loyalty" | "weekly-summary";

export function FinancialSettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get("tab");
  const activeTab: Tab =
    rawTab === "credit-card" || rawTab === "loyalty" || rawTab === "weekly-summary"
      ? rawTab
      : "general";

  const financialQuery = useFinancialSettings();

  function handleTabChange(tab: Tab) {
    if (tab === "general") {
      searchParams.delete("tab");
      setSearchParams(searchParams, { replace: true });
    } else {
      searchParams.set("tab", tab);
      setSearchParams(searchParams, { replace: true });
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <h1 className={styles.title}>Financeiro &amp; Metas</h1>
          <p className={styles.subtitle}>
            Gerencie seu modelo de comissões, taxas de maquininha, catálogo do Clube VIP e resumo semanal.
          </p>
        </div>
        <div>
          <Link
            to="/despesas-fixas"
            className="button button--secondary"
            style={{ fontSize: "0.82rem", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}
          >
            <span>Custos Fixos &amp; Equilíbrio &rarr;</span>
          </Link>
        </div>
      </header>

      {/* Navegação por Abas no Topo */}
      <nav className={styles.tabNav} role="tablist" aria-label="Abas de configurações financeiras">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "general"}
          className={`${styles.tabBtn} ${activeTab === "general" ? styles.tabBtnActive : ""}`}
          onClick={() => handleTabChange("general")}
        >
          <span className={styles.tabIcon}>
            <IconSettings width="16" height="16" />
          </span>
          <span>Modelo &amp; Taxas Gerais</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "credit-card"}
          className={`${styles.tabBtn} ${activeTab === "credit-card" ? styles.tabBtnActive : ""}`}
          onClick={() => handleTabChange("credit-card")}
        >
          <span className={styles.tabIcon}>
            <IconCreditCard width="16" height="16" />
          </span>
          <span>Taxas de Cartão de Crédito</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "loyalty"}
          className={`${styles.tabBtn} ${activeTab === "loyalty" ? styles.tabBtnActive : ""}`}
          onClick={() => handleTabChange("loyalty")}
        >
          <span className={styles.tabIcon} style={{ fontSize: "1rem" }}>
            🎁
          </span>
          <span>Catálogo VIP &amp; Recompensas</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "weekly-summary"}
          className={`${styles.tabBtn} ${activeTab === "weekly-summary" ? styles.tabBtnActive : ""}`}
          onClick={() => handleTabChange("weekly-summary")}
        >
          <span className={styles.tabIcon}>
            <IconWhatsApp width="16" height="16" />
          </span>
          <span>Resumo Semanal no WhatsApp</span>
        </button>
      </nav>

      {/* Conteúdo da Aba Ativa */}
      <div className={styles.tabContent} role="tabpanel">
        {activeTab === "general" && (
          <AsyncBoundary
            query={financialQuery}
            skeleton={<p>Carregando configurações financeiras…</p>}
            empty={<p>Não foi possível carregar as configurações.</p>}
          >
            {(settings) => <FinancialSettingsForm initial={settings} />}
          </AsyncBoundary>
        )}

        {activeTab === "credit-card" && <PaymentFeeRulesManager />}

        {activeTab === "loyalty" && <LoyaltyRewardsManager />}

        {activeTab === "weekly-summary" && <WeeklySummarySection />}
      </div>
    </div>
  );
}


