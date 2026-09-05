import { useState } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import styles from "./LegalPages.module.css";
import { IconShield } from "@/ui/icons";

export const CURRENT_TERMS_VERSION = "2026-09-v1";

export function TermsAcceptanceModal() {
  const { user, acceptTerms } = useAuth();
  const [accepted, setAccepted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Se o usuário não estiver autenticado ou já tiver aceitado a versão atual, não renderiza
  if (!user || (user.terms_accepted && user.terms_version === CURRENT_TERMS_VERSION)) {
    return null;
  }

  async function handleConfirm() {
    if (!accepted) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await acceptTerms(CURRENT_TERMS_VERSION);
    } catch (err) {
      setError("Não foi possível registrar o aceite no momento. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-labelledby="terms-title">
      <div className={styles.modalBox}>
        <div className={styles.modalTitle} id="terms-title">
          <IconShield width="24" height="24" color="#6366f1" />
          <span>Atualização de Termos e LGPD</span>
        </div>

        <div className={styles.modalBody}>
          <p>
            Olá, <strong>{user.name}</strong>. Para continuar utilizando o Estética Manager,
            é necessário formalizar o seu consentimento com os nossos Termos de Uso e com o
            <strong> Contrato de Tratamento de Dados Pessoais (LGPD / DPA)</strong>.
          </p>
          <p>
            Como profissional ou clínica, você atua como <strong>Controladora</strong> dos dados dos seus clientes,
            e nós atuamos como <strong>Operadora</strong> sob rigorosas diretrizes técnicas e isolamento por banco de dados.
          </p>
        </div>

        <div className={styles.termsLinks}>
          <a
            href="/termos"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.linkItem}
          >
            <span>📄 Ler Termos de Uso e Prestação de Serviços</span>
            <span>↗</span>
          </a>
          <a
            href="/privacidade"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.linkItem}
          >
            <span>🔒 Ler Política de Privacidade e Contrato LGPD (DPA)</span>
            <span>↗</span>
          </a>
        </div>

        <label className={styles.checkboxRow}>
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            disabled={isSubmitting}
          />
          <span>
            Declaro que li, compreendi e concordo integralmente com os <strong>Termos de Uso</strong> e o <strong>Contrato de Tratamento de Dados (DPA/LGPD)</strong>.
          </span>
        </label>

        {error && (
          <div style={{ color: "#ef4444", fontSize: "0.875rem" }}>
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleConfirm}
          disabled={!accepted || isSubmitting}
          className={styles.acceptBtn}
        >
          {isSubmitting ? "Registrando aceite…" : "Confirmar e Acessar o Sistema"}
        </button>
      </div>
    </div>
  );
}
