/**
 * Fonte única do access_token da sessão. Duas implementações:
 *
 * - dev-auth: VITE_DEV_AUTH=true chama POST /dev/login do backend
 *   (só existe quando o backend está com ENV=development), sem Supabase.
 *   Existe apenas para desenvolvimento local sem projeto Supabase — ver
 *   frontend/BACKLOG.md F-001a.
 * - supabase: caminho de produção, inalterado.
 *
 * client.ts (o HTTP client) não sabe qual dos dois está ativo — só
 * chama getSessionToken/refreshSessionToken/signOutSession.
 */

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === "true";
// /dev/login vive na raiz do app FastAPI, fora do prefixo /api/v1
// (ver backend/app/main.py) — não usar VITE_API_URL aqui.
const API_ROOT = import.meta.env.VITE_API_URL.replace(/\/api\/v1\/?$/, "");
const DEV_TOKEN_KEY = "estetica.dev-auth.token";

export async function devLogin(email?: string, password?: string): Promise<string | null> {
  const res = await fetch(`${API_ROOT}/dev/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(email ? { email, password } : {}),
  });
  if (!res.ok) return null;
  const body = (await res.json()) as { access_token: string };
  sessionStorage.setItem(DEV_TOKEN_KEY, body.access_token);
  return body.access_token;
}

export async function getSessionToken(): Promise<string | null> {
  if (DEV_AUTH) {
    return sessionStorage.getItem(DEV_TOKEN_KEY) ?? devLogin();
  }
  const { supabase } = await import("./supabase");
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function refreshSessionToken(): Promise<string | null> {
  if (DEV_AUTH) {
    // Token dev dura 24h (ver backend/app/main.py) — "refresh" é só pedir outro.
    return devLogin();
  }
  const { supabase } = await import("./supabase");
  const { data } = await supabase.auth.refreshSession();
  return data.session?.access_token ?? null;
}

export async function signOutSession(): Promise<void> {
  if (DEV_AUTH) {
    sessionStorage.removeItem(DEV_TOKEN_KEY);
    return;
  }
  const { supabase } = await import("./supabase");
  await supabase.auth.signOut();
}
