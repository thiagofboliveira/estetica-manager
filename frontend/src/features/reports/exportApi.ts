import { getSessionToken } from "@/lib/auth/session";

const BASE = import.meta.env.VITE_API_URL;

export async function downloadCsv(
  type: "sales" | "sessions" | "patients",
  filename?: string,
): Promise<void> {
  const token = await getSessionToken();
  const res = await fetch(`${BASE}/export/${type}.csv`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) {
    throw new Error("Erro ao baixar arquivo CSV.");
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `${type}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}
