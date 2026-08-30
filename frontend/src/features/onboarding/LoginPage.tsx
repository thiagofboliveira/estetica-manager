import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getSessionToken } from "@/lib/auth/session";
import styles from "./LoginPage.module.css";

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === "true";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const [authMode, setAuthMode] = useState<"dev" | "standard">(DEV_AUTH ? "dev" : "standard");

  function goToReturnTo() {
    const returnTo = sessionStorage.getItem("returnTo") ?? "/dashboard";
    sessionStorage.removeItem("returnTo");
    navigate(returnTo, { replace: true });
  }

  async function handleDevLogin(e?: FormEvent) {
    if (e) e.preventDefault();
    setError(null);
    setIsPending(true);
    try {
      const token = await getSessionToken();
      setIsPending(false);
      if (!token) {
        setError("Não foi possível autenticar no backend de desenvolvimento.");
        return;
      }
      goToReturnTo();
    } catch (err: any) {
      setIsPending(false);
      setError(err?.message || "Erro ao conectar com servidor local.");
    }
  }

  async function handleStandardSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsPending(true);
    try {
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
    } catch {
      setIsPending(false);
      setError("Falha ao autenticar. Tente novamente.");
    }
  }

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCardWrapper}>
        {/* Left Side: Brand & Value Prop */}
        <div className={styles.brandSide}>
          <div className={styles.brandHeader}>
            <div className={styles.logoBadge}>✨</div>
            <span className={styles.brandName}>Lumina</span>
          </div>

          <div className={styles.brandBody}>
            <h2>Gestão e inteligência de retorno para sua clínica.</h2>
            <p>
              Acesse o painel para visualizar a régua diária de WhatsApp, controlar
              pacotes e blindar seu lucro real.
            </p>

            <div className={styles.featureHighlights}>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>✓</span>
                <span>Régua diária de WhatsApp com 1 clique</span>
              </div>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>✓</span>
                <span>Lucro real vs. provisório por sessão</span>
              </div>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>✓</span>
                <span>Agenda integrada à baixa de procedimentos</span>
              </div>
            </div>
          </div>

          <div className={styles.brandFooter}>
            <Link to="/" className={styles.backLink}>
              ← Voltar para o site institucional
            </Link>
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className={styles.formSide}>
          <div className={styles.formHeader}>
            <h3>Acesse sua conta</h3>
            <p>Selecione a forma de acesso para continuar</p>
          </div>

          {/* Quick Tab Switcher */}
          <div className={styles.tabSwitcher}>
            <button
              type="button"
              className={`${styles.tabBtn} ${authMode === "standard" ? styles.tabBtnActive : ""}`}
              onClick={() => setAuthMode("standard")}
            >
              Email & Senha
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${authMode === "dev" ? styles.tabBtnActive : ""}`}
              onClick={() => setAuthMode("dev")}
            >
              ⚡ Acesso Dev (Cliente Zero)
            </button>
          </div>

          {error && (
            <div role="alert" className={styles.alertError}>
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {authMode === "standard" ? (
            <form onSubmit={handleStandardSubmit} className={styles.form}>
              <div className={styles.inputGroup}>
                <label htmlFor="email">E-mail Profissional</label>
                <input
                  id="email"
                  type="email"
                  inputMode="email"
                  autoComplete="email"
                  placeholder="doutora@clinica.com.br"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className={styles.inputGroup}>
                <div className={styles.labelRow}>
                  <label htmlFor="password">Senha</label>
                  <a href="#recuperar" className={styles.forgotLink}>
                    Esqueceu?
                  </a>
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isPending}
                className={styles.submitBtn}
              >
                {isPending ? "Autenticando…" : "Entrar no Sistema"}
              </button>
            </form>
          ) : (
            <div className={styles.devBox}>
              <div className={styles.devCardInfo}>
                <strong>Modo de Desenvolvimento</strong>
                <p>
                  Autentica diretamente contra a rota <code>/dev/login</code> do backend
                  local para testes imediatos sem necessidade de Supabase ativo.
                </p>
              </div>

              <button
                type="button"
                onClick={() => handleDevLogin()}
                disabled={isPending}
                className={styles.devSubmitBtn}
              >
                {isPending ? "Conectando ao Backend…" : "⚡ Entrar como Cliente Zero"}
              </button>
            </div>
          )}

          <div className={styles.termsNote}>
            Ao acessar, você concorda com os Termos de Uso e Política de Privacidade LGPD da Lumina.
          </div>
        </div>
      </div>
    </div>
  );
}
