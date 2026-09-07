import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/lib/http/client";
import { CurrencyInput } from "@/ui/CurrencyInput";
import { ZERO, type Money } from "@/lib/money/money";
import type { Modality, Procedure, ProcedureSupplyItem, ProcedureType } from "./api";
import { toast } from "@/ui/ToastContext";
import { SUGGESTED_PROCEDURE_PHOTOS, getProcedurePhoto } from "@/features/public-booking/procedureImages";
import { useSupplies } from "@/features/supplies/useSupplies";

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

export type ProcedureFormValues = z.infer<typeof schema> & {
  supplies?: ProcedureSupplyItem[];
};

type Props = {
  initial?: Procedure;
  onSubmit: (values: ProcedureFormValues) => Promise<unknown>;
  submitLabel: string;
};

export function ProcedureForm({ initial, onSubmit, submitLabel }: Props) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const { data: availableSupplies = [] } = useSupplies();
  const [suppliesList, setSuppliesList] = useState<ProcedureSupplyItem[]>(
    initial?.supplies ?? []
  );
  const [selectedSupplyId, setSelectedSupplyId] = useState("");
  const [supplyQty, setSupplyQty] = useState("1");

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

  useEffect(() => {
    if (initial?.supplies) {
      setSuppliesList(initial.supplies);
    }
  }, [initial?.supplies]);

  // Qualquer edição após salvar invalida o "Salvo com sucesso"
  useEffect(() => {
    const sub = watch(() => setSaved(false));
    return () => sub.unsubscribe();
  }, [watch]);

  const handleAddSupply = () => {
    if (!selectedSupplyId) return;
    const supply = availableSupplies.find((s) => s.id === selectedSupplyId);
    if (!supply) return;

    const qty = parseFloat(supplyQty) || 1;
    const existingIndex = suppliesList.findIndex((item) => item.supply_id === supply.id);

    if (existingIndex >= 0) {
      const updated = [...suppliesList];
      const newQty = Number(updated[existingIndex].quantity) + qty;
      updated[existingIndex] = {
        ...updated[existingIndex],
        quantity: newQty,
        subtotal_cost: supply.cost_price ? (Number(supply.cost_price) * newQty).toFixed(2) : undefined,
      };
      setSuppliesList(updated);
    } else {
      setSuppliesList([
        ...suppliesList,
        {
          supply_id: supply.id,
          quantity: qty,
          supply_name: supply.name,
          unit_measure: supply.unit_measure,
          cost_price: supply.cost_price ?? null,
          subtotal_cost: supply.cost_price ? (Number(supply.cost_price) * qty).toFixed(2) : undefined,
        },
      ]);
    }
    setSelectedSupplyId("");
    setSupplyQty("1");
    toast.success(`Insumo "${supply.name}" adicionado à ficha técnica!`);
  };

  const handleUpdateSupplyQty = (supplyId: string, newQty: number) => {
    if (newQty <= 0) {
      handleRemoveSupply(supplyId);
      return;
    }
    setSuppliesList((prev) =>
      prev.map((item) => {
        if (item.supply_id === supplyId) {
          const cost = Number(item.cost_price || 0);
          return {
            ...item,
            quantity: newQty,
            subtotal_cost: cost > 0 ? (cost * newQty).toFixed(2) : undefined,
          };
        }
        return item;
      })
    );
  };

  const handleRemoveSupply = (supplyId: string) => {
    setSuppliesList((prev) => prev.filter((item) => item.supply_id !== supplyId));
  };

  const totalSuppliesCost = suppliesList.reduce((acc, item) => {
    const cost = Number(item.cost_price || 0);
    const qty = Number(item.quantity || 0);
    return acc + cost * qty;
  }, 0);

  const priceVal = Number(watch("price") || 0);
  const currentCostVal = Number(watch("estimated_cost") || 0);
  const currentProfit = priceVal - currentCostVal;
  const currentMarginPct = priceVal > 0 ? Math.round((currentProfit / priceVal) * 100) : 0;

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    setSaved(false);
    try {
      await onSubmit({ ...values, supplies: suppliesList });
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

      {/* SEÇÃO DA FICHA TÉCNICA DE INSUMOS */}
      <div
        style={{
          marginTop: "12px",
          marginBottom: "16px",
          padding: "16px",
          background: "#f8fafc",
          borderRadius: "12px",
          border: "1.5px solid #e2e8f0",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "8px",
          }}
        >
          <div>
            <h3
              style={{
                margin: 0,
                fontSize: "0.98rem",
                fontWeight: 600,
                color: "#0f172a",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              🧪 Ficha Técnica do Procedimento (Baixa Automática)
            </h3>
            <p style={{ margin: "3px 0 0", fontSize: "0.82rem", color: "#64748b" }}>
              Insumos e doses que este procedimento consome. O sistema dará baixa no estoque automaticamente a cada sessão realizada ou venda.
            </p>
          </div>
          {suppliesList.length > 0 && totalSuppliesCost > 0 && (
            <button
              type="button"
              onClick={() => {
                setValue("estimated_cost", totalSuppliesCost.toFixed(2) as Money, { shouldDirty: true });
                toast.show(`Custo estimado atualizado para R$ ${totalSuppliesCost.toFixed(2)} com base na ficha!`, "info");
              }}
              style={{
                background: "#fef3c7",
                color: "#92400e",
                border: "1px solid #f59e0b",
                borderRadius: "6px",
                padding: "5px 12px",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              ✨ Usar custo da ficha (R$ {totalSuppliesCost.toFixed(2)})
            </button>
          )}
        </div>

        {/* Adicionar Insumo */}
        <div style={{ display: "flex", gap: "8px", marginTop: "14px", flexWrap: "wrap" }}>
          <select
            value={selectedSupplyId}
            onChange={(e) => setSelectedSupplyId(e.target.value)}
            style={{
              flex: "1 1 240px",
              padding: "8px 10px",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              fontSize: "0.85rem",
              background: "#fff",
            }}
          >
            <option value="">Selecione um insumo do estoque...</option>
            {availableSupplies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.unit_measure}) {s.cost_price ? `• Custo: R$ ${Number(s.cost_price).toFixed(2)}` : ""} • Saldo: {s.current_stock}
              </option>
            ))}
          </select>

          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <span style={{ fontSize: "0.8rem", color: "#475569" }}>Dose/Qtd:</span>
            <input
              type="number"
              step="any"
              min="0.01"
              value={supplyQty}
              onChange={(e) => setSupplyQty(e.target.value)}
              style={{
                width: "80px",
                padding: "8px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                fontSize: "0.85rem",
                background: "#fff",
              }}
            />
          </div>

          <button
            type="button"
            onClick={handleAddSupply}
            disabled={!selectedSupplyId}
            style={{
              padding: "8px 14px",
              background: selectedSupplyId ? "#0f766e" : "#94a3b8",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              fontSize: "0.85rem",
              fontWeight: 500,
              cursor: selectedSupplyId ? "pointer" : "not-allowed",
            }}
          >
            + Adicionar
          </button>
        </div>

        {/* Lista de Insumos da Ficha */}
        <div style={{ marginTop: "12px" }}>
          {suppliesList.length === 0 ? (
            <div
              style={{
                padding: "14px",
                background: "#fff",
                borderRadius: "8px",
                border: "1px dashed #cbd5e1",
                textAlign: "center",
                fontSize: "0.82rem",
                color: "#64748b",
              }}
            >
              Nenhum insumo vinculado ainda. Selecione um insumo acima para automatizar o controle de estoque e custo real.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {suppliesList.map((item) => {
                const supply = availableSupplies.find((s) => s.id === item.supply_id);
                const name = item.supply_name || supply?.name || "Insumo";
                const unit = item.unit_measure || supply?.unit_measure || "UN";
                const unitCost = Number(item.cost_price || supply?.cost_price || 0);
                const subtotal = unitCost * Number(item.quantity);

                return (
                  <div
                    key={item.supply_id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      background: "#fff",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      border: "1px solid #e2e8f0",
                      fontSize: "0.85rem",
                      gap: "8px",
                      flexWrap: "wrap",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: "1 1 200px" }}>
                      <span style={{ fontWeight: 600, color: "#1e293b" }}>{name}</span>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          background: "#f1f5f9",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          color: "#475569",
                          fontWeight: 500,
                        }}
                      >
                        {unit}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <span style={{ fontSize: "0.78rem", color: "#64748b" }}>Qtd:</span>
                        <input
                          type="number"
                          step="any"
                          value={item.quantity}
                          onChange={(e) => handleUpdateSupplyQty(item.supply_id, parseFloat(e.target.value) || 0)}
                          style={{
                            width: "65px",
                            padding: "4px 6px",
                            fontSize: "0.82rem",
                            borderRadius: "4px",
                            border: "1px solid #cbd5e1",
                          }}
                        />
                      </div>

                      <div style={{ textAlign: "right", minWidth: "90px" }}>
                        <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#0f172a" }}>
                          R$ {subtotal.toFixed(2)}
                        </div>
                        {unitCost > 0 && (
                          <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                            R$ {unitCost.toFixed(2)} / {unit}
                          </div>
                        )}
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRemoveSupply(item.supply_id)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#ef4444",
                          cursor: "pointer",
                          padding: "4px",
                          fontSize: "1rem",
                        }}
                        title="Remover da ficha técnica"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                );
              })}

              {/* Barra de Lucratividade em Tempo Real */}
              <div
                style={{
                  marginTop: "8px",
                  padding: "10px 14px",
                  background: "#f0fdf4",
                  borderRadius: "8px",
                  border: "1px solid #bbf7d0",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "8px",
                  fontSize: "0.85rem",
                }}
              >
                <div>
                  <span style={{ color: "#166534", fontWeight: 600 }}>Custo Total em Insumos: </span>
                  <span style={{ color: "#15803d", fontWeight: 700 }}>R$ {totalSuppliesCost.toFixed(2)}</span>
                </div>
                {priceVal > 0 && (
                  <div>
                    <span style={{ color: "#166534" }}>Margem Bruta Estimada: </span>
                    <span
                      style={{
                        color: currentMarginPct >= 50 ? "#15803d" : "#b45309",
                        fontWeight: 700,
                      }}
                    >
                      {currentMarginPct}% (R$ {currentProfit.toFixed(2)} de lucro)
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

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
