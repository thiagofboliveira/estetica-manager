import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { ZERO, type Money } from "@/lib/money/money";
import type { Modality, Procedure, ProcedureType } from "./api";
import { toast } from "@/ui/ToastContext";
import { SUGGESTED_PROCEDURE_PHOTOS, getProcedurePhoto } from "@/features/public-booking/procedureImages";

const schema = z.object({
  name: z.string().min(1, "Nome é obrigatório"),
  type: z.enum(["SERVICE", "PRODUCT"]),
  price: z.string().refine((v) => Number(v) > 0, "Preço deve ser maior que zero"),
  estimated_cost: z.string(),
  return_interval_days: z.string().optional(),
  default_modality: z.enum(["IN_PERSON", "REMOTE"]),
  is_invasive: z.boolean(),
  session_plan: z.enum(["SINGLE", "MULTIPLE"]),
  image_url: z.string().optional(),
});

export type ProcedureFormValues = z.infer<typeof schema>;

type Props = {
  initial?: Procedure;
  onSubmit: (values: ProcedureFormValues) => Promise<unknown>;
  submitLabel: string;
};

export function ProcedureForm({ initial, onSubmit, submitLabel }: Props) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    control,
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProcedureFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? "",
      type: (initial?.type ?? "SERVICE") as ProcedureType,
      price: initial?.price ?? ZERO,
      estimated_cost: initial?.estimated_cost ?? ZERO,
      return_interval_days: initial?.return_interval_days?.toString() ?? "",
      default_modality: (initial?.default_modality ?? "IN_PERSON") as Modality,
      is_invasive: initial?.is_invasive ?? false,
      session_plan: initial?.session_plan ?? "SINGLE",
      image_url: initial?.image_url ?? "",
    },
  });

  const type = watch("type");
  const name = watch("name");
  const currentImageUrl = watch("image_url");
  const activePreview = currentImageUrl?.trim() || (name ? getProcedurePhoto(name) : "");

  // Qualquer edição após salvar invalida o "Salvo com sucesso" —
  // senão a mensagem fica presa mesmo depois de mudar campos sem reenviar.
  useEffect(() => {
    const sub = watch(() => setSaved(false));
    return () => sub.unsubscribe();
  }, [watch]);

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    setSaved(false);
    try {
      await onSubmit(values);
      setSaved(true);
      toast.success("Procedimento salvo com sucesso!");
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Não consegui salvar. Tenta de novo?");
    }
  });

  return (
    <form onSubmit={submit} noValidate className="form">
      <label className="form__field">
        <span>Nome *</span>
        <input {...register("name")} />
        {errors.name && <span role="alert">{errors.name.message}</span>}
      </label>

      <fieldset className="form__field">
        <legend>Tipo</legend>
        <label>
          <input type="radio" value="SERVICE" {...register("type")} /> Serviço (procedimento)
        </label>
        <label>
          <input type="radio" value="PRODUCT" {...register("type")} /> Produto
        </label>
      </fieldset>

      <div className="form__field" style={{ marginTop: "8px", marginBottom: "8px" }}>
        <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>🖼️ Foto do Procedimento (Vitrine & Agendamento)</span>
        <p style={{ margin: "2px 0 8px", fontSize: "0.82rem", color: "#64748b" }}>
          Foto exibida para os clientes na agenda pública e catálogo.
        </p>

        <div style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
          {activePreview ? (
            <div style={{ position: "relative", flexShrink: 0 }}>
              <img
                src={activePreview}
                alt="Preview do procedimento"
                style={{
                  width: "110px",
                  height: "75px",
                  objectFit: "cover",
                  borderRadius: "8px",
                  border: "1px solid #e2e8f0",
                }}
              />
              {currentImageUrl && (
                <button
                  type="button"
                  onClick={() => setValue("image_url", "", { shouldDirty: true })}
                  style={{
                    position: "absolute",
                    top: "-6px",
                    right: "-6px",
                    background: "#ef4444",
                    color: "#fff",
                    border: "none",
                    borderRadius: "50%",
                    width: "20px",
                    height: "20px",
                    fontSize: "11px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  title="Remover foto personalizada (usar automática)"
                >
                  ✕
                </button>
              )}
            </div>
          ) : null}

          <div style={{ flex: 1 }}>
            <input
              {...register("image_url")}
              placeholder="Cole a URL de uma foto (https://...)"
              style={{ width: "100%", fontSize: "0.85rem" }}
            />
            {errors.image_url && (
              <span role="alert" style={{ color: "#ef4444", fontSize: "0.8rem", display: "block", marginTop: "2px" }}>
                {errors.image_url.message}
              </span>
            )}

            <div style={{ marginTop: "8px" }}>
              <span style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "4px" }}>
                Ou selecione uma foto da nossa biblioteca clínica:
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {SUGGESTED_PROCEDURE_PHOTOS.map((photo) => (
                  <button
                    key={photo.label}
                    type="button"
                    onClick={() => setValue("image_url", photo.url, { shouldDirty: true })}
                    style={{
                      fontSize: "0.74rem",
                      padding: "3px 8px",
                      borderRadius: "12px",
                      border: currentImageUrl === photo.url ? "1.5px solid #d97706" : "1px solid #cbd5e1",
                      background: currentImageUrl === photo.url ? "#fef3c7" : "#f8fafc",
                      color: currentImageUrl === photo.url ? "#92400e" : "#334155",
                      cursor: "pointer",
                    }}
                  >
                    {photo.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <label className="form__field">
        <span>Preço *</span>
        <Controller
          control={control}
          name="price"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Preço"
            />
          )}
        />
        {errors.price && <span role="alert">{errors.price.message}</span>}
      </label>

      <label className="form__field">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "4px" }}>
          <span>Custo estimado</span>
          <button
            type="button"
            className="button--text"
            style={{ fontSize: "0.78rem", color: "#b45309", cursor: "pointer", background: "none", border: "none", padding: "0 2px", textDecoration: "underline" }}
            onClick={() => {
              const p = Number(watch("price")) || 0;
              const defaultCost = p > 0 ? (p * 0.2).toFixed(2) : "30.00";
              setValue("estimated_cost", defaultCost as Money, { shouldDirty: true });
              toast.show(`Custo estimado em 20% (${defaultCost}).`, "info");
            }}
          >
            💡 Não sei agora (estimar 20% do preço)
          </button>
        </div>
        <Controller
          control={control}
          name="estimated_cost"
          render={({ field }) => (
            <CurrencyInput
              value={field.value as Money}
              onChange={(v) => field.onChange(v)}
              aria-label="Custo estimado"
            />
          )}
        />
        <span style={{ fontSize: "0.76rem", color: "#64748b" }}>
          Insumos e materiais consumidos na sessão. Você pode ajustar a qualquer momento.
        </span>
      </label>

      <fieldset className="form__field">
        <legend>Sessões</legend>
        <label>
          <input type="radio" value="SINGLE" {...register("session_plan")} /> Sessão única
        </label>
        <label>
          <input type="radio" value="MULTIPLE" {...register("session_plan")} /> Múltiplas sessões
        </label>
      </fieldset>

      <label className="form__field" style={{ flexDirection: "row", alignItems: "center", gap: "8px" }}>
        <input type="checkbox" {...register("is_invasive")} />
        <span>⚠️ Procedimento invasivo</span>
      </label>

      {type === "SERVICE" && (
        <>
          <fieldset className="form__field">
            <legend>Modalidade padrão</legend>
            <label>
              <input type="radio" value="IN_PERSON" {...register("default_modality")} /> 📍 Presencial (consultório)
            </label>
            <label>
              <input type="radio" value="REMOTE" {...register("default_modality")} /> 💻 Remoto / Videochamada
            </label>
          </fieldset>

          <label className="form__field">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "4px" }}>
              <span>Retorno recomendado (dias)</span>
              <button
                type="button"
                className="button--text"
                style={{ fontSize: "0.78rem", color: "#b45309", cursor: "pointer", background: "none", border: "none", padding: "0 2px", textDecoration: "underline" }}
                onClick={() => {
                  setValue("return_interval_days", "30", { shouldDirty: true });
                  toast.show("Retorno sugerido para 30 dias.", "info");
                }}
              >
                💡 Não sei agora (usar 30 dias)
              </button>
            </div>
            <input
              {...register("return_interval_days")}
              type="number"
              min={0}
              placeholder="ex: 30"
            />
            <span style={{ fontSize: "0.76rem", color: "#64748b" }}>
              Intervalo para alimentar a fila inteligente "Quem chamar hoje?".
            </span>
          </label>
        </>
      )}

      {serverError && (
        <p role="alert" className="form__error">
          {serverError}
        </p>
      )}

      {saved && !serverError && (
        <p role="status" className="form__success">
          Salvo com sucesso.
        </p>
      )}

      <button type="submit" disabled={isSubmitting} className="tap-target">
        {isSubmitting ? "Salvando…" : submitLabel}
      </button>
    </form>
  );
}
