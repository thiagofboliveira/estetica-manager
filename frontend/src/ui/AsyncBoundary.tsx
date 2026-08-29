import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";
import { ApiError } from "@/lib/http/client";

type Props<T> = {
  query: UseQueryResult<T>;
  skeleton: ReactNode;
  empty: ReactNode;
  isEmpty?: (data: T) => boolean;
  children: (data: T) => ReactNode;
};

export function AsyncBoundary<T>({ query, skeleton, empty, isEmpty, children }: Props<T>) {
  const { data, isPending, isError, error, refetch, isFetching } = query;

  // isPending: primeira carga sem dado. Refetch com dado antigo mostra
  // os dados, não o skeleton — ela não quer ver a tela desmontar ao
  // voltar do WhatsApp.
  if (isPending) return <>{skeleton}</>;

  if (isError) {
    const e = error instanceof ApiError ? error : undefined;
    const offline = !navigator.onLine || e?.status === 0;
    return (
      <div role="alert" className="state state--error">
        <p>
          {offline
            ? "Sem internet agora. Seus dados estão salvos."
            : (e?.message ?? "Algo deu errado.")}
        </p>
        <button onClick={() => refetch()} disabled={isFetching} className="tap-target">
          {isFetching ? "Tentando…" : "Tentar de novo"}
        </button>
      </div>
    );
  }

  const isEmptyData = isEmpty
    ? isEmpty(data)
    : Array.isArray(data)
      ? data.length === 0
      : data == null;

  if (isEmptyData) return <>{empty}</>;

  return (
    <>
      {isFetching && <div className="refetch-bar" aria-hidden />}
      {children(data)}
    </>
  );
}
