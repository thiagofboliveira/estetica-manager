import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  throw new Error(
    "VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY são obrigatórias — configure .env.local",
  );
}

export const supabase = createClient(url, anonKey, {
  auth: {
    persistSession: true, // sessão longa — ela usa entre atendimentos
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storageKey: "estetica.auth",
    flowType: "pkce", // nunca implicit: PKCE não põe token na URL
  },
  global: { headers: { "x-client-info": "estetica-web" } },
});
