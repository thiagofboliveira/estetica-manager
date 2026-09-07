import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/app/layout/AppLayout";
import { GlobalErrorBoundary } from "@/app/layout/GlobalErrorBoundary";
import { RequireAuth } from "@/app/layout/RequireAuth";
import { LandingPage } from "@/features/landing/LandingPage";
import { HowWeCalculatePage } from "@/features/landing/HowWeCalculatePage";
import { LoginPage } from "@/features/onboarding/LoginPage";
import { ResetPasswordPage } from "@/features/onboarding/ResetPasswordPage";
import { AuthRecoveryListener } from "@/app/layout/AuthRecoveryListener";
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
import { ModoOcupadoPage } from "@/features/agenda/ModoOcupadoPage";
import { FinancialSettingsPage } from "@/features/settings/FinancialSettingsPage";
import { FixedExpensesPage } from "@/features/fixed-expenses/FixedExpensesPage";
import { PriceSimulatorPage } from "@/features/simulator/PriceSimulatorPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { EstoquePage } from "@/features/vials/EstoquePage";
import { WhatsAppCampaignsPage } from "@/features/whatsapp-campaigns/WhatsAppCampaignsPage";
import { SetupWizardPage } from "@/features/admin/SetupWizardPage";

import { AdminLayout } from "@/features/admin/AdminLayout";
import { AdminUsersPage } from "@/features/admin/AdminUsersPage";
import { SuperAdminLayout } from "@/features/admin/SuperAdminLayout";
import { SuperAdminClinicsPage } from "@/features/admin/SuperAdminClinicsPage";
import { SuperAdminUsersPage } from "@/features/admin/SuperAdminUsersPage";

import { TermsOfServicePage } from "@/features/legal/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/features/legal/PrivacyPolicyPage";
import { PublicBookingPage } from "@/features/public-booking/PublicBookingPage";
import { BookingManagementPage } from "@/features/public-booking/BookingManagementPage";
import { AnamnesisPage } from "@/features/anamnesis/AnamnesisPage";
import { PublicAnamnesisPage } from "@/features/anamnesis/PublicAnamnesisPage";

export const router = createBrowserRouter([
  {
    // G-08a: o boundary agora envolve a árvore INTEIRA, não só a
    // autenticada — /login e /setup são as telas do primeiro contato;
    // um erro de render nelas dava tela branca sem recuperação antes.
    element: <GlobalErrorBoundary />,
    children: [
      {
        element: <AuthRecoveryListener />,
        children: [
          { path: "/", element: <LandingPage /> },
          { path: "/como-calculamos", element: <HowWeCalculatePage /> },
          { path: "/termos", element: <TermsOfServicePage /> },
          { path: "/privacidade", element: <PrivacyPolicyPage /> },
          { path: "/login", element: <LoginPage /> },
          { path: "/redefinir-senha", element: <ResetPasswordPage /> },
          { path: "/reset-password", element: <Navigate to="/redefinir-senha" replace /> },
          { path: "/setup", element: <SetupWizardPage /> },
          { path: "/agendar/:slug", element: <PublicBookingPage /> },
          { path: "/agendamento/:id", element: <BookingManagementPage /> },
          { path: "/anamnese/:token", element: <PublicAnamnesisPage /> },
          {
            element: <RequireAuth />,
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
              { path: "/disparos-whatsapp", element: <WhatsAppCampaignsPage /> },
              { path: "/pacientes", element: <PatientsPage /> },
              { path: "/pacientes/novo", element: <NewPatientPage /> },
              { path: "/pacientes/importar", element: <PatientImportPage /> },
              { path: "/pacientes/:id", element: <PatientDetailPage /> },
              { path: "/anamnese", element: <AnamnesisPage /> },
              { path: "/procedimentos", element: <ProceduresPage /> },
              { path: "/procedimentos/novo", element: <NewProcedurePage /> },
              { path: "/procedimentos/:id", element: <ProcedureDetailPage /> },
              { path: "/estoque", element: <EstoquePage /> },
              { path: "/vendas/nova", element: <NewSalePage /> },
              { path: "/vendas/nova-pacote", element: <NewPackageSalePage /> },
              { path: "/agenda", element: <AgendaPage /> },
              { path: "/agenda/rapido", element: <ModoOcupadoPage /> },
              { path: "/financeiro", element: <FinancialSettingsPage /> },
              { path: "/despesas-fixas", element: <FixedExpensesPage /> },
              { path: "/simulador", element: <PriceSimulatorPage /> },
              { path: "/relatorios", element: <ReportsPage /> },
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
        ],
      },
    ],
  },
]);

