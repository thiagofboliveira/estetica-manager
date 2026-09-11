import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import type { FeePayer, FinancialSettings, PaymentMethod, SplitBase } from "./api";
import { useUpdateFinancialSettings } from "./hooks";
import { toast } from "@/ui/ToastContext";

const schema = z.object({
  has_split: z.enum(["YES", "NO"]),
  split_clinic_percentage: z.string().refine((v) => {
    const n = Number(v);
    return !isNaN(n) && n >= 0 && n <= 100;
  }, "Percentual deve estar entre 0% e 100%"),
  split_base: z.enum(["GROSS", "NET_OF_FEE"]),
  fee_payer: z.enum(["PROFESSIONAL", "CLINIC"]),
  pix_fee_percentage: z.string().refine((v) => {
    const n = Number(v);
    return !isNaN(n) && n >= 0 && n <= 100;
  }, "Percentual deve estar entre 0% e 100%"),
  debit_card_fee_percentage: z.string().refine((v) => {
    const n = Number(v);
    return !isNaN(n) && n >= 0 && n <= 100;
  }, "Percentual deve estar entre 0% e 100%"),
  default_payment_method: z.enum(["PIX", "DEBIT", "CREDIT", "CASH", "TRANSFER"]),
  monthly_revenue_goal: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

type Props = {
  initial: FinancialSettings;
};

export function FinancialSettingsForm({ initial }: Props) {
  const updateSettings = useUpdateFinancialSettings();
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const initialHasSplit = Number(initial.split_clinic_percentage) > 0 ? "YES" : "NO";

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      has_split: initialHasSplit,
      split_clinic_percentage: initial.split_clinic_percentage ?? "0.00",
      split_base: initial.split_base ?? "GROSS",
      fee_payer: initial.fee_payer ?? "PROFESSIONAL",
      pix_fee_percentage: initial.pix_fee_percentage ?? "0.00",
      debit_card_fee_percentage: initial.debit_card_fee_percentage ?? "1.99",
      default_payment_method: initial.default_payment_method ?? "PIX",
      monthly_revenue_goal: initial.monthly_revenue_goal
        ? String(Number(initial.monthly_revenue_goal))
        : "",
    },
  });

  const hasSplit = watch("has_split");

  useEffect(() => {
    const sub = watch(() => setSaved(false));
    return () => sub.unsubscribe();
  }, [watch]);

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    setSaved(false);
    try {
      const cleanGoal = values.monthly_revenue_goal?.trim()
        ? values.monthly_revenue_goal.replace(/[^\d.,]/g, "").replace(",", ".")
        : null;

      await updateSettings.mutateAsync({
        split_clinic_percentage: values.has_split === "YES" ? values.split_clinic_percentage : "0.00",
        split_base: values.has_split === "YES" ? (values.split_base as SplitBase) : "GROSS",
        fee_payer: (values.fee_payer as FeePayer) ?? "PROFESSIONAL",
        pix_fee_percentage: values.pix_fee_percentage,
        debit_card_fee_percentage: values.debit_card_fee_percentage,
        default_payment_method: values.default_payment_method as PaymentMethod,
        monthly_revenue_goal: cleanGoal,
      });
      setSaved(true);
      toast.success("Configurações financeiras salvas com sucesso!");
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Erro ao salvar configurações financeiras.");
    }
  });

  return (
    <div className="settings-section">
      <form onSubmit={submit} noValidate className="form">
        <div style={{
          background: "#fffbeb",
          border: "1px solid #fde68a",
          borderRadius: "8px",
          padding: "12px 14px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}>
          <div>
            <strong style={{ fontSize: "0.85rem", color: "#92400e", display: "block" }}>
              💡 Não tem certeza das suas taxas ou modelo agora?
            </strong>
            <span style={{ fontSize: "0.78rem", color: "#78350f" }}>
              Preencha com os padrões médios de mercado (consultório próprio, Pix 0%, Débito 1.99%) e ajuste quando quiser.
            </span>
          </div>
          <button
            type="button"
            className="button button--secondary"
            style={{ fontSize: "0.8rem", padding: "6px 12px", minHeight: "34px" }}
            onClick={() => {
              setValue("has_split", "NO", { shouldDirty: true });
              setValue("split_clinic_percentage", "0.00", { shouldDirty: true });
              setValue("split_base", "GROSS", { shouldDirty: true });
              setValue("fee_payer", "PROFESSIONAL", { shouldDirty: true });
              setValue("pix_fee_percentage", "0.00", { shouldDirty: true });
              setValue("debit_card_fee_percentage", "1.99", { shouldDirty: true });
              setValue("default_payment_method", "PIX", { shouldDirty: true });
              toast.show("Padrões recomendados de mercado aplicados. Clique em Salvar.", "info");
            }}
          >
            Usar padrões recomendados
          </button>
        </div>

        <fieldset className="form__field">
          <legend>Modelo de Atendimento & Comissão</legend>
          <p className="form__hint">
            Defina se você atende com repasse para clínica ou em consultório próprio.
          </p>

          <label className="radio-label">
            <input
              type="radio"
              value="NO"
              {...register("has_split")}
              onChange={() => {
                setValue("has_split", "NO");
                setValue("split_clinic_percentage", "0.00");
              }}
            />
            <span>Consultório próprio ou aluguel fixo (sem comissão para clínica)</span>
          </label>

          <label className="radio-label">
            <input
              type="radio"
              value="YES"
              {...register("has_split")}
              onChange={() => {
                setValue("has_split", "YES");
                if (Number(watch("split_clinic_percentage")) === 0) {
                  setValue("split_clinic_percentage", "30.00");
                }
              }}
            />
            <span>Atendo em clínica parceira com comissão/split percentual</span>
          </label>
        </fieldset>

        {hasSplit === "YES" && (
          <div className="form__subgroup">
            <label className="form__field">
              <span>Comissão da clínica (%) *</span>
              <input
                {...register("split_clinic_percentage")}
                type="text"
                inputMode="decimal"
                placeholder="ex: 30.00"
              />
              {errors.split_clinic_percentage && (
                <span role="alert" className="form__error">
                  {errors.split_clinic_percentage.message}
                </span>
              )}
            </label>

            <fieldset className="form__field">
              <legend>Como a clínica calcula a comissão dela?</legend>
              <label className="radio-label">
                <input type="radio" value="GROSS" {...register("split_base")} />
                <span>Sobre o valor cheio (bruto cobrado do paciente)</span>
              </label>
              <label className="radio-label">
                <input type="radio" value="NET_OF_FEE" {...register("split_base")} />
                <span>Sobre o que sobra após descontar taxas de cartão/Pix</span>
              </label>
            </fieldset>

            <fieldset className="form__field">
              <legend>Quem arca com as taxas da maquininha/Pix?</legend>
              <label className="radio-label">
                <input type="radio" value="PROFESSIONAL" {...register("fee_payer")} />
                <span>Sai do meu bolso (profissional)</span>
              </label>
              <label className="radio-label">
                <input type="radio" value="CLINIC" {...register("fee_payer")} />
                <span>A clínica cobre / desconta da parte dela</span>
              </label>
            </fieldset>
          </div>
        )}

        <fieldset className="form__field">
          <legend>Taxas Padrão de Recebimento</legend>
          <p className="form__hint">
            Taxas médias cobradas pelo seu banco ou maquininha em pagamentos à vista.
          </p>

          <div className="form__row">
            <label className="form__field">
              <span>Taxa Pix (%)</span>
              <input
                {...register("pix_fee_percentage")}
                type="text"
                inputMode="decimal"
                placeholder="ex: 0.00"
              />
              {errors.pix_fee_percentage && (
                <span role="alert" className="form__error">
                  {errors.pix_fee_percentage.message}
                </span>
              )}
            </label>

            <label className="form__field">
              <span>Taxa Débito (%)</span>
              <input
                {...register("debit_card_fee_percentage")}
                type="text"
                inputMode="decimal"
                placeholder="ex: 1.99"
              />
              {errors.debit_card_fee_percentage && (
                <span role="alert" className="form__error">
                  {errors.debit_card_fee_percentage.message}
                </span>
              )}
            </label>
          </div>

          <label className="form__field">
            <span>Forma de pagamento padrão</span>
            <select {...register("default_payment_method")}>
              <option value="PIX">Pix</option>
              <option value="DEBIT">Cartão de Débito</option>
              <option value="CREDIT">Cartão de Crédito</option>
              <option value="CASH">Dinheiro</option>
              <option value="TRANSFER">Transferência</option>
            </select>
          </label>
        </fieldset>

        {/* Gamificação: Meta de Faturamento Mensal */}
        <fieldset
          id="meta-faturamento"
          className="form__field"
          style={{
            background: "#f0fdf4",
            border: "1.5px solid #86efac",
            borderRadius: "10px",
            padding: "16px 18px",
            marginTop: "12px",
            marginBottom: "12px",
          }}
        >
          <legend
            style={{
              fontSize: "0.95rem",
              fontWeight: 700,
              color: "#166534",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "0 8px",
              background: "#ffffff",
              border: "1px solid #bbf7d0",
              borderRadius: "6px",
            }}
          >
            <span>🎯 Meta de Faturamento Mensal</span>
          </legend>
          <p className="form__hint" style={{ color: "#15803d", marginTop: "4px", fontSize: "0.85rem", lineHeight: 1.4 }}>
            Defina quanto sua clínica almeja faturar a cada mês. Essa meta alimenta o termômetro de conquista, previsibilidade de caixa e as celebrações de metas batidas no Dashboard.
          </p>

          <div style={{ marginTop: "12px" }}>
            <label className="form__field" style={{ marginBottom: "8px" }}>
              <span style={{ fontWeight: 600, color: "#166534", fontSize: "0.9rem" }}>
                Valor da meta do mês (R$)
              </span>
              <div style={{ position: "relative", maxWidth: "280px" }}>
                <span
                  style={{
                    position: "absolute",
                    left: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "#6b7280",
                    fontWeight: 600,
                    fontSize: "0.9rem",
                    pointerEvents: "none",
                  }}
                >
                  R$
                </span>
                <input
                  {...register("monthly_revenue_goal")}
                  type="text"
                  inputMode="decimal"
                  placeholder="ex: 15000.00"
                  aria-label="Meta de faturamento mensal em reais"
                  style={{
                    paddingLeft: "42px",
                    fontWeight: 700,
                    fontSize: "1.05rem",
                    color: "#14532d",
                    border: "1.5px solid #86efac",
                    borderRadius: "6px",
                    width: "100%",
                  }}
                />
              </div>
            </label>

            {/* Sugestões Rápidas de Meta */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginTop: "10px" }}>
              <span style={{ fontSize: "0.78rem", color: "#166534", fontWeight: 600 }}>
                Sugestões rápidas:
              </span>
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
                  style={{
                    fontSize: "0.78rem",
                    padding: "4px 10px",
                    borderRadius: "6px",
                    border: "1px solid #86efac",
                    background: "#ffffff",
                    color: "#15803d",
                    cursor: "pointer",
                    fontWeight: 600,
                    transition: "all 0.15s ease",
                  }}
                  onClick={() => setValue("monthly_revenue_goal", sug.val, { shouldDirty: true })}
                >
                  {sug.label}
                </button>
              ))}
              <button
                type="button"
                style={{
                  fontSize: "0.78rem",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  border: "1px dashed #cbd5e1",
                  background: "transparent",
                  color: "#64748b",
                  cursor: "pointer",
                }}
                onClick={() => setValue("monthly_revenue_goal", "", { shouldDirty: true })}
              >
                Limpar meta
              </button>
            </div>
          </div>
        </fieldset>

        {serverError && (
          <p role="alert" className="form__error">
            {serverError}
          </p>
        )}

        {saved && !serverError && (
          <p role="status" className="form__success">
            Configurações salvas com sucesso.
          </p>
        )}

        <button type="submit" disabled={isSubmitting} className="tap-target">
          {isSubmitting ? "Salvando…" : "Salvar configurações financeiras"}
        </button>
      </form>
    </div>
  );
}
