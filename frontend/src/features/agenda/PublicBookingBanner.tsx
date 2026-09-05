import { useState } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import styles from "./PublicBookingBanner.module.css";

export function PublicBookingBanner() {
  const { user, updatePublicProfile } = useAuth();
  const [copied, setCopied] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const [slugInput, setSlugInput] = useState(user?.slug || "");
  const [bioInput, setBioInput] = useState(user?.bio || "");
  const [saving, setSaving] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  if (!user || user.role === "receptionist") return null;

  const currentSlug = user.slug || "minha-agenda";
  const publicUrl = `${window.location.origin}/agendar/${currentSlug}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(publicUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setModalError(null);

    try {
      const cleanSlug = slugInput
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");

      if (cleanSlug.length < 3) {
        setModalError("O link deve ter pelo menos 3 caracteres alfanuméricos.");
        setSaving(false);
        return;
      }

      await updatePublicProfile(cleanSlug, bioInput.trim() || undefined);
      setShowModal(false);
    } catch (err: unknown) {
      const error = err as Error;
      setModalError(error.message || "Erro ao salvar perfil público.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <div className={styles.banner}>
        <div className={styles.info}>
          <div className={styles.icon}>🔗</div>
          <div className={styles.textGroup}>
            <span className={styles.title}>Seu Link de Agendamento (Bio & WhatsApp)</span>
            <span className={styles.linkPreview}>{publicUrl}</span>
          </div>
        </div>

        <div className={styles.actions}>
          <button type="button" className={styles.btnCopy} onClick={handleCopy}>
            {copied ? "✓ Link Copiado!" : "Copiar Link da Bio"}
          </button>

          <a
            href={`/agendar/${currentSlug}`}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.btnSecondary}
          >
            Visualizar Página ↗
          </a>

          <button
            type="button"
            className={styles.btnSecondary}
            onClick={() => {
              setSlugInput(user.slug || "");
              setBioInput(user.bio || "");
              setShowModal(true);
            }}
          >
            Personalizar
          </button>
        </div>
      </div>

      {showModal && (
        <div className={styles.modalBackdrop}>
          <form className={styles.modalContent} onSubmit={handleSaveProfile}>
            <h2 className={styles.modalTitle}>Personalizar Link de Agendamento</h2>
            <p className={styles.modalDescription}>
              Este link é o que suas pacientes acessam para escolher serviços e agendar horários vagos direto pelo celular.
            </p>

            <div className={styles.inputGroup}>
              <label className={styles.label}>Link Personalizado (slug)</label>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  /agendar/
                </span>
                <input
                  type="text"
                  className={styles.input}
                  style={{ flex: 1 }}
                  placeholder="dra-camila"
                  value={slugInput}
                  onChange={(e) => setSlugInput(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label className={styles.label}>Bio / Apresentação (opcional)</label>
              <textarea
                className={styles.input}
                rows={3}
                placeholder="Ex: Biomédica esteta especializada em harmonização e cuidados com a pele."
                value={bioInput}
                onChange={(e) => setBioInput(e.target.value)}
              />
            </div>

            {modalError && <div className={styles.error}>{modalError}</div>}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "8px" }}>
              <button
                type="button"
                className={styles.btnSecondary}
                onClick={() => setShowModal(false)}
                disabled={saving}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className={styles.btnCopy}
                disabled={saving}
              >
                {saving ? "Salvando..." : "Salvar Alterações"}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
