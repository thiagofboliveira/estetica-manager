import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { IconSparkles, IconCheck, IconAlertTriangle, IconLock } from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./LoginPage.module.css";

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === "true";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();

  const [status, setStatus] = useState<"loading" | "ready" | "saving" | "success" | "error">(
    "loading"
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    let isMounted = true;

    async function initRecovery() {
      if (DEV_AUTH) {
        if (isMounted) setStatus("ready");
        return;
      }

      try {
        const { supabase } = await import("@/lib/auth/supabase");

        // 1. Verifica se há erros retornados na URL (hash ou query params)
        const hash = window.location.hash.replace(/^#/, "");
        const hashParams = new URLSearchParams(hash);
        const searchParams = new URLSearchParams(window.location.search);

        const errorDesc =
          hashParams.get("error_description") ||
          searchParams.get("error_description") ||
          hashParams.get("error") ||
          searchParams.get("error");

        if (errorDesc) {
          if (isMounted) {
            setErrorMessage(
              "Este link de recuperação expirou ou é inválido. Por favor, solicite um novo link na tela de login."
            );
            setStatus("error");
          }
          return;
        }

        // 2. Se houver PKCE code na query string, troca pelo token de sessão
        const code = searchParams.get("code");
        if (code) {
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            if (isMounted) {
              setErrorMessage(
                exchangeError.message ||
                  "Não foi possível validar o código de recuperação. Solicite um novo link."
              );
              setStatus("error");
            }
            return;
          }
        }

        // 3. Verifica se já temos sessão ativa (oriunda do hash ou de exchange)
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          if (isMounted) setStatus("ready");
          return;
        }

        // 4. Aguarda listener caso o Supabase ainda esteja processando o hash
        const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
          if (!isMounted) return;
          if (event === "PASSWORD_RECOVERY" || session) {
            setStatus("ready");
          }
        });

        // Timeout de fallback para não travar em loading se o link não tiver credenciais
        const timer = setTimeout(() => {
          if (isMounted) {
            supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
              if (isMounted) {
                if (currentSession) {
                  setStatus("ready");
                } else {
                  setErrorMessage(
                    "Link de recuperação expirado ou não encontrado. Por favor, solicite um novo link."
                  );
                  setStatus("error");
                }
              }
            });
          }
        }, 2000);

        return () => {
          authListener.subscription.unsubscribe();
          clearTimeout(timer);
        };
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Erro ao validar sessão de recuperação.";
          setErrorMessage(msg);
          setStatus("error");
        }
      }
    }

    initRecovery();

    return () => {
      isMounted = false;
    };
  }, []);

  // Contagem regressiva para redirecionar após o sucesso
  useEffect(() => {
    if (status !== "success") return;

    if (countdown <= 0) {
      navigate("/dashboard", { replace: true });
      return;
    }

    const timer = setTimeout(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [status, countdown, navigate]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setValidationError(null);

    if (password.length < 6) {
      setValidationError("A senha deve ter no mínimo 6 caracteres.");
      return;
    }

    if (password !== confirmPassword) {
      setValidationError("As senhas digitadas não conferem.");
      return;
    }

    setStatus("saving");

    try {
      if (DEV_AUTH) {
        setStatus("success");
        return;
      }

      const { supabase } = await import("@/lib/auth/supabase");
      const { error: updateError } = await supabase.auth.updateUser({
        password: password,
      });

      if (updateError) {
        let msg = updateError.message;
        if (msg.toLowerCase().includes("same_password") || msg.toLowerCase().includes("different")) {
          msg = "A nova senha deve ser diferente da senha anterior.";
        }
        setValidationError(msg);
        setStatus("ready");
        return;
      }

      // Sincroniza sessão com a API do backend
      await checkAuth();
      setStatus("success");
    } catch {
      setValidationError("Falha ao atualizar a senha. Tente novamente.");
      setStatus("ready");
    }
  }

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCardWrapper}>
        {/* Left Side: Brand & Security Guarantee */}
        <div className={styles.brandSide}>
          <div className={styles.brandHeader}>
            <div className={styles.logoBadge}>
              <IconSparkles width="20" height="20" />
            </div>
            <span className={styles.brandName}>Lumina</span>
          </div>

          <div className={styles.brandBody}>
            <h2>Segurança e controle de acesso para sua clínica.</h2>
            <p>
              Defina sua nova senha de acesso para gerenciar sua agenda, pacientes e
              indicadores com total proteção e conformidade LGPD.
            </p>

            <div className={styles.featureHighlights}>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>
                  <IconCheck width="14" height="14" />
                </span>
                <span>Criptografia de ponta a ponta</span>
              </div>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>
                  <IconCheck width="14" height="14" />
                </span>
                <span>Sessão segura com renovação automática</span>
              </div>
              <div className={styles.featureItem}>
                <span className={styles.featureDot}>
                  <IconCheck width="14" height="14" />
                </span>
                <span>Acesso instantâneo a todas as unidades</span>
              </div>
            </div>
          </div>

          <div className={styles.brandFooter}>
            <Link to="/login" className={styles.backLink}>
              ← Ir para o login
            </Link>
          </div>
        </div>

        {/* Right Side: Form / Status */}
        <div className={styles.formSide}>
          <div className={styles.formHeader}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <h3>Redefinição de Senha</h3>
                <p>Crie uma nova senha para sua conta</p>
              </div>
              <ThemeToggle />
            </div>
          </div>

          {status === "loading" && (
            <div className={styles.devBox} style={{ textAlign: "center", padding: "32px 16px" }}>
              <div className={styles.devCardHeader} style={{ justifyContent: "center" }}>
                <IconLock width="20" height="20" />
                <strong>Verificando link de acesso…</strong>
              </div>
              <p style={{ marginTop: "12px", color: "var(--muted)" }}>
                Aguarde um instante enquanto validamos sua solicitação.
              </p>
            </div>
          )}

          {status === "error" && (
            <div className={styles.devBox}>
              <div className={styles.alertError} style={{ marginBottom: "16px" }}>
                <IconAlertTriangle width="20" height="20" />
                <span>{errorMessage}</span>
              </div>
              <p style={{ fontSize: "14px", color: "var(--muted)", marginBottom: "20px" }}>
                Por motivos de segurança, os links de redefinição têm prazo de validade. Você pode
                solicitar um novo link a qualquer momento.
              </p>
              <Link to="/login" className={styles.submitBtn} style={{ textAlign: "center", display: "block", textDecoration: "none" }}>
                Voltar para o login
              </Link>
            </div>
          )}

          {status === "success" && (
            <div className={styles.devBox}>
              <div className={styles.devCardInfo}>
                <div className={styles.devCardHeader}>
                  <IconCheck width="20" height="20" />
                  <strong>Senha atualizada com sucesso!</strong>
                </div>
                <p style={{ marginTop: "12px" }}>
                  Sua nova senha foi salva. Você será redirecionado para o sistema em{" "}
                  <strong>{countdown}s</strong>.
                </p>
              </div>
              <button
                type="button"
                className={styles.submitBtn}
                onClick={() => navigate("/dashboard", { replace: true })}
                style={{ marginTop: "16px" }}
              >
                Acessar o Painel Agora →
              </button>
            </div>
          )}

          {(status === "ready" || status === "saving") && (
            <form onSubmit={handleSubmit} className={styles.form}>
              {validationError && (
                <div role="alert" className={styles.alertError}>
                  <IconAlertTriangle width="18" height="18" />
                  <span>{validationError}</span>
                </div>
              )}

              <div className={styles.inputGroup}>
                <label htmlFor="password">Nova Senha</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Mínimo 6 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={status === "saving"}
                />
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="confirmPassword">Confirmar Nova Senha</label>
                <input
                  id="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Repita a nova senha"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={status === "saving"}
                />
              </div>

              <button
                type="submit"
                disabled={status === "saving"}
                className={styles.submitBtn}
              >
                {status === "saving" ? "Salvando nova senha…" : "Salvar Nova Senha"}
              </button>

              <div style={{ textAlign: "center", marginTop: "16px" }}>
                <Link to="/login" className={styles.forgotLink}>
                  ← Cancelar e voltar para o login
                </Link>
              </div>
            </form>
          )}

          <div className={styles.termsNote}>
            Ao acessar, você concorda com nossos{" "}
            <Link to="/termos" target="_blank" rel="noopener noreferrer">
              Termos de Uso
            </Link>{" "}
            e nossa{" "}
            <Link to="/privacidade" target="_blank" rel="noopener noreferrer">
              Política de Privacidade (LGPD)
            </Link>
            .
          </div>
        </div>
      </div>
    </div>
  );
}
