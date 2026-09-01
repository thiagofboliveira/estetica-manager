import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { api } from "@/lib/http/client";

interface SystemStatus {
  is_initialized: boolean;
  users_count: number;
}

export function RequireAuth() {
  const { user, isLoading } = useAuth();
  const location = useLocation();
  const [setupRequired, setSetupRequired] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkSetup() {
      try {
        const res = await api.get<SystemStatus>("/system/status");
        setSetupRequired(!res.is_initialized);
      } catch {
        setSetupRequired(false);
      }
    }

    checkSetup();
  }, []);

  if (isLoading || setupRequired === null) {
    return (
      <div
        style={{
          display: "flex",
          height: "100vh",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "var(--font-sans, system-ui)",
          color: "#6b7280",
        }}
      >
        Carregando...
      </div>
    );
  }

  if (setupRequired && location.pathname !== "/setup") {
    return <Navigate to="/setup" replace />;
  }

  if (!user && location.pathname !== "/setup") {
    sessionStorage.setItem("returnTo", location.pathname + location.search);
    return <Navigate to="/login" replace />;
  }

  // Redireciona o Super Admin Global para o painel SaaS
  if (user && user.role === "superadmin" && location.pathname === "/dashboard") {
    return <Navigate to="/super-admin/clinicas" replace />;
  }

  return <Outlet />;
}
