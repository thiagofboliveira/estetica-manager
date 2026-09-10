import { useState } from "react";
import { IconTag, IconCheck } from "@/ui/icons";
import { validateCoupon, type BillingCycle, type CouponValidation } from "./billingApi";
import styles from "./CouponInput.module.css";

interface CouponInputProps {
  selectedCycle: BillingCycle;
  appliedCoupon: CouponValidation | null;
  onCouponApplied: (coupon: CouponValidation | null) => void;
}

export function CouponInput({
  selectedCycle,
  appliedCoupon,
  onCouponApplied,
}: CouponInputProps) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleApply() {
    if (!code.trim()) return;
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await validateCoupon(code, selectedCycle);
      if (res.is_valid) {
        onCouponApplied(res);
        setCode("");
      } else {
        setErrorMsg(res.message || "Cupom inválido ou não aplicável.");
      }
    } catch {
      setErrorMsg("Erro ao validar cupom. Verifique e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  function handleRemove() {
    onCouponApplied(null);
    setErrorMsg(null);
  }

  if (appliedCoupon) {
    return (
      <div className={styles.couponBox}>
        <div className={styles.appliedBadge}>
          <div className={styles.badgeContent}>
            <IconCheck width="16" height="16" />
            <span>
              Cupom <strong>{appliedCoupon.code}</strong> aplicado (economia de R${" "}
              {appliedCoupon.discount_amount})
            </span>
          </div>
          <button
            type="button"
            className={styles.removeBtn}
            onClick={handleRemove}
            title="Remover cupom"
          >
            Remover
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.couponBox}>
      <div className={styles.inputRow}>
        <div className={styles.inputWrapper}>
          <span className={styles.icon}>
            <IconTag width="16" height="16" />
          </span>
          <input
            type="text"
            className={styles.input}
            placeholder="Possui cupom? Ex: INAUGURACAO"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleApply();
              }
            }}
            disabled={loading}
          />
        </div>
        <button
          type="button"
          className={styles.applyBtn}
          onClick={handleApply}
          disabled={loading || !code.trim()}
        >
          {loading ? "Validando..." : "Aplicar"}
        </button>
      </div>
      {errorMsg && <p className={styles.errorText}>{errorMsg}</p>}
    </div>
  );
}
