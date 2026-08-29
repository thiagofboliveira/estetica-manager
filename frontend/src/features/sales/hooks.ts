import { useMutation } from "@tanstack/react-query";
import { useRef } from "react";
import { invalidateAfterSale } from "@/lib/query/invalidation";
import { salesApi, type SaleCreateInput } from "./api";

/**
 * Idempotency-Key nasce ao montar o form (useRef), sobrevive a
 * re-render, retry e duplo-toque. Só troca depois de sucesso
 * confirmado — ver ENGENHARIA.md "Idempotency key" e F-014a.
 */
export function useCreateSale() {
  const idemKey = useRef(crypto.randomUUID());

  return useMutation({
    mutationFn: (input: SaleCreateInput) => salesApi.create(input, idemKey.current),
    onSuccess: async (sale) => {
      idemKey.current = crypto.randomUUID();
      await invalidateAfterSale(sale.patient_id);
    },
  });
}
