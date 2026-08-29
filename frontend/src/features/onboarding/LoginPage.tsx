import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSessionToken } from "@/lib/auth/session";

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === "true";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  function goToReturnTo() {
    const returnTo = sessionStorage.getItem("returnTo") ?? "/";
    sessionStorage.removeItem("returnTo");
    navigate(returnTo, { replace: true });
  }

  async function onSubmitDev(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsPending(true);
    const token = await getSessionToken();
    setIsPending(false);
    if (!token) {
      setError("Não consegui obter o token de desenvolvimento do backend.");
      return;
    }
    goToReturnTo();
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsPending(true);
    const { supabase } = await import("@/lib/auth/supabase");
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    setIsPending(false);
    if (signInError) {
      setError("E-mail ou senha inválidos.");
      return;
    }
    goToReturnTo();
  }

  if (DEV_AUTH) {
    return (
      <form onSubmit={onSubmitDev} className="login-form">
        <h1>Entrar (modo desenvolvimento)</h1>
        <p>Sem Supabase configurado — autentica direto contra o backend local.</p>
        {error && (
          <p role="alert" className="login-form__error">
            {error}
          </p>
        )}
        <button type="submit" disabled={isPending} className="tap-target submit">
          {isPending ? "Entrando…" : "Entrar como Cliente Zero (dev)"}
        </button>
      </form>
    );
  }

  return (
    <form onSubmit={onSubmit} className="login-form">
      <h1>Entrar</h1>
      <label>
        <span>E-mail</span>
        <input
          type="email"
          inputMode="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label>
        <span>Senha</span>
        <input
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error && (
        <p role="alert" className="login-form__error">
          {error}
        </p>
      )}
      <button type="submit" disabled={isPending} className="tap-target submit">
        {isPending ? "Entrando…" : "Entrar"}
      </button>
    </form>
  );
}
