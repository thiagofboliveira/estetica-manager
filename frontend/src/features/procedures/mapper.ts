import { money, ZERO } from "@/lib/money/money";
import type { ProcedureFormValues } from "./ProcedureForm";

export function toProcedurePayload(values: ProcedureFormValues) {
  const returnInterval =
    values.type === "PRODUCT" || !values.return_interval_days
      ? null
      : parseInt(String(values.return_interval_days), 10);

  return {
    name: values.name.trim(),
    type: values.type,
    price: money(values.price),
    estimated_cost: money(values.estimated_cost || ZERO),
    return_interval_days:
      returnInterval !== null && !isNaN(returnInterval) && returnInterval >= 0
        ? returnInterval
        : null,
    default_modality: values.default_modality,
    is_invasive: values.is_invasive,
    session_plan: values.session_plan,
    image_url: values.image_url?.trim() ? values.image_url.trim() : null,
    supplies: (values.supplies ?? []).map((s) => ({
      supply_id: s.supply_id,
      quantity: Number(s.quantity) > 0 ? Number(s.quantity) : 1,
    })),
  };
}
