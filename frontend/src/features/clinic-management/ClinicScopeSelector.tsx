import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth/AuthContext";
import { api } from "@/lib/http/client";
import { IconBuilding, IconUsers } from "@/ui/icons";
import styles from "./ClinicScopeSelector.module.css";

export type ClinicScopeValue = {
  scope: "me" | "clinic";
  professional_id?: string;
};

export type ClinicUserItem = {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
};

export type ClinicScopeSelectorProps = {
  value: ClinicScopeValue;
  onChange: (value: ClinicScopeValue) => void;
  professionalsCount?: number;
};

export function ClinicScopeSelector({
  value,
  onChange,
  professionalsCount,
}: ClinicScopeSelectorProps) {
  const { user } = useAuth();

  const isAdmin = user?.role === "admin" || user?.role === "superadmin" || Boolean(user?.is_superuser);
  const isEligible = Boolean(isAdmin && user?.clinic_id);

  const { data: users = [] } = useQuery<ClinicUserItem[]>({
    queryKey: ["clinic", "users", user?.clinic_id],
    queryFn: () => api.get<ClinicUserItem[]>("/users"),
    enabled: isEligible,
    staleTime: 5 * 60 * 1000,
  });

  if (!isEligible) {
    return null;
  }

  const isAllClinic = value.scope === "clinic" && !value.professional_id;
  const isOnlyMe = value.scope === "me" || (value.professional_id === user?.id);
  const isSpecificOther = Boolean(value.professional_id && value.professional_id !== user?.id);

  return (
    <div className={styles.container}>
      <div className={styles.scopeNav} role="group" aria-label="Escopo de visualização">
        <button
          type="button"
          className={`${styles.scopeBtn} ${isAllClinic ? styles.scopeBtnActive : ""}`}
          onClick={() => onChange({ scope: "clinic", professional_id: undefined })}
          title="Visualizar dados agregados de toda a clínica"
        >
          <IconBuilding width="15" height="15" />
          <span>Toda a Clínica</span>
        </button>

        <button
          type="button"
          className={`${styles.scopeBtn} ${isOnlyMe ? styles.scopeBtnActive : ""}`}
          onClick={() => onChange({ scope: "me", professional_id: undefined })}
          title="Visualizar apenas meus atendimentos e finanças"
        >
          <IconUsers width="15" height="15" />
          <span>Meu Atendimento</span>
        </button>
      </div>

      {users.length > 1 && (
        <select
          className={`${styles.scopeSelect} ${isSpecificOther ? styles.scopeSelectActive : ""}`}
          value={value.professional_id ?? (value.scope === "clinic" ? "all" : "me")}
          onChange={(e) => {
            const val = e.target.value;
            if (val === "all") {
              onChange({ scope: "clinic", professional_id: undefined });
            } else if (val === "me") {
              onChange({ scope: "me", professional_id: undefined });
            } else {
              onChange({ scope: "clinic", professional_id: val });
            }
          }}
          aria-label="Filtrar por profissional da equipe"
        >
          <option value="all">🏢 Toda a equipe ({users.length})</option>
          <option value="me">👤 Meu atendimento (você)</option>
          <optgroup label="Profissionais da equipe">
            {users
              .filter((u) => u.id !== user?.id)
              .map((u) => (
                <option key={u.id} value={u.id}>
                  👤 {u.name}
                </option>
              ))}
          </optgroup>
        </select>
      )}

      {isAllClinic && (
        <span className={styles.consolidatedBadge}>
          <IconBuilding width="13" height="13" />
          Consolidado ({professionalsCount ?? Math.max(users.length, 1)} { (professionalsCount ?? Math.max(users.length, 1)) === 1 ? "profissional" : "profissionais" })
        </span>
      )}
    </div>
  );
}
