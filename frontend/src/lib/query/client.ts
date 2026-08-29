import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/http/client";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Default CONSERVADOR: dinheiro é sempre stale. Refetch em foco é
      // o que faz ela ver o número certo ao voltar do WhatsApp para o app.
      staleTime: 0,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: true,
      refetchOnReconnect: true, // 4G instável no salão
      retry: (failureCount, err) => {
        const status = err instanceof ApiError ? err.status : undefined;
        if (status !== undefined && status >= 400 && status < 500) return false;
        return failureCount < 2;
      },
      retryDelay: (n) => Math.min(400 * 2 ** n, 3_000),
    },
    // Retry automático em mutation não-idempotente cria vendas duplicadas.
    // Ligar depois que o backend confirmar o contrato de idempotência (C-1).
    mutations: { retry: 0 },
  },
});

/** Perfis nomeados — use estes, não números soltos nos hooks. */
export const CACHE = {
  MONEY: { staleTime: 0, gcTime: 5 * 60_000 },
  CATALOG: { staleTime: 5 * 60_000, gcTime: 30 * 60_000 },
  SETTINGS: { staleTime: 10 * 60_000, gcTime: 60 * 60_000 },
  SEARCH: { staleTime: 30_000, gcTime: 60_000 },
} as const;
