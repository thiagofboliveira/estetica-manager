import { useMemo, useState } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useProcedures } from "@/features/procedures/hooks";
import { formatBRL } from "@/lib/money/format";
import { ZERO, money, type Money } from "@/lib/money/money";
import { allocateDiscountForDisplay, estimatePackageProfit, type PaymentMethod } from "./prototypeMath";
import { PatientPicker } from "./PatientPicker";
import type { Patient } from "@/features/patients/api";
import type { Procedure } from "@/features/procedures/api";

const lineSchema = z.object({
  procedureId: z.string().min(1, "Selecione o procedimento"),
  procedureName: z.string(),
  unitPrice: z.string(),
  unitCost: z.string(),
  quantity: z.string().refine((v) => Number(v) > 0, "Quantidade deve ser maior que zero"),
});

const schema = z.object({
  patientId: z.string().min(1, "Selecione a paciente"),
  lines: z.array(lineSchema).min(1, "Adicione pelo menos um item"),
  discount: z.string(),
  paymentMethod: z.enum(["PIX", "CARD"]),
  installments: z.string(),
});

type FormValues = z.infer<typeof schema>;

const emptyLine = { procedureId: "", procedureName: "", unitPrice: ZERO, unitCost: ZERO, quantity: "1" };

/**
 * PROTÓTIPO — F-014b. Venda de pacote: múltiplos itens (procedimento +
 * quantidade), desconto único rateado por item para exibição (MVP v6
 * §11.5). Separada da venda avulsa (F-014) para não atrasá-la — ver
 * frontend/BACKLOG.md F-014b. Sem chamada de API.
 */
