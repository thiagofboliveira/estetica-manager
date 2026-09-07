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
      await startImpersonation(targetUser.id, targetUser.name, currentUser.name, currentUser.id);
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
          <>
            {/* Tabela para Desktop */}
            <div className={styles.tableWrap}>
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
                              className={`${styles.btnAction} ${styles.btnActionImpersonate}`}
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
            </div>

            {/* Lista em Cards para Mobile */}
            <div className={styles.mobileCardList}>
              {users.map((u) => (
                <div className={styles.userCard} key={u.id}>
                  <div className={styles.userCardHeader}>
                    <div className={styles.userCell}>
                      <div className={styles.avatar}>{u.name.charAt(0).toUpperCase()}</div>
                      <div className={styles.userInfo}>
                        <span className={styles.userName}>{u.name}</span>
                        <span className={styles.userEmail}>{u.email}</span>
                      </div>
                    </div>
                    <span className={u.is_active ? styles.statusActive : styles.statusInactive}>
                      {u.is_active ? "● Ativo" : "○ Inativo"}
                    </span>
                  </div>

                  <div className={styles.userCardDetails}>
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>Perfil:</span>
                      <RoleBadge role={u.role} />
                    </div>
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>Clínica:</span>
                      <span className={styles.detailValue}>
                        {u.clinic_name || (u.is_superuser ? "Plataforma Global" : "-")}
                      </span>
                    </div>
                  </div>

                  <div className={styles.userCardActions}>
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
                        className={`${styles.btnAction} ${styles.btnActionImpersonate}`}
                        disabled={impersonatingId === u.id}
                        onClick={() => handleImpersonate(u)}
                        title={`Visualizar sistema como ${u.name}`}
                      >
                        {impersonatingId === u.id ? "Entrando…" : "👁 Entrar como"}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {isModalOpen && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalCard}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>
                {editingUser ? "Editar Usuário Global" : "Novo Usuário na Plataforma"}
              </h2>
              <button
                type="button"
                className={styles.modalCloseBtn}
                onClick={() => setIsModalOpen(false)}
                aria-label="Fechar modal"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div style={{ margin: "16px 20px 0" }} className={styles.errorMessage}>
                {modalError}
              </div>
            )}

            <form onSubmit={handleSaveUser}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    Nome Completo *
                  </label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className={styles.input}
                    placeholder="Ex: Dra. Mariana Silva"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    E-mail de Login *
                  </label>
                  <input
                    type="email"
                    required
                    disabled={!!editingUser}
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    className={styles.input}
                    placeholder="mariana@clinica.com"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    Perfil de Acesso
                  </label>
                  <select
                    value={formRole}
                    onChange={(e) => setFormRole(e.target.value)}
                    className={styles.select}
                  >
                    <option value="admin">Administrador de Clínica</option>
                    <option value="professional">Profissional / Esteticista</option>
                    <option value="receptionist">Recepcionista</option>
                    <option value="user">Usuário Básico</option>
                    <option value="superadmin">Super Admin Global</option>
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    Clínica Alvo
                  </label>
                  <select
                    value={formClinicId}
                    onChange={(e) => setFormClinicId(e.target.value)}
                    className={styles.select}
                  >
                    <option value="">Nenhuma / Plataforma Global</option>
                    {clinics.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className={styles.btnCancel}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className={styles.btnSave}
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
