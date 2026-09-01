import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/http/client";
import { IconCrown, IconAlertTriangle } from "@/ui/icons";
import { ThemeToggle } from "@/ui/ThemeToggle";
import styles from "./SetupWizardPage.module.css";

export function SetupWizardPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    adminName: "",
    email: "",
    password: "",
  });
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsPending(true);
    setError(null);

    try {
      await api.post("/system/setup", {
        clinic_name: "Plataforma Lumina",
        admin_name: formData.adminName,
        email: formData.email,
        password: formData.password || undefined,
      });

      navigate("/login");
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
        <div className={styles.header}>
          <div className={styles.iconBadge}>
            <IconCrown width="24" height="24" />
          </div>
          <h1 className={styles.title}>Bem-vindo à Lumina</h1>
          <p className={styles.subtitle}>
            Crie a conta do <strong>Super Administrador Global</strong> para gerenciar a plataforma SaaS e suas clínicas parceiras.
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

          <div className={styles.inputGroup}>
            <label htmlFor="password">Senha Master</label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder="Mínimo de 8 caracteres"
              minLength={8}
            />
          </div>

          <button type="submit" className={styles.submitBtn} disabled={isPending}>
            {isPending ? "Criando conta..." : "Criar Conta Super Admin"}
          </button>
        </form>
      </div>
    </div>
  );
}
