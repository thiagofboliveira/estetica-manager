import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import type { FeePayer, FinancialSettings, PaymentMethod, SplitBase } from "./api";
import { useUpdateFinancialSettings } from "./hooks";
import { PaymentFeeRulesManager } from "./PaymentFeeRulesManager";

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
      await updateSettings.mutateAsync({
        split_clinic_percentage: values.has_split === "YES" ? values.split_clinic_percentage : "0.00",
        split_base: values.has_split === "YES" ? (values.split_base as SplitBase) : "GROSS",
        fee_payer: (values.fee_payer as FeePayer) ?? "PROFESSIONAL",
        pix_fee_percentage: values.pix_fee_percentage,
        debit_card_fee_percentage: values.debit_card_fee_percentage,
        default_payment_method: values.default_payment_method as PaymentMethod,
      });
      setSaved(true);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Erro ao salvar configurações financeiras.");
    }
  });

  return (
    <div className="settings-section">
      <form onSubmit={submit} noValidate className="form">
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

      <hr className="settings-divider" />

      <PaymentFeeRulesManager />
    </div>
  );
}
