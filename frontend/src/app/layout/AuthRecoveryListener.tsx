import { useEffect } from "react";
import { useLocation, useNavigate, Outlet } from "react-router-dom";

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === "true";

export function AuthRecoveryListener() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const hash = window.location.hash;
    const search = window.location.search;

    const isRecoveryHash = hash.includes("type=recovery") || hash.includes("type=invite");
    const isRecoverySearch = search.includes("type=recovery") || search.includes("type=invite");
    const hasCode = search.includes("code=");

    const isAlreadyOnResetPage =
      location.pathname.startsWith("/redefinir-senha") ||
      location.pathname.startsWith("/reset-password");

    if ((isRecoveryHash || isRecoverySearch || hasCode) && !isAlreadyOnResetPage) {
      navigate(`/redefinir-senha${search}${hash}`, { replace: true });
      return;
    }

    if (DEV_AUTH) return;

    let cleanup: (() => void) | undefined;

    import("@/lib/auth/supabase").then(({ supabase }) => {
      const { data: listener } = supabase.auth.onAuthStateChange((event) => {
        if (event === "PASSWORD_RECOVERY") {
          if (
            !window.location.pathname.startsWith("/redefinir-senha") &&
            !window.location.pathname.startsWith("/reset-password")
          ) {
            navigate(
              `/redefinir-senha${window.location.search}${window.location.hash}`,
              { replace: true }
            );
          }
        }
      });
      cleanup = () => listener.subscription.unsubscribe();
    });

    return () => {
      if (cleanup) cleanup();
    };
  }, [location, navigate]);

  return <Outlet />;
}
