import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { api } from "@/lib/http/client";
import { toast } from "@/ui/ToastContext";
import styles from "./AdminUsersPage.module.css";

export interface UserItem {
  id: string;
  name: string;
  email: string;
  role: "superadmin" | "admin" | "user" | "professional" | "receptionist";
  is_superuser: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

function RoleBadge({ role }: { role: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    superadmin: { label: "Super Admin", cls: styles.badgeRoleSuper },
    admin: { label: "Administrador", cls: styles.badgeRoleAdmin },
    professional: { label: "Profissional", cls: styles.badgeRoleProf },
    receptionist: { label: "Recepção", cls: styles.badgeRoleRecp },
    user: { label: "Usuário", cls: styles.badgeRoleUser },
  };

  const { label, cls } = map[role] || { label: role, cls: "" };
  return <span className={`${styles.badge} ${cls}`}>{label}</span>;
}

export function AdminUsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    role: "professional" as UserItem["role"],
  });
  const [isSaving, setIsSaving] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  async function fetchUsers() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<UserItem[]>("/users");
      setUsers(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar usuários.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchUsers();
  }, []);

  function handleOpenCreate() {
    setEditingUser(null);
    setFormData({
      name: "",
      email: "",
      role: "professional",
    });
    setModalError(null);
    setIsModalOpen(true);
  }

  function handleOpenEdit(u: UserItem) {
    setEditingUser(u);
    setFormData({
      name: u.name,
      email: u.email,
      role: u.role,
    });
    setModalError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingUser(null);
    setModalError(null);
  }

  async function handleSaveUser(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim()) {
      setModalError("Nome e e-mail são obrigatórios.");
      return;
    }

    setIsSaving(true);
    setModalError(null);

    try {
      if (editingUser) {
        await api.put(`/users/${editingUser.id}`, {
          name: formData.name.trim(),
          role: formData.role,
        });
        toast.success("Usuário atualizado com sucesso!");
      } else {
        await api.post("/users", {
          name: formData.name.trim(),
          email: formData.email.trim().toLowerCase(),
          role: formData.role,
        });
        toast.success("Usuário cadastrado com sucesso!");
      }
      setIsModalOpen(false);
      await fetchUsers();
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Erro ao salvar usuário.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleToggleStatus(targetUser: UserItem) {
    if (targetUser.id === currentUser?.id) {
      alert("Você não pode desativar seu próprio usuário.");
      return;
    }

    try {
      await api.put(`/users/${targetUser.id}`, {
        is_active: !targetUser.is_active,
      });
      toast.success(`Usuário ${!targetUser.is_active ? "ativado" : "desativado"} com sucesso!`);
      await fetchUsers();
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      } else {
        alert("Erro ao alterar status do usuário.");
      }
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Usuários do Sistema</h1>
          <p className={styles.subtitle}>Gerencie a equipe e níveis de acesso</p>
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
                    <RoleBadge role={u.role} />
                  </td>
                  <td>
                    <span className={u.is_active ? styles.statusActive : styles.statusInactive}>
                      {u.is_active ? "● Ativo" : "○ Inativo"}
                    </span>
                  </td>
                  <td>
                    <div className={styles.actions}>
                      <button
                        className={styles.btnAction}
                        onClick={() => handleOpenEdit(u)}
                      >
                        Editar
                      </button>
                      <button
                        className={styles.btnAction}
                        onClick={() => handleToggleStatus(u)}
                        disabled={currentUser?.id === u.id}
                        title={currentUser?.id === u.id ? "Não pode inativar a si mesmo" : ""}
                      >
                        {u.is_active ? "Desativar" : "Ativar"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal de Criação / Edição */}
      {isModalOpen && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>
                {editingUser ? "Editar Usuário" : "Novo Usuário"}
              </h2>
              <button className={styles.modalCloseBtn} onClick={closeModal}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveUser}>
              <div className={styles.modalBody}>
                {modalError && <div className={styles.errorMessage}>{modalError}</div>}

                <div className={styles.formGroup}>
                  <label className={styles.formLabel} htmlFor="userName">
                    Nome Completo
                  </label>
                  <input
                    id="userName"
                    className={styles.input}
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ex: Dra. Ana Paula"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel} htmlFor="userEmail">
                    E-mail
                  </label>
                  <input
                    id="userEmail"
                    className={styles.input}
                    type="email"
                    required
                    disabled={!!editingUser}
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="ana@clinica.com.br"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel} htmlFor="userRole">
                    Nível de Acesso
                  </label>
                  <select
                    id="userRole"
                    className={styles.select}
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value as UserItem["role"] })
                    }
                  >
                    <option value="user">Usuário Básico</option>
                    <option value="receptionist">Recepção</option>
                    <option value="professional">Profissional / Esteticista</option>
                    <option value="admin">Administrador</option>
                    <option value="superadmin">Super Admin</option>
                  </select>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button type="button" className={styles.btnCancel} onClick={closeModal}>
                  Cancelar
                </button>
                <button type="submit" className={styles.btnSave} disabled={isSaving}>
                  {isSaving ? "Salvando..." : "Salvar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
