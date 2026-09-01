import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/app/layout/AppLayout";
import { GlobalErrorBoundary } from "@/app/layout/GlobalErrorBoundary";
import { RequireAuth } from "@/app/layout/RequireAuth";
import { LandingPage } from "@/features/landing/LandingPage";
import { LoginPage } from "@/features/onboarding/LoginPage";
import { PatientsPage } from "@/features/patients/PatientsPage";
import { NewPatientPage } from "@/features/patients/NewPatientPage";
import { PatientImportPage } from "@/features/patients/PatientImportPage";
import { PatientDetailPage } from "@/features/patients/PatientDetailPage";
import { ProceduresPage } from "@/features/procedures/ProceduresPage";
import { NewProcedurePage } from "@/features/procedures/NewProcedurePage";
import { ProcedureDetailPage } from "@/features/procedures/ProcedureDetailPage";
import { NewSalePage } from "@/features/sales/NewSalePage";
import { NewPackageSalePage } from "@/features/sales/NewPackageSalePage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { RetentionPage } from "@/features/retention/RetentionPage";
import { AgendaPage } from "@/features/agenda/AgendaPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { SetupWizardPage } from "@/features/admin/SetupWizardPage";
import { AdminLayout } from "@/features/admin/AdminLayout";
import { AdminUsersPage } from "@/features/admin/AdminUsersPage";
import { SuperAdminLayout } from "@/features/admin/SuperAdminLayout";
import { SuperAdminClinicsPage } from "@/features/admin/SuperAdminClinicsPage";
import { SuperAdminUsersPage } from "@/features/admin/SuperAdminUsersPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/setup", element: <SetupWizardPage /> },
  {
    element: (
      <GlobalErrorBoundary>
        <RequireAuth />
      </GlobalErrorBoundary>
    ),
    children: [
      {
        path: "/super-admin",
        element: <SuperAdminLayout />,
        children: [
          { path: "clinicas", element: <SuperAdminClinicsPage /> },
          { path: "usuarios", element: <SuperAdminUsersPage /> },
          { index: true, element: <Navigate to="clinicas" replace /> },
        ]
      },
      {
        element: <AppLayout />,
        children: [
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/retornos", element: <RetentionPage /> },
          { path: "/pacientes", element: <PatientsPage /> },
          { path: "/pacientes/novo", element: <NewPatientPage /> },
          { path: "/pacientes/importar", element: <PatientImportPage /> },
          { path: "/pacientes/:id", element: <PatientDetailPage /> },
          { path: "/procedimentos", element: <ProceduresPage /> },
          { path: "/procedimentos/novo", element: <NewProcedurePage /> },
          { path: "/procedimentos/:id", element: <ProcedureDetailPage /> },
          { path: "/vendas/nova", element: <NewSalePage /> },
          { path: "/vendas/nova-pacote", element: <NewPackageSalePage /> },
          { path: "/agenda", element: <AgendaPage /> },
          { path: "/configuracoes", element: <SettingsPage /> },
          { path: "*", element: <Navigate to="/dashboard" replace /> },
        ],
      },
      {
        path: "/admin",
        element: <AdminLayout />,
        children: [
          { path: "usuarios", element: <AdminUsersPage /> },
          { index: true, element: <Navigate to="usuarios" replace /> },
        ],
      },
    ],
  },
]);
