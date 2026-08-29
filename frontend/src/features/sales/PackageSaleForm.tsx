import { useMemo, useState } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useProcedures } from "@/features/procedures/hooks";
import { formatBRL } from "@/lib/money/format";
import { ApiError } from "@/lib/http/client";
import { ZERO, money, mulQty, sub, sum, type Money } from "@/lib/money/money";
import { PatientPicker } from "./PatientPicker";
import { useCreateSale } from "./hooks";
import type { Patient } from "@/features/patients/api";
import type { Procedure } from "@/features/procedures/api";
import type { Sale } from "./api";

const lineSchema = z.object({
  procedureId: z.string().min(1, "Selecione o procedimento"),
  procedureName: z.string(),
  unitPrice: z.string(),
  quantity: z.string().refine((v) => Number(v) > 0, "Quantidade deve ser maior que zero"),
});

const schema = z.object({
  patientId: z.string().min(1, "Selecione a paciente"),
  lines: z.array(lineSchema).min(1, "Adicione pelo menos um item"),
  discount: z.string(),
  paymentMethod: z.enum(["PIX", "DEBIT", "CREDIT", "CASH", "TRANSFER"]),
  installments: z.string(),
});

type FormValues = z.infer<typeof schema>;

const emptyLine = { procedureId: "", procedureName: "", unitPrice: ZERO, quantity: "1" };

/**
 * F-014b, venda de pacote: múltiplos itens (procedimento + quantidade),
 * desconto único para a venda toda. Integrado com POST /sales real
 * (T-015) — o rateio do desconto por item e o lucro vêm da resposta da
 * API (discount_allocated, net_profit), nunca recalculados no cliente.
 * O preview antes de confirmar mostra só total/desconto/valor da venda
 * (soma simples, sem rateio) — não é uma alegação de lucro.
 */
export function PackageSaleForm() {
  const proceduresQuery = useProcedures();
  const createSale = useCreateSale();
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [confirmedSale, setConfirmedSale] = useState<Sale | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

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
  }

  const preview = useMemo(() => {
    try {
      const validLines = lines.filter((l) => l.procedureId);
      if (!validLines.length) return null;
      const lineTotals = validLines.map((l) => mulQty(money(l.unitPrice || ZERO), Number(l.quantity) || 0));
      const itemsTotal = sum(lineTotals);
      const grossAmount = sub(itemsTotal, money(discount || ZERO));
      return { itemsTotal, grossAmount };
    } catch {
      return null;
    }
  }, [lines, discount]);

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      const sale = await createSale.mutateAsync({
        patient_id: values.patientId,
        type: "PACKAGE",
        items: values.lines.map((l) => ({ procedure_id: l.procedureId, quantity: Number(l.quantity) })),
        discount_amount: values.discount || ZERO,
        payment_method: values.paymentMethod,
        installments: values.paymentMethod === "CREDIT" ? Number(values.installments) : 1,
      });
      setConfirmedSale(sale);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não consegui registrar a venda. Tenta de novo?");
    }
  });

  if (confirmedSale) {
    return (
      <div className="sale-confirm" role="status">
        <h2>Venda de pacote registrada</h2>
        {selectedPatient && <p>{selectedPatient.name}</p>}
        {confirmedSale.items.length > 1 && (
          <ul className="sale-form__line-discounts">
            {confirmedSale.items.map((item) => (
              <li key={item.id}>
                {lines.find((l) => l.procedureId === item.procedure_id)?.procedureName ?? item.procedure_id}
                : desconto rateado {formatBRL(money(item.discount_allocated))}
              </li>
            ))}
          </ul>
        )}
        <p>Total dos itens: {formatBRL(money(confirmedSale.items_total))}</p>
        <p>Desconto: {formatBRL(money(confirmedSale.discount_amount))}</p>
        <p>Valor da venda: {formatBRL(money(confirmedSale.gross_amount))}</p>
        <p>
          Lucro: <strong>{formatBRL(money(confirmedSale.net_profit))}</strong>
        </p>
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
          <input type="radio" value="DEBIT" {...register("paymentMethod")} /> Débito
        </label>
        <label>
          <input type="radio" value="CREDIT" {...register("paymentMethod")} /> Crédito
        </label>
        <label>
          <input type="radio" value="CASH" {...register("paymentMethod")} /> Dinheiro
        </label>
        <label>
          <input type="radio" value="TRANSFER" {...register("paymentMethod")} /> Transferência
        </label>
      </fieldset>

      {paymentMethod === "CREDIT" && (
        <label className="form__field">
          <span>Parcelas</span>
          <input {...register("installments")} type="number" min={1} max={12} />
        </label>
      )}

      {preview && (
        <div className="sale-form__preview">
          <p>Total dos itens: {formatBRL(preview.itemsTotal)}</p>
          <p>Valor da venda: {formatBRL(preview.grossAmount)}</p>
        </div>
      )}

      {serverError && (
        <p role="alert" className="form__error">
          {serverError}
        </p>
      )}

      <button type="submit" disabled={isSubmitting || createSale.isPending} className="tap-target">
        {createSale.isPending ? "Confirmando…" : "Confirmar venda"}
      </button>
    </form>
  );
}
