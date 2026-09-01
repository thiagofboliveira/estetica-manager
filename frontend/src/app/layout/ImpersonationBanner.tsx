import { useNavigate } from "react-router-dom";
import { stopImpersonation, getImpersonationState } from "@/lib/auth/impersonation";
import { useAuth } from "@/lib/auth/AuthContext";
import styles from "./ImpersonationBanner.module.css";

export function ImpersonationBanner() {
  const state = getImpersonationState();
  const { checkAuth } = useAuth();
  const navigate = useNavigate();

  if (!state.isImpersonating) return null;

  async function handleExit() {
    stopImpersonation();
    await checkAuth();
    navigate("/super-admin/clinicas", { replace: true });
  }

  return (
    <div className={styles.banner}>
      <span className={styles.icon}>👁</span>
      <span className={styles.text}>
        Você está visualizando como{" "}
        <strong>{state.targetUserName ?? "Usuário"}</strong>
        {state.originalUserName && (
          <span className={styles.subtle}> · logado como {state.originalUserName}</span>
        )}
      </span>
      <button className={styles.exitBtn} onClick={handleExit}>
        ✕ Sair da visão
      </button>
    </div>
  );
}
