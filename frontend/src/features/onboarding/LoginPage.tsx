import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { devLogin, getSessionToken } from "@/lib/auth/session";
import { useAuth } from "@/lib/auth/AuthContext";
import { IconSparkles, IconCheck, IconShield, IconAlertTriangle } from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./LoginPage.module.css";

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === "true";

export function LoginPage() {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const [authMode, setAuthMode] = useState<"dev" | "standard">(DEV_AUTH ? "dev" : "standard");

  async function goToReturnTo() {
    await checkAuth();
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
      await goToReturnTo();
    } catch (err: unknown) {
      setIsPending(false);
      const errMsg = err instanceof Error ? err.message : "Erro ao conectar com servidor local.";
      setError(errMsg);
    }
  }

  async function handleStandardSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsPending(true);
    try {
      if (DEV_AUTH) {
        const token = await devLogin(email, password);
        setIsPending(false);
        if (!token) {
          setError("Não foi possível autenticar. Verifique se o e-mail está cadastrado.");
          return;
        }
        await goToReturnTo();
        return;
      }

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
      await goToReturnTo();
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
            <div className={styles.logoBadge}>
              <IconSparkles width="20" height="20" />
            </div>
            <span className={styles.brandName}>Lumina</span>
          </div>

          <div className={styles.brandBody}>
            <h2>Gestão e inteligência de retorno para estética avançada.</h2>
            <p>
              Acesse o painel para orquestrar a régua de retenção via WhatsApp, controlar
              pacotes e blindar seu lucro real.
            </p>

            <div className={styles.featureHighlights}>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>
                  <IconCheck width="14" height="14" />
                </span>
                <span>Régua diária de WhatsApp com 1 toque</span>
              </div>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>
                  <IconCheck width="14" height="14" />
                </span>
                <span>Lucro real vs. provisório por sessão</span>
              </div>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>
                  <IconCheck width="14" height="14" />
                </span>
                <span>Agenda integrada à baixa de procedimentos</span>
              </div>
            </div>
          </div>

          <div className={styles.brandFooter}>
            <Link to="/" className={styles.backLink}>
              ← Voltar para o início
            </Link>
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className={styles.formSide}>
          <div className={styles.formHeader}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <h3>Acesse sua conta</h3>
                <p>Selecione a modalidade de acesso</p>
              </div>
              <ThemeToggle />
            </div>
          </div>

          {/* Quick Tab Switcher */}
          <div className={styles.tabSwitcher}>
            <button
              type="button"
              className={authMode === "standard" ? `${styles.tabBtn} ${styles.tabBtnActive}` : styles.tabBtn}
              onClick={() => setAuthMode("standard")}
            >
              Email & Senha
            </button>
            <button
              type="button"
              className={authMode === "dev" ? `${styles.tabBtn} ${styles.tabBtnActive}` : styles.tabBtn}
              onClick={() => setAuthMode("dev")}
            >
              Acesso Rápido Dev
            </button>
          </div>

          {error && (
            <div role="alert" className={styles.alertError}>
              <IconAlertTriangle width="18" height="18" />
              <span>{error}</span>
            </div>
          )}

          {authMode === "standard" ? (
            <form onSubmit={handleStandardSubmit} className={styles.form}>
              <div className={styles.inputGroup}>
                <label htmlFor="email">E-mail de Acesso</label>
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
                    Esqueceu a senha?
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
                <div className={styles.devCardHeader}>
                  <IconShield width="16" height="16" />
                  <strong>Ambiente de Desenvolvimento</strong>
                </div>
                <p>
                  Autentica instantaneamente contra a API local (<code>/dev/login</code>)
                  com credenciais locais de teste.
                </p>
              </div>

              <button
                type="button"
                onClick={() => handleDevLogin()}
                disabled={isPending}
                className={styles.devSubmitBtn}
              >
                {isPending ? "Conectando ao Backend…" : "Entrar com Conta de Teste"}
              </button>
            </div>
          )}

          <div className={styles.termsNote}>
            Plataforma protegida e em conformidade com as diretrizes de privacidade LGPD.
          </div>
        </div>
      </div>
    </div>
  );
}
