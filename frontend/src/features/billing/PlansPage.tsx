import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  IconSparkles,
  IconCheck,
  IconLock,
  IconCreditCard,
  IconArrowRight,
  IconClock,
} from "@/ui/icons";
import {
  getPlans,
  createCheckout,
  type BillingCycle,
  type CouponValidation,
  type CheckoutResponse,
} from "./billingApi";
import { CouponInput } from "./CouponInput";
import styles from "./PlansPage.module.css";

const CYCLE_DETAILS: Record<
  BillingCycle,
  { name: string; desc: string; badge?: string; isBest?: boolean }
> = {
  MONTHLY: {
    name: "Mensal",
    desc: "Flexibilidade mês a mês, cancele quando desejar.",
  },
  QUARTERLY: {
    name: "Trimestral",
    desc: "Cobrado a cada 3 meses. Mais tranquilidade.",
    badge: "Mais Escolhido",
    isBest: true,
  },
  YEARLY: {
    name: "Anual",
    desc: "Cobrança anual com o melhor custo-benefício.",
    badge: "Maior Economia 37% OFF",
  },
};

export function PlansPage() {
  const [selectedCycle, setSelectedCycle] = useState<BillingCycle>("QUARTERLY");
  const [billingType, setBillingType] = useState<"PIX" | "CREDIT_CARD" | "BOLETO">("CREDIT_CARD");
  const [document, setDocument] = useState("");
  const [phone, setPhone] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState<CouponValidation | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [checkoutSuccess, setCheckoutSuccess] = useState<CheckoutResponse | null>(null);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);

  const { data: plans, isLoading, isError } = useQuery({
    queryKey: ["billing-plans"],
    queryFn: getPlans,
  });

  const plan = plans?.[0];

  function handleSelectCycle(cycle: BillingCycle) {
    setSelectedCycle(cycle);
    // Se mudou o ciclo, limpa cupom caso tenha restrição de ciclo
    if (appliedCoupon) {
      setAppliedCoupon(null);
    }
  }

  const currentCyclePricing = plan?.cycles.find((c) => c.cycle === selectedCycle);

  // Cálculo de valores com ou sem cupom
  const baseTotal = currentCyclePricing ? Number(currentCyclePricing.total_amount) : 0;
  const finalTotal = appliedCoupon ? Number(appliedCoupon.final_amount) : baseTotal;
  const discountAmount = appliedCoupon ? Number(appliedCoupon.discount_amount) : 0;

  async function handleCheckout(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setCheckoutError(null);

    try {
      const res = await createCheckout({
        cycle: selectedCycle,
        coupon_code: appliedCoupon?.code,
        billing_type: billingType,
        document: document.trim() || undefined,
        phone: phone.trim() || undefined,
      });
      setCheckoutSuccess(res);
    } catch (err: any) {
      setCheckoutError(err?.message || "Não foi possível processar a assinatura. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: "center", padding: "4rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>Carregando planos de inauguração...</p>
        </div>
      </div>
    );
  }

  if (isError || !plan) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: "center", padding: "4rem" }}>
          <p style={{ color: "#ef4444" }}>Erro ao carregar os planos. Recarregue a página.</p>
        </div>
      </div>
    );
  }

  // Visualização pós checkout / confirmação
  if (checkoutSuccess) {
    return (
      <div className={styles.container}>
        <div className={styles.successBox}>
          <div className={styles.successIcon}>
            <IconCheck width="32" height="32" />
          </div>
          <h2 className={styles.successTitle}>Assinatura Iniciada!</h2>
          <p className={styles.successDesc}>
            Seu plano <strong>Lumina Pro ({selectedCycle})</strong> foi registrado com sucesso.
            {checkoutSuccess.is_trial_included ? (
              <>
                <br />
                Você tem <strong>14 dias de teste grátis</strong>. Seu primeiro vencimento está
                agendado para <strong>{new Date(checkoutSuccess.first_due_date).toLocaleDateString("pt-BR")}</strong>.
              </>
            ) : null}
          </p>

          {checkoutSuccess.invoice_url && (
            <div style={{ marginTop: "1.5rem" }}>
              <a
                href={checkoutSuccess.invoice_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.asaasLinkBtn}
              >
                <span>Acessar Fatura no Asaas</span>
                <IconArrowRight width="16" height="16" />
              </a>
            </div>
          )}

          <div style={{ marginTop: "2rem" }}>
            <button
              type="button"
              className={styles.submitBtn}
              style={{ background: "transparent", color: "var(--primary)", border: "1px solid var(--primary)" }}
              onClick={() => {
                setCheckoutSuccess(null);
                window.location.href = "/dashboard";
              }}
            >
              Ir para o Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header com destaque de inauguração */}
      <div className={styles.header}>
        <div className={styles.promoBadge}>
          <IconSparkles width="16" height="16" />
          <span>{plan.promo_badge}</span>
        </div>
        <h1 className={styles.title}>Garanta sua vaga com preço travado</h1>
        <p className={styles.subtitle}>
          Preço promocional vitalício garantido para as clínicas pioneiras. Escolha o ciclo ideal para você.
        </p>
        <div className={styles.trialBannerBox}>
          <IconClock width="18" height="18" />
          <span>2 semanas (14 dias) grátis no primeiro mês sem cobrança imediata</span>
        </div>
      </div>

      {/* Grid com os 3 Ciclos de Assinatura */}
      <div className={styles.cardsGrid}>
        {plan.cycles.map((cycleItem) => {
          const isSelected = selectedCycle === cycleItem.cycle;
          const meta = CYCLE_DETAILS[cycleItem.cycle];
          const hasDiscount = Number(cycleItem.savings_percentage) > 0;

          return (
            <div
              key={cycleItem.cycle}
              className={`${styles.card} ${isSelected ? styles.cardSelected : ""} ${
                meta?.isBest ? styles.featuredCard : ""
              }`}
              onClick={() => handleSelectCycle(cycleItem.cycle)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  handleSelectCycle(cycleItem.cycle);
                }
              }}
            >
              {meta?.badge && (
                <div
                  className={`${styles.cardBadge} ${
                    meta.isBest ? styles.cardBadgeBest : ""
                  }`}
                >
                  {meta.badge}
                </div>
              )}

              <div className={styles.cardHeader}>
                <h2 className={styles.cycleName}>{meta?.name || cycleItem.cycle}</h2>
                <p className={styles.cycleDescription}>{meta?.desc}</p>
              </div>

              <div className={styles.pricingSection}>
                <div className={styles.priceRow}>
                  <span className={styles.currency}>R$</span>
                  <span className={styles.priceAmount}>
                    {Math.floor(Number(cycleItem.monthly_equivalent))}
                  </span>
                  <span className={styles.priceInterval}>/mês</span>
                </div>

                <div className={styles.billingDetail}>
                  {cycleItem.cycle === "MONTHLY" && "Cobrado R$ 80 todo mês"}
                  {cycleItem.cycle === "QUARTERLY" && "Cobrado R$ 195 a cada 3 meses"}
                  {cycleItem.cycle === "YEARLY" && "Cobrado R$ 600 anualmente"}
                </div>

                {hasDiscount && (
                  <div className={styles.savingsPill}>
                    Economize {cycleItem.savings_percentage}%
                  </div>
                )}
              </div>

              <div className={styles.radioIndicator}>
                <input
                  type="radio"
                  name="billingCycle"
                  checked={isSelected}
                  onChange={() => handleSelectCycle(cycleItem.cycle)}
                  aria-label={`Selecionar plano ${meta?.name}`}
                />
                <span>{isSelected ? "Selecionado" : "Selecionar"}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Caixa de Checkout & Forma de Pagamento */}
      <div className={styles.checkoutSection}>
        <h2 className={styles.sectionHeading}>Finalizar Assinatura</h2>

        <form onSubmit={handleCheckout}>
          {/* Escolha do Método */}
          <div className={styles.fieldGroup} style={{ marginBottom: "1.25rem" }}>
            <label className={styles.label}>Forma de Pagamento</label>
            <div className={styles.methodSelector}>
              <button
                type="button"
                className={`${styles.methodBtn} ${billingType === "CREDIT_CARD" ? styles.methodSelected : ""}`}
                onClick={() => setBillingType("CREDIT_CARD")}
              >
                <IconCreditCard width="20" height="20" />
                <span>Cartão de Crédito</span>
              </button>
              <button
                type="button"
                className={`${styles.methodBtn} ${billingType === "PIX" ? styles.methodSelected : ""}`}
                onClick={() => setBillingType("PIX")}
              >
                <IconSparkles width="20" height="20" />
                <span>Pix</span>
              </button>
              <button
                type="button"
                className={`${styles.methodBtn} ${billingType === "BOLETO" ? styles.methodSelected : ""}`}
                onClick={() => setBillingType("BOLETO")}
              >
                <IconLock width="20" height="20" />
                <span>Boleto Bancário</span>
              </button>
            </div>
          </div>

          {/* Dados Fiscais para Nota */}
          <div className={styles.formGrid}>
            <div className={styles.fieldGroup}>
              <label className={styles.label} htmlFor="cpf-cnpj">
                CPF ou CNPJ (para emissão de NF)
              </label>
              <input
                id="cpf-cnpj"
                type="text"
                className={styles.input}
                placeholder="000.000.000-00"
                value={document}
                onChange={(e) => setDocument(e.target.value)}
              />
            </div>
            <div className={styles.fieldGroup}>
              <label className={styles.label} htmlFor="phone">
                WhatsApp / Telefone
              </label>
              <input
                id="phone"
                type="tel"
                className={styles.input}
                placeholder="(00) 00000-0000"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </div>

          {/* Cupom de Desconto */}
          <div style={{ marginBottom: "1.5rem" }}>
            <label className={styles.label}>Cupom de Inauguração ou Parceiro</label>
            <CouponInput
              selectedCycle={selectedCycle}
              appliedCoupon={appliedCoupon}
              onCouponApplied={setAppliedCoupon}
            />
          </div>

          {/* Resumo Financeiro */}
          <div className={styles.summaryBox}>
            <div className={styles.summaryRow}>
              <span>Plano Lumina Pro ({CYCLE_DETAILS[selectedCycle]?.name})</span>
              <span>R$ {baseTotal.toFixed(2)}</span>
            </div>

            {appliedCoupon && (
              <div className={styles.summaryRow} style={{ color: "#059669" }}>
                <span>Desconto Cupom ({appliedCoupon.code})</span>
                <span>- R$ {discountAmount.toFixed(2)}</span>
              </div>
            )}

            <div className={styles.summaryRow}>
              <span>Período de Degustação</span>
              <span style={{ color: "#059669", fontWeight: 600 }}>14 dias grátis</span>
            </div>

            <div className={styles.summaryTotal}>
              <span>Total no primeiro ciclo:</span>
              <span>R$ {finalTotal.toFixed(2)}</span>
            </div>
          </div>

          {checkoutError && (
            <p style={{ color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem" }}>
              {checkoutError}
            </p>
          )}

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span>Processando no Asaas...</span>
            ) : (
              <>
                <span>Ativar Assinatura com 14 Dias Grátis</span>
                <IconArrowRight width="18" height="18" />
              </>
            )}
          </button>

          <div className={styles.securityNote}>
            <IconLock width="14" height="14" />
            <span>Processamento seguro via Asaas Pagamentos • Cancele quando quiser</span>
          </div>
        </form>
      </div>

      {/* Lista de Recursos Incluídos */}
      <div className={styles.featuresGrid}>
        <h2 className={styles.featuresTitle}>Tudo o que sua clínica precisa em um só lugar</h2>
        <ul className={styles.featuresList}>
          {plan.features.map((feature, idx) => (
            <li key={idx} className={styles.featureItem}>
              <span className={styles.checkIcon}>
                <IconCheck width="18" height="18" />
              </span>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
