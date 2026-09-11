import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth/AuthContext";
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
  const { user } = useAuth();
  const navigate = useNavigate();

  const [selectedCycle, setSelectedCycle] = useState<BillingCycle>("QUARTERLY");
  const [billingType, setBillingType] = useState<"PIX" | "CREDIT_CARD" | "BOLETO">("CREDIT_CARD");
  const [document, setDocument] = useState("");
  const [phone, setPhone] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState<CouponValidation | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [checkoutSuccess, setCheckoutSuccess] = useState<CheckoutResponse | null>(null);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [copiedPix, setCopiedPix] = useState(false);

  const { data: plans, isLoading, isError } = useQuery({
    queryKey: ["billing-plans"],
    queryFn: getPlans,
  });

  const plan = plans?.[0];

  // Restaura ciclo e cupom se o usuário acabou de voltar do login
  useEffect(() => {
    const savedCycle = sessionStorage.getItem("selectedPlanCycle") as BillingCycle | null;
    if (savedCycle && ["MONTHLY", "QUARTERLY", "YEARLY"].includes(savedCycle)) {
      setSelectedCycle(savedCycle);
      sessionStorage.removeItem("selectedPlanCycle");
    }
  }, []);

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

    // Se o usuário ainda não está logado, salva a intenção e guia para o login/cadastro
    if (!user) {
      sessionStorage.setItem("returnTo", "/assinatura");
      sessionStorage.setItem("selectedPlanCycle", selectedCycle);
      if (appliedCoupon) {
        sessionStorage.setItem("selectedCouponCode", appliedCoupon.code);
      }
      navigate("/login");
      return;
    }

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
      if (err?.status === 401 || err?.status === 403 || err?.code === "UNAUTHENTICATED") {
        setCheckoutError(
          "Sua sessão expirou ou não está autenticada. Acesse sua conta para concluir a assinatura."
        );
      } else {
        setCheckoutError(err?.message || "Não foi possível processar a assinatura. Tente novamente.");
      }
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
          <h2 className={styles.successTitle}>Assinatura Registrada!</h2>
          <p className={styles.successDesc}>
            Seu plano <strong>Lumina Pro ({selectedCycle})</strong> foi vinculado à sua conta com sucesso.
            {checkoutSuccess.is_trial_included ? (
              <>
                <br />
                Você tem <strong>14 dias de teste grátis</strong>. Seu primeiro vencimento está
                agendado para <strong>{new Date(checkoutSuccess.first_due_date).toLocaleDateString("pt-BR")}</strong>.
              </>
            ) : null}
          </p>

          {/* Se houver código Pix copia e cola */}
          {checkoutSuccess.pix_qrcode_payload && (
            <div className={styles.pixBox}>
              <div className={styles.pixLabel}>Código Pix Copia e Cola:</div>
              <div className={styles.pixCode}>{checkoutSuccess.pix_qrcode_payload}</div>
              <button
                type="button"
                className={styles.copyPixBtn}
                onClick={() => {
                  navigator.clipboard.writeText(checkoutSuccess.pix_qrcode_payload || "");
                  setCopiedPix(true);
                  setTimeout(() => setCopiedPix(false), 2500);
                }}
              >
                <IconCheck width="16" height="16" />
                <span>{copiedPix ? "Código Pix Copiado!" : "Copiar Código Pix"}</span>
              </button>
            </div>
          )}

          {checkoutSuccess.invoice_url && (
            <div style={{ marginTop: "1.5rem" }}>
              <a
                href={checkoutSuccess.invoice_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.asaasLinkBtn}
              >
                <span>Acessar Fatura Completa no Asaas</span>
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
                navigate("/dashboard");
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

          {/* Aviso se o usuário ainda não está logado */}
          {!user && (
            <div className={styles.loginPromptBox}>
              <IconLock width="20" height="20" className={styles.loginPromptIcon} />
              <div>
                <strong>Acesso quase liberado!</strong> Para emitir seu Pix e vincular os 14 dias grátis à sua clínica, acesse ou crie sua conta.
              </div>
            </div>
          )}

          {checkoutError && (
            <div style={{ marginBottom: "1rem" }}>
              <p style={{ color: "#dc2626", fontSize: "0.875rem", margin: "0 0 0.5rem" }}>
                {checkoutError}
              </p>
              {!user && (
                <Link
                  to="/login"
                  style={{ color: "var(--primary)", fontSize: "0.85rem", textDecoration: "underline", fontWeight: 600 }}
                >
                  Clique aqui para entrar na sua conta →
                </Link>
              )}
            </div>
          )}

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span>Processando no Asaas...</span>
            ) : !user ? (
              <>
                <span>Entrar / Criar Conta para Liberar 14 Dias Grátis</span>
                <IconArrowRight width="18" height="18" />
              </>
            ) : (
              <>
                <span>
                  {billingType === "PIX"
                    ? "Gerar Pix com 14 Dias Grátis"
                    : billingType === "CREDIT_CARD"
                    ? "Cadastrar Cartão com 14 Dias Grátis"
                    : "Gerar Boleto com 14 Dias Grátis"}
                </span>
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
