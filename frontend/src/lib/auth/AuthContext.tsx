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
  terms_accepted?: boolean;
  terms_accepted_at?: string | null;
  terms_version?: string | null;
  slug?: string | null;
  bio?: string | null;
}

interface AuthContextValue {
  user: UserSession | null;
  isLoading: boolean;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  acceptTerms: (termsVersion?: string) => Promise<void>;
  updatePublicProfile: (slug?: string, bio?: string) => Promise<void>;
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
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function acceptTerms(termsVersion: string = "2026-09-v1") {
    const updated = await api.post<UserSession>("/users/me/accept-terms", {
      terms_version: termsVersion,
    });
    setUser(updated);
  }

  async function updatePublicProfile(slug?: string, bio?: string) {
    const updated = await api.patch<UserSession>("/users/me/public-profile", {
      slug,
      bio,
    });
    setUser(updated);
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
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        logout,
        checkAuth,
        acceptTerms,
        updatePublicProfile,
      }}
    >
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
