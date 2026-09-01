import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getSessionToken, signOutSession } from "./session";
import { queryClient } from "@/lib/query/client";
import { api } from "@/lib/http/client";

export type Role = "superadmin" | "admin" | "professional" | "receptionist";

export interface UserSession {
  id: string;
  clinic_id?: string | null;
  clinic_name?: string | null;
  name: string;
  email: string;
  role: Role;
  is_superuser: boolean;
  is_active?: boolean;
}

interface AuthContextValue {
  user: UserSession | null;
  isLoading: boolean;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function checkAuth() {
    setIsLoading(true);
    try {
      const token = await getSessionToken();
      if (!token) {
        setUser(null);
        return;
      }
      
      const res = await api.get<UserSession>("/users/me");
      setUser(res);
    } catch (e) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function logout() {
    await signOutSession();
    setUser(null);
    queryClient.clear();
  }

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
