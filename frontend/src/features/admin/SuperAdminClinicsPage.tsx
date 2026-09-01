import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./SuperAdminClinicsPage.module.css";
import { api } from "@/lib/http/client";
import { useAuth } from "@/lib/auth/AuthContext";
import { startImpersonation } from "@/lib/auth/impersonation";
import { toast } from "@/ui/ToastContext";

interface ClinicItem {
  id: string;
  name: string;
  document: string | null;
  phone: string | null;
  email: string | null;
  plan: string;
  is_active: boolean;
  users_count: number;
  created_at: string;
}

export function SuperAdminClinicsPage() {
  const navigate = useNavigate();
  const { user: currentUser, checkAuth } = useAuth();
  const [clinics, setClinics] = useState<ClinicItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [impersonatingId, setImpersonatingId] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingClinic, setEditingClinic] = useState<ClinicItem | null>(null);
  const [formName, setFormName] = useState("");
  const [formDoc, setFormDoc] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPlan, setFormPlan] = useState("standard");
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  async function fetchClinics() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<ClinicItem[]>("/super-admin/clinics");
      setClinics(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar clínicas.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchClinics();
  }, []);

  function handleOpenCreate() {
    setEditingClinic(null);
    setFormName("");
    setFormDoc("");
    setFormPhone("");
    setFormEmail("");
    setFormPlan("standard");
    setModalError(null);
    setIsModalOpen(true);
  }

  function handleOpenEdit(clinic: ClinicItem) {
    setEditingClinic(clinic);
    setFormName(clinic.name);
    setFormDoc(clinic.document || "");
    setFormPhone(clinic.phone || "");
    setFormEmail(clinic.email || "");
    setFormPlan(clinic.plan || "standard");
    setModalError(null);
    setIsModalOpen(true);
  }

  async function handleSaveClinic(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim()) {
      setModalError("Nome da clínica é obrigatório.");
      return;
    }

    setFormSubmitting(true);
    setModalError(null);

    const payload = {
      name: formName.trim(),
      document: formDoc.trim() || null,
      phone: formPhone.trim() || null,
      email: formEmail.trim() || null,
      plan: formPlan,
    };

    try {
      if (editingClinic) {
        await api.put(`/super-admin/clinics/${editingClinic.id}`, payload);
        toast.success("Clínica atualizada com sucesso!");
      } else {
        await api.post("/super-admin/clinics", payload);
        toast.success("Clínica cadastrada com sucesso!");
      }
      setIsModalOpen(false);
      await fetchClinics();
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Erro ao salvar clínica.");
    } finally {
      setFormSubmitting(false);
    }
  }

  async function handleToggle(id: string, currentStatus: boolean) {
    try {
      if (currentStatus) {
        await api.del(`/super-admin/clinics/${id}`);
        toast.success("Clínica desativada com sucesso!");
      } else {
        await api.put(`/super-admin/clinics/${id}`, { is_active: true });
        toast.success("Clínica ativada com sucesso!");
      }
      await fetchClinics();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Erro ao alterar status da clínica.");
    }
  }

  async function handleImpersonateClinic(clinic: ClinicItem) {
    if (!currentUser) return;
    setImpersonatingId(clinic.id);
    try {
      // Busca o primeiro usuário da clínica (não superadmin)
      const allUsers = await api.get<Array<{ id: string; name: string; role: string; clinic_id: string | null; is_superuser: boolean }>>("/super-admin/users");
      const clinicUser = allUsers.find(
        (u) => u.clinic_id === clinic.id && !u.is_superuser,
      );
      if (!clinicUser) {
        alert(`Nenhum usuário encontrado para a clínica "${clinic.name}". Crie um usuário antes de entrar como ela.`);
        setImpersonatingId(null);
        return;
      }
      await startImpersonation(clinicUser.id, `${clinicUser.name} (${clinic.name})`, currentUser.name);
      await checkAuth();
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Erro ao entrar como clínica.");
      setImpersonatingId(null);
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Clínicas (Tenants)</h1>
          <p className={styles.subtitle}>Gerencie as clínicas cadastradas na plataforma SaaS</p>
        </div>
        <button className={styles.btnNew} onClick={handleOpenCreate}>
          <span>+</span> Nova Clínica
        </button>
      </header>

      {error && <div style={{ color: "#ef4444", marginBottom: "16px" }}>{error}</div>}

      <div className={styles.tableCard}>
        {isLoading ? (
          <div style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>Carregando clínicas...</div>
        ) : clinics.length === 0 ? (
          <div style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>Nenhuma clínica cadastrada.</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Clínica</th>
                <th>Plano</th>
                <th>Status</th>
                <th>Usuários</th>
                <th>Cadastro</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {clinics.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div className={styles.clinicName}>{c.name}</div>
                    {c.document && <div className={styles.clinicDoc}>{c.document}</div>}
                  </td>
                  <td>
                    <span style={{ textTransform: "capitalize", fontWeight: 600, fontSize: "13px" }}>
                      {c.plan}
                    </span>
                  </td>
                  <td>
                    <span className={c.is_active ? styles.statusActive : styles.statusInactive}>
                      {c.is_active ? "● Ativa" : "○ Inativa"}
                    </span>
                  </td>
                  <td>{c.users_count}</td>
                  <td>{new Date(c.created_at).toLocaleDateString("pt-BR")}</td>
                  <td>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      <button className={styles.btnAction} onClick={() => handleOpenEdit(c)}>
                        Editar
                      </button>
                      <button
                        className={styles.btnAction}
                        onClick={() => handleToggle(c.id, c.is_active)}
                      >
                        {c.is_active ? "Desativar" : "Ativar"}
                      </button>
                      {c.is_active && c.users_count > 0 && (
                        <button
                          className={styles.btnAction}
                          style={{ background: "#7c3aed", color: "#fff", borderColor: "#7c3aed" }}
                          disabled={impersonatingId === c.id}
                          onClick={() => handleImpersonateClinic(c)}
                          title={`Visualizar sistema como gerente de ${c.name}`}
                        >
                          {impersonatingId === c.id ? "Entrando…" : "👁 Entrar como"}
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
              {editingClinic ? "Editar Clínica" : "Nova Clínica"}
            </h2>

            {modalError && (
              <div style={{ background: "#fee2e2", color: "#b91c1c", padding: "8px 12px", borderRadius: "6px", marginBottom: "16px", fontSize: "13px" }}>
                {modalError}
              </div>
            )}

            <form onSubmit={handleSaveClinic} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Nome da Clínica *
                </label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                  placeholder="Ex: Lumière Estética"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  CNPJ / CPF
                </label>
                <input
                  type="text"
                  value={formDoc}
                  onChange={(e) => setFormDoc(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                  placeholder="00.000.000/0001-00"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Telefone / WhatsApp
                </label>
                <input
                  type="text"
                  value={formPhone}
                  onChange={(e) => setFormPhone(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                  placeholder="(11) 99999-9999"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  E-mail de Contato
                </label>
                <input
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                  placeholder="contato@clinica.com"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Plano SaaS
                </label>
                <select
                  value={formPlan}
                  onChange={(e) => setFormPlan(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a", backgroundColor: "#ffffff", fontSize: "14px" }}
                >
                  <option value="standard" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Standard</option>
                  <option value="pro" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Pro</option>
                  <option value="enterprise" style={{ color: "#0f172a", backgroundColor: "#ffffff" }}>Enterprise</option>
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
