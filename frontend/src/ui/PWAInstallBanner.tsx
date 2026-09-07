import { useEffect, useState } from "react";
import { IconX, IconSparkles } from "@/ui/icons";
import styles from "./PWAInstallBanner.module.css";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function PWAInstallBanner() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isDismissed, setIsDismissed] = useState(true);

  useEffect(() => {
    // Verificar se já está instalado em standalone
    const isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as unknown as { standalone?: boolean }).standalone === true;

    if (isStandalone) {
      return;
    }

    // Verificar se o usuário já dispensou nos últimos 7 dias
    const dismissedAt = localStorage.getItem("pwa_prompt_dismissed_at");
    if (dismissedAt) {
      const diff = Date.now() - Number(dismissedAt);
      if (diff < 7 * 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // Detectar iOS Safari
    const userAgent = window.navigator.userAgent.toLowerCase();
    const isIosDevice = /iphone|ipad|ipod/.test(userAgent);
    if (isIosDevice) {
      setIsIOS(true);
      setIsDismissed(false);
      return;
    }

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setIsDismissed(false);
    };

    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem("pwa_prompt_dismissed_at", Date.now().toString());
  };

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") {
      setIsDismissed(true);
    }
    setDeferredPrompt(null);
  };

  if (isDismissed) {
    return null;
  }

  return (
    <aside className={styles.banner} role="dialog" aria-label="Instalar Aplicativo">
      <div className={styles.content}>
        <div className={styles.appIcon}>
          <IconSparkles width="22" height="22" />
        </div>
        <div className={styles.textGroup}>
          <h4 className={styles.title}>Instalar Estética Manager</h4>
          <p className={styles.subtitle}>
            {isIOS
              ? "Toque no botão Compartilhar e selecione 'Adicionar à Tela de Início'."
              : "Acesse sua agenda e clientes num toque direto da tela inicial."}
          </p>
        </div>
      </div>

      <div className={styles.actions}>
        {!isIOS && deferredPrompt && (
          <button
            type="button"
            className={styles.installBtn}
            onClick={handleInstallClick}
          >
            Instalar
          </button>
        )}
        <button
          type="button"
          className={styles.closeBtn}
          onClick={handleDismiss}
          aria-label="Dispensar aviso de instalação"
        >
          <IconX width="18" height="18" />
        </button>
      </div>
    </aside>
  );
}
