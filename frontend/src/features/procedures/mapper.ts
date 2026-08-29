import { money, ZERO } from "@/lib/money/money";
import type { ProcedureFormValues } from "./ProcedureForm";

export function toProcedurePayload(values: ProcedureFormValues) {
  return {
    name: values.name,
    type: values.type,
    price: money(values.price),
    estimated_cost: money(values.estimated_cost || ZERO),
    return_interval_days:
      values.type === "PRODUCT" || !values.return_interval_days
        ? null
        : Number(values.return_interval_days),
  };
}
