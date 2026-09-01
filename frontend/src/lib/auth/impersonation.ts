/**
 * Impersonação de usuário — só disponível em dev com VITE_DEV_AUTH=true.
 *
 * Fluxo:
 *  1. Super Admin clica em "Entrar como X"
 *  2. O token atual (superadmin) é salvo em sessionStorage como "token de retorno"
 *  3. Um novo token de impersonação é obtido via POST /dev/impersonate/{user_id}
 *  4. Esse novo token vira a sessão ativa
 *  5. Um banner de aviso aparece em toda a app
 *  6. Ao clicar "Sair da visão", o token original é restaurado
 */

const IMPERSONATION_KEY = "estetica.impersonation.token";
const ORIGINAL_TOKEN_KEY = "estetica.impersonation.originalToken";
const ORIGINAL_USER_KEY = "estetica.impersonation.originalUser";
const DEV_TOKEN_KEY = "estetica.dev-auth.token";
const API_ROOT = import.meta.env.VITE_API_URL.replace(/\/api\/v1\/?$/, "");

export interface ImpersonationState {
  isImpersonating: boolean;
  originalUserName: string | null;
  targetUserName: string | null;
}

export function getImpersonationState(): ImpersonationState {
  const imp = sessionStorage.getItem(IMPERSONATION_KEY);
  const originalUser = sessionStorage.getItem(ORIGINAL_USER_KEY);
  if (!imp) return { isImpersonating: false, originalUserName: null, targetUserName: null };
  try {
    const data = JSON.parse(imp) as { targetName: string };
    return {
      isImpersonating: true,
      originalUserName: originalUser,
      targetUserName: data.targetName,
    };
  } catch {
    return { isImpersonating: false, originalUserName: null, targetUserName: null };
  }
}

export async function startImpersonation(
  userId: string,
  targetName: string,
  originalUserName: string,
): Promise<void> {
  const currentToken = sessionStorage.getItem(DEV_TOKEN_KEY);
  if (!currentToken) throw new Error("Nenhuma sessão ativa para salvar");

  const res = await fetch(`${API_ROOT}/dev/impersonate/${userId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${currentToken}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Falha ao iniciar impersonação");
  }

  const body = (await res.json()) as { access_token: string };

  // Salva o token original e os metadados antes de trocar
  sessionStorage.setItem(ORIGINAL_TOKEN_KEY, currentToken);
  sessionStorage.setItem(ORIGINAL_USER_KEY, originalUserName);
  sessionStorage.setItem(IMPERSONATION_KEY, JSON.stringify({ targetName }));

  // Substitui a sessão ativa pelo token de impersonação
  sessionStorage.setItem(DEV_TOKEN_KEY, body.access_token);
}

export function stopImpersonation(): void {
  const originalToken = sessionStorage.getItem(ORIGINAL_TOKEN_KEY);
  if (originalToken) {
    sessionStorage.setItem(DEV_TOKEN_KEY, originalToken);
  }
  sessionStorage.removeItem(ORIGINAL_TOKEN_KEY);
  sessionStorage.removeItem(ORIGINAL_USER_KEY);
  sessionStorage.removeItem(IMPERSONATION_KEY);
}
