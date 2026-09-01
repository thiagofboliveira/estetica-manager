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
import { toast } from "@/ui/ToastContext";
import { PatientPicker } from "./PatientPicker";
import { useCreateSale } from "./hooks";
import type { Patient } from "@/features/patients/api";
import type { Procedure } from "@/features/procedures/api";
import type { Sale } from "./api";

import { Link, useSearchParams } from "react-router-dom";
import { usePatient } from "@/features/patients/hooks";

const lineSchema = z.object({
  procedureId: z.string().min(1, "Selecione o procedimento"),
  procedureName: z.string(),
  unitPrice: z.string(),
  quantity: z.string().refine((v) => Number(v) > 0, "Quantidade deve ser maior que zero"),
});

const schema = z
  .object({
    patientId: z.string().min(1, "Selecione a paciente"),
    lines: z.array(lineSchema).min(1, "Adicione pelo menos um item"),
    discount: z.string(),
    paymentMethod: z.enum(["PIX", "DEBIT", "CREDIT", "CASH", "TRANSFER"]),
    installments: z.string(),
  })
  .refine(
    (data) => {
      try {
        const validLines = data.lines.filter((l) => l.procedureId);
        if (!validLines.length) return true;
        const lineTotals = validLines.map((l) =>
          mulQty(money(l.unitPrice || ZERO), Number(l.quantity) || 0)
        );
        const itemsTotal = sum(lineTotals);
        const disc = money(data.discount || ZERO);
        return Number(disc) <= Number(itemsTotal);
      } catch {
        return true;
      }
    },
    {
      message: "O desconto não pode ser maior que o total dos itens",
      path: ["discount"],
    }
  );

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
  const [searchParams] = useSearchParams();
  const patientIdParam = searchParams.get("patient_id");
  const preloadedPatientQuery = usePatient(patientIdParam || "");

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

  useMemo(() => {
    if (preloadedPatientQuery.data && !selectedPatient) {
      setSelectedPatient(preloadedPatientQuery.data);
      setValue("patientId", preloadedPatientQuery.data.id);
    }
  }, [preloadedPatientQuery.data, selectedPatient, setValue]);

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

  const submit = handleSubmit(
    async (values) => {
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
        toast.success("Venda de pacote registrada com sucesso!");
      } catch (e) {
        setServerError(e instanceof ApiError ? e.message : "Não consegui registrar a venda. Tenta de novo?");
      }
    },
    () => {
      toast.show("Por favor, selecione a paciente e os procedimentos do pacote antes de confirmar.", "error");
    }
  );

  if (confirmedSale) {
    return (
      <div className="sale-confirm" role="status" style={{ padding: "24px", backgroundColor: "#f8fafc", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ margin: 0, color: "#0f172a" }}>Venda de pacote registrada com sucesso!</h2>
          <span className="badge badge--accent" style={{ backgroundColor: "#fef3c7", color: "#92400e", padding: "6px 12px", borderRadius: "20px", fontWeight: "600" }} title="Sessões futuras ainda a serem realizadas">
            🟡 Lucro Provisório
          </span>
        </div>
        {selectedPatient && (
          <p style={{ fontSize: "15px", color: "#334155", marginBottom: "8px" }}>
            <strong>Paciente:</strong> {selectedPatient.name}
          </p>
        )}
        {confirmedSale.items.length > 1 && (
          <ul className="sale-form__line-discounts" style={{ margin: "12px 0", paddingLeft: "20px", color: "#475569" }}>
            {confirmedSale.items.map((item) => (
              <li key={item.id}>
                {lines.find((l) => l.procedureId === item.procedure_id)?.procedureName ?? item.procedure_id}
                : desconto rateado {formatBRL(money(item.discount_allocated))}
              </li>
            ))}
          </ul>
        )}
        <p style={{ fontSize: "15px", color: "#334155", marginBottom: "6px" }}>
          <strong>Total dos Itens:</strong> {formatBRL(money(confirmedSale.items_total))}
        </p>
        {Number(money(confirmedSale.discount_amount)) > 0 && (
          <p style={{ fontSize: "15px", color: "#dc2626", marginBottom: "6px" }}>
            <strong>Desconto Aplicado:</strong> -{formatBRL(money(confirmedSale.discount_amount))}
          </p>
        )}
        <p style={{ fontSize: "15px", color: "#334155", marginBottom: "6px" }}>
          <strong>Valor Final:</strong> {formatBRL(money(confirmedSale.gross_amount))}
        </p>
        <p style={{ fontSize: "16px", color: "#15803d", marginBottom: "20px" }}>
          <strong>Lucro Líquido Provisório:</strong> {formatBRL(money(confirmedSale.net_profit))}
        </p>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginTop: "16px" }}>
          <button
            type="button"
            className="button tap-target"
            onClick={() => {
              setConfirmedSale(null);
              setSelectedPatient(null);
              setValue("patientId", "");
              setValue("lines", [emptyLine]);
              setValue("discount", ZERO);
            }}
          >
            + Registrar outro pacote
          </button>
          <Link to="/agenda" className="button button--secondary tap-target">
            📅 Agendar Sessões na Agenda
          </Link>
          <Link to="/dashboard" className="button button--secondary tap-target">
            📊 Ir para o Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="form">
      <div className="form__field">
        <label htmlFor="patient-select" style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-h)", marginBottom: "4px", display: "block" }}>
          Paciente *
        </label>
        <PatientPicker
          selected={selectedPatient}
          onSelect={(p) => {
            setSelectedPatient(p);
            setValue("patientId", p.id, { shouldValidate: true });
          }}
          onClear={() => {
            setSelectedPatient(null);
            setValue("patientId", "", { shouldValidate: true });
          }}
        />
        {errors.patientId && (
          <span role="alert" className="form__error" style={{ color: "#dc2626", fontWeight: "600", fontSize: "13px", marginTop: "4px", display: "block" }}>
            {errors.patientId.message}
          </span>
        )}
      </div>

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
