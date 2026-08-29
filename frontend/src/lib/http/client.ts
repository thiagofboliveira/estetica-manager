import { getSessionToken, refreshSessionToken, signOutSession } from "@/lib/auth/session";

const BASE = import.meta.env.VITE_API_URL;

export class ApiError extends Error {
  status: number;
  code: string | undefined;
  details: unknown;

  constructor(status: number, code: string | undefined, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

type Opts = RequestInit & { headers?: Record<string, string> };

/** Deduplica refresh concorrentes: 5 queries paralelas dão 1 refresh, não 5. */
let refreshing: Promise<string | null> | null = null;
async function freshToken(force = false): Promise<string | null> {
  if (!force) {
    const token = await getSessionToken();
    if (token) return token;
  }
  refreshing ??= refreshSessionToken().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

async function request<T>(path: string, opts: Opts = {}, isRetry = false): Promise<T> {
  const token = await freshToken();

  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...opts.headers,
    },
  });

  if (res.status === 401 && !isRetry) {
    // Uma única tentativa de refresh forçado. Se falhar, é logout de verdade.
    const renewed = await freshToken(true);
    if (renewed) return request<T>(path, opts, true);
    await signOutSession();
    // Guarda o destino: perder o form de venda meio preenchido mata os 30 segundos.
    sessionStorage.setItem("returnTo", location.pathname + location.search);
    location.assign("/login");
    throw new ApiError(401, "UNAUTHENTICATED", "Sessão expirada");
  }

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    // FastAPI's default shape é {"detail": "..."} (HTTPException) ou
    // {"detail": [...]} (erro de validação 422) — nunca `message`.
    const detail = typeof body.detail === "string" ? body.detail : undefined;
    throw new ApiError(
      res.status,
      body.code,
      body.message ?? detail ?? "Não consegui salvar. Tenta de novo?",
      body.details ?? body.detail,
    );
  }

  // Valores monetários chegam como string e assim ficam — nunca reviver
  // o JSON convertendo para number aqui.
  return body as T;
}

export const api = {
  get: <T>(p: string, o?: Opts) => request<T>(p, { ...o, method: "GET" }),
  post: <T>(p: string, b: unknown, o?: Opts) =>
    request<T>(p, { ...o, method: "POST", body: JSON.stringify(b) }),
  patch: <T>(p: string, b: unknown, o?: Opts) =>
    request<T>(p, { ...o, method: "PATCH", body: JSON.stringify(b) }),
  del: <T>(p: string, o?: Opts) => request<T>(p, { ...o, method: "DELETE" }),
};
