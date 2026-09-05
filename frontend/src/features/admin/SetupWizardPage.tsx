import { useState } from "react";
import { api } from "@/lib/http/client";
import { IconCrown, IconAlertTriangle, IconCheck } from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./SetupWizardPage.module.css";

/**
 * B-01 (docs/pending/BACKLOG_GO_LIVE.md): sem campo de senha. O backend
 * (system_service.setup_root) cria o usuário no Supabase Auth via Admin
 * API e o Supabase manda um e-mail de convite — a pessoa define a
 * própria senha ao clicar no link. Um campo de senha aqui seria
 * coletado e descartado, exatamente o defeito que existia antes: a tela
 * dizia "Criando conta..." e a senha nunca chegava a lugar nenhum.
 */
export function SetupWizardPage() {
  const [formData, setFormData] = useState({
    adminName: "",
    email: "",
  });
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsPending(true);
    setError(null);

    try {
      await api.post("/system/setup", {
        clinic_name: "Plataforma Lumina",
        admin_name: formData.adminName,
        email: formData.email,
      });

      setDone(true);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Ocorreu um erro ao configurar o sistema.");
      }
    } finally {
      setIsPending(false);
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  return (
    <div className={styles.setupContainer}>
      <div className={styles.card}>
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "16px 20px 0" }}>
          <ThemeToggle />
        </div>
        {done ? (
          <div className={styles.header}>
            <div className={styles.iconBadge}>
              <IconCheck width="24" height="24" />
            </div>
            <h1 className={styles.title}>Convite enviado!</h1>
            <p className={styles.subtitle}>
              Enviamos um e-mail para <strong>{formData.email}</strong> com um link para você
              definir sua senha e acessar a plataforma. Confira também a caixa de spam.
            </p>
          </div>
        ) : (
          <>
            <div className={styles.header}>
              <div className={styles.iconBadge}>
                <IconCrown width="24" height="24" />
              </div>
              <h1 className={styles.title}>Bem-vindo à Lumina</h1>
              <p className={styles.subtitle}>
                Crie a conta do <strong>Super Administrador Global</strong> para gerenciar a
                plataforma SaaS e suas clínicas parceiras. Você receberá um e-mail para definir
                sua senha.
              </p>
            </div>

            <form className={styles.form} onSubmit={handleSubmit}>
              {error && (
                <div role="alert" className={styles.alertError}>
                  <IconAlertTriangle width="18" height="18" />
                  <span>{error}</span>
                </div>
              )}

              <div className={styles.inputGroup}>
                <label htmlFor="adminName">Nome do Administrador</label>
                <input
                  id="adminName"
                  name="adminName"
                  type="text"
                  required
                  value={formData.adminName}
                  onChange={handleChange}
                  placeholder="Ex: Thiago Oliveira"
                />
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="email">E-mail Master</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="admin@lumina.com.br"
                />
              </div>

              <button type="submit" className={styles.submitBtn} disabled={isPending}>
                {isPending ? "Enviando convite..." : "Criar Conta Super Admin"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
