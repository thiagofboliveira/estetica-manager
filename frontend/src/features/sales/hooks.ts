import { useMutation, useQuery } from "@tanstack/react-query";
import { useRef } from "react";
import { qk } from "@/lib/query/keys";
import { invalidateAfterSale } from "@/lib/query/invalidation";
import { salesApi, type SaleCorrectInput, type SaleCreateInput } from "./api";

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

export function useSale(id: string) {
  return useQuery({
    queryKey: qk.saleDetail(id),
    queryFn: () => salesApi.get(id),
    enabled: !!id,
  });
}

// F-014d/T-017: corrigir é estornar + criar venda nova (id diferente).
// Sem idempotency-key própria porque o backend usa `reason` obrigatório
// e um segundo clique acidental cairia em 409 (venda já estornada), não
// numa duplicata silenciosa — risco menor que o de F-014a.
export function useCorrectSale(id: string) {
  return useMutation({
    mutationFn: (payload: SaleCorrectInput) => salesApi.correct(id, payload),
    onSuccess: async (sale) => {
      await invalidateAfterSale(sale.patient_id);
    },
  });
}
