import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./AdminUsersPage.module.css";
import { api } from "@/lib/http/client";
import { useAuth } from "@/lib/auth/AuthContext";
import { startImpersonation } from "@/lib/auth/impersonation";
import { toast } from "@/ui/ToastContext";

interface GlobalUserItem {
  id: string;
  clinic_id: string | null;
  clinic_name: string | null;
  name: string;
  email: string;
  role: string;
  is_superuser: boolean;
  is_active: boolean;
}

interface ClinicOption {
  id: string;
  name: string;
}

function RoleBadge({ role }: { role: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    superadmin: { label: "Plataforma (Super)", cls: styles.badgeRoleSuper },
    admin: { label: "Admin de Clínica", cls: styles.badgeRoleAdmin },
    professional: { label: "Profissional", cls: styles.badgeRoleProf },
    receptionist: { label: "Recepção", cls: styles.badgeRoleRecp },
    user: { label: "Usuário", cls: styles.badgeRoleUser },
  };

  const { label, cls } = map[role] || { label: role, cls: "" };
  return <span className={`${styles.badge} ${cls}`}>{label}</span>;
}

export function SuperAdminUsersPage() {
  const navigate = useNavigate();
  const { user: currentUser, checkAuth } = useAuth();
  const [users, setUsers] = useState<GlobalUserItem[]>([]);
  const [clinics, setClinics] = useState<ClinicOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [impersonatingId, setImpersonatingId] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<GlobalUserItem | null>(null);
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formRole, setFormRole] = useState("user");
  const [formClinicId, setFormClinicId] = useState<string>("");
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  async function fetchUsersAndClinics() {
    setIsLoading(true);
    setError(null);
    try {
      const [usersData, clinicsData] = await Promise.all([
        api.get<GlobalUserItem[]>("/super-admin/users"),
        api.get<ClinicOption[]>("/super-admin/clinics"),
      ]);
      setUsers(usersData);
      setClinics(clinicsData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchUsersAndClinics();
  }, []);

  function handleOpenCreate() {
    setEditingUser(null);
    setFormName("");
    setFormEmail("");
    setFormRole("user");
    setFormClinicId(clinics.length > 0 ? clinics[0].id : "");
    setModalError(null);
    setIsModalOpen(true);
  }

  function handleOpenEdit(targetUser: GlobalUserItem) {
    setEditingUser(targetUser);
    setFormName(targetUser.name);
    setFormEmail(targetUser.email);
    setFormRole(targetUser.role);
    setFormClinicId(targetUser.clinic_id || "");
    setModalError(null);
    setIsModalOpen(true);
  }

  async function handleSaveUser(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim() || !formEmail.trim()) {
      setModalError("Nome e e-mail são obrigatórios.");
      return;
    }

    setFormSubmitting(true);
    setModalError(null);

    const payload = {
      name: formName.trim(),
      email: formEmail.trim().toLowerCase(),
      role: formRole,
      clinic_id: formClinicId || null,
      is_superuser: formRole === "superadmin",
    };

    try {
      if (editingUser) {
        await api.put(`/super-admin/users/${editingUser.id}`, payload);
        toast.success("Usuário atualizado com sucesso!");
      } else {
        await api.post("/super-admin/users", payload);
        toast.success("Usuário cadastrado com sucesso!");
      }
      setIsModalOpen(false);
      await fetchUsersAndClinics();
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Erro ao salvar usuário.");
    } finally {
      setFormSubmitting(false);
    }
  }

  async function handleToggleStatus(targetUser: GlobalUserItem) {
    try {
      await api.put(`/super-admin/users/${targetUser.id}`, {
        is_active: !targetUser.is_active,
      });
      toast.success(`Usuário ${!targetUser.is_active ? "ativado" : "desativado"} com sucesso!`);
      await fetchUsersAndClinics();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Erro ao alterar status do usuário.");
    }
  }

  async function handleImpersonate(targetUser: GlobalUserItem) {
    if (!currentUser) return;
    setImpersonatingId(targetUser.id);
    try {
      await startImpersonation(targetUser.id, targetUser.name, currentUser.name);
      await checkAuth();
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Erro ao iniciar impersonação.");
      setImpersonatingId(null);
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Usuários Globais (Plataforma)</h1>
          <p className={styles.subtitle}>Visão de todos os usuários através de todas as clínicas</p>
        </div>
        <button className={styles.btnNew} onClick={handleOpenCreate}>
          <span>+</span> Novo Usuário
        </button>
      </header>

      {error && <div className={styles.errorMessage}>{error}</div>}

      <div className={styles.tableCard}>
        {isLoading ? (
          <div className={styles.loadingState}>Carregando usuários...</div>
        ) : users.length === 0 ? (
          <div className={styles.emptyState}>Nenhum usuário cadastrado.</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Clínica Vinculada</th>
                <th>Perfil de Acesso</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className={styles.userCell}>
                      <div className={styles.avatar}>{u.name.charAt(0).toUpperCase()}</div>
                      <div className={styles.userInfo}>
                        <span className={styles.userName}>{u.name}</span>
                        <span className={styles.userEmail}>{u.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 500, color: "#334155", fontSize: "13px" }}>
                      {u.clinic_name || (u.is_superuser ? "Plataforma Global" : "-")}
                    </span>
                  </td>
                  <td>
                    <RoleBadge role={u.role} />
                  </td>
                  <td>
                    <span className={u.is_active ? styles.statusActive : styles.statusInactive}>
                      {u.is_active ? "● Ativo" : "○ Inativo"}
                    </span>
                  </td>
                  <td>
                    <div className={styles.actions}>
                      <button className={styles.btnAction} onClick={() => handleOpenEdit(u)}>
                        Editar
                      </button>
                      <button
                        className={styles.btnAction}
                        onClick={() => handleToggleStatus(u)}
                      >
                        {u.is_active ? "Desativar" : "Ativar"}
                      </button>
                      {!u.is_superuser && u.is_active && (
                        <button
                          className={styles.btnAction}
                          style={{ background: "#7c3aed", color: "#fff", borderColor: "#7c3aed" }}
                          disabled={impersonatingId === u.id}
                          onClick={() => handleImpersonate(u)}
                          title={`Visualizar sistema como ${u.name}`}
                        >
                          {impersonatingId === u.id ? "Entrando…" : "👁 Entrar como"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {isModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "12px",
              padding: "24px",
              width: "100%",
              maxWidth: "480px",
              boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
            }}
          >
            <h2 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "16px", color: "#0f172a" }}>
              {editingUser ? "Editar Usuário Global" : "Novo Usuário na Plataforma"}
            </h2>

            {modalError && (
              <div style={{ background: "#fee2e2", color: "#b91c1c", padding: "8px 12px", borderRadius: "6px", marginBottom: "16px", fontSize: "13px" }}>
                {modalError}
              </div>
            )}

            <form onSubmit={handleSaveUser} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Nome Completo *
                </label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                  placeholder="Ex: Dra. Mariana Silva"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  E-mail de Login *
                </label>
                <input
                  type="email"
                  required
                  disabled={!!editingUser}
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: editingUser ? "#64748b" : "#0f172a", backgroundColor: editingUser ? "#f1f5f9" : "#ffffff", fontSize: "14px" }}
                  placeholder="mariana@clinica.com"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Perfil de Acesso
                </label>
                <select
                  value={formRole}
                  onChange={(e) => setFormRole(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                >
                  <option value="admin" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Administrador de Clínica</option>
                  <option value="professional" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Profissional / Esteticista</option>
                  <option value="receptionist" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Recepcionista</option>
                  <option value="user" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Usuário Básico</option>
                  <option value="superadmin" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Super Admin Global</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Clínica Alvo
                </label>
                <select
                  value={formClinicId}
                  onChange={(e) => setFormClinicId(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                >
                  <option value="" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Nenhuma / Plataforma Global</option>
                  {clinics.map((c) => (
                    <option key={c.id} value={c.id} style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  style={{ padding: "8px 16px", borderRadius: "6px", border: "1px solid #cbd5e1", background: "#fff", cursor: "pointer", fontWeight: 600 }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  style={{ padding: "8px 16px", borderRadius: "6px", border: "none", background: "#4f46e5", color: "#fff", cursor: "pointer", fontWeight: 600 }}
                >
                  {formSubmitting ? "Salvando..." : "Salvar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