export function PackageSaleForm({ onConfirm }: { onConfirm: () => Promise<void> }) {
  const proceduresQuery = useProcedures();
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const {
    register,
    control,
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      patientId: "",
      lines: [emptyLine],
      discount: ZERO,
      paymentMethod: "PIX",
      installments: "1",
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "lines" });

  const lines = watch("lines");
  const discount = watch("discount");
  const paymentMethod = watch("paymentMethod");

  function handlePickProcedure(index: number, procedure: Procedure) {
    setValue(`lines.${index}.procedureId`, procedure.id);
    setValue(`lines.${index}.procedureName`, procedure.name);
    setValue(`lines.${index}.unitPrice`, procedure.price as Money);
    setValue(`lines.${index}.unitCost`, procedure.estimated_cost as Money);
  }

  const preview = useMemo(() => {
    try {
      const parsedLines = lines
        .filter((l) => l.procedureId)
        .map((l) => ({
          unitPrice: money(l.unitPrice || ZERO),
          unitCost: money(l.unitCost || ZERO),
          quantity: Number(l.quantity) || 0,
        }));
      if (!parsedLines.length) return null;
      const result = estimatePackageProfit({
        lines: parsedLines,
        discount: money(discount || ZERO),
        paymentMethod: paymentMethod as PaymentMethod,
      });
      const lineTotals = parsedLines.map((l) => money((Number(l.unitPrice) * l.quantity).toFixed(2)));
      const perLineDiscount = allocateDiscountForDisplay(lineTotals, result.discount);
      return { ...result, perLineDiscount };
    } catch {
      return null;
    }
  }, [lines, discount, paymentMethod]);

  const submit = handleSubmit(async () => {
    setConfirming(true);
    try {
      await onConfirm();
      setConfirmed(true);
    } finally {
      setConfirming(false);
    }
  });

  if (confirmed) {
    return (
      <div className="sale-confirm" role="status">
        <h2>Venda de pacote registrada</h2>
        {selectedPatient && <p>{selectedPatient.name}</p>}
        {preview && (
          <>
            <p>Total dos itens: {formatBRL(preview.itemsTotal)}</p>
            <p>Desconto: {formatBRL(preview.discount)}</p>
            <p>Valor da venda: {formatBRL(preview.grossAmount)}</p>
            <p>
              Lucro estimado: <strong>{formatBRL(preview.profit)}</strong>
            </p>
            <p className="sale-confirm__disclaimer">
              Estimativa de protótipo — o lucro real vem do backend quando a venda estiver
              integrada (T-015/T-018).
            </p>
          </>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="form">
      <label className="form__field">
        <span>Paciente *</span>
        <PatientPicker
          selected={selectedPatient}
          onSelect={(p) => {
            setSelectedPatient(p);
            setValue("patientId", p.id);
          }}
          onClear={() => {
            setSelectedPatient(null);
            setValue("patientId", "");
          }}
        />
        {errors.patientId && <span role="alert">{errors.patientId.message}</span>}
      </label>

      <fieldset className="form__field">
        <legend>Itens do pacote</legend>
        <AsyncBoundary
          query={proceduresQuery}
          skeleton={<p>Carregando…</p>}
          empty={<p>Nenhum procedimento cadastrado.</p>}
        >
          {(procedures) => (
            <>
              {fields.map((field, index) => (
                <div key={field.id} className="sale-form__line">
                  <select
                    value={lines[index]?.procedureId ?? ""}
                    onChange={(e) => {
                      const proc = procedures.find((p) => p.id === e.target.value);
                      if (proc) handlePickProcedure(index, proc);
                    }}
                  >
                    <option value="">Selecione…</option>
                    {procedures.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>

                  <input
                    {...register(`lines.${index}.quantity`)}
                    type="number"
                    min={1}
                    aria-label="Quantidade"
                    className="sale-form__qty"
                  />

                  <Controller
                    control={control}
                    name={`lines.${index}.unitPrice`}
                    render={({ field: f }) => (
                      <CurrencyInput
                        value={f.value as Money}
                        onChange={f.onChange}
                        aria-label={`Valor unitário do item ${index + 1}`}
                      />
                    )}
                  />

                  {fields.length > 1 && (
                    <button type="button" className="tap-target" onClick={() => remove(index)}>
                      Remover
                    </button>
                  )}
                  {errors.lines?.[index]?.procedureId && (
                    <span role="alert">{errors.lines[index]?.procedureId?.message}</span>
                  )}
                </div>
              ))}
              <button type="button" className="tap-target" onClick={() => append(emptyLine)}>
                + Adicionar item
              </button>
            </>
          )}
        </AsyncBoundary>
      </fieldset>

      <label className="form__field">
        <span>Desconto</span>
        <Controller
          control={control}
          name="discount"
          render={({ field }) => (
            <CurrencyInput value={field.value as Money} onChange={field.onChange} aria-label="Desconto" />
          )}
        />
      </label>

      <fieldset className="form__field">
        <legend>Forma de pagamento</legend>
        <label>
          <input type="radio" value="PIX" {...register("paymentMethod")} /> Pix
        </label>
        <label>
          <input type="radio" value="CARD" {...register("paymentMethod")} /> Cartão
        </label>
      </fieldset>

      {paymentMethod === "CARD" && (
        <label className="form__field">
          <span>Parcelas</span>
          <input {...register("installments")} type="number" min={1} max={12} />
        </label>
      )}

      {preview && (
        <div className="sale-form__preview">
          {preview.perLineDiscount.length > 1 && (
            <ul className="sale-form__line-discounts">
              {preview.perLineDiscount.map((d, i) => (
                <li key={i}>
                  {lines[i]?.procedureName || `Item ${i + 1}`}: desconto rateado {formatBRL(d)}
                </li>
              ))}
            </ul>
          )}
          <p>Total dos itens: {formatBRL(preview.itemsTotal)}</p>
          <p>Desconto: {formatBRL(preview.discount)}</p>
          <p>Valor da venda: {formatBRL(preview.grossAmount)}</p>
          <p>
            Lucro estimado: <strong>{formatBRL(preview.profit)}</strong>
          </p>
        </div>
      )}

      <button type="submit" disabled={isSubmitting || confirming} className="tap-target">
        {confirming ? "Confirmando…" : "Confirmar venda"}
      </button>
    </form>
  );
}
