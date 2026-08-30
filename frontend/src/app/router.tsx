import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/app/layout/AppLayout";
import { GlobalErrorBoundary } from "@/app/layout/GlobalErrorBoundary";
import { LandingPage } from "@/features/landing/LandingPage";
import { LoginPage } from "@/features/onboarding/LoginPage";
import { PatientsPage } from "@/features/patients/PatientsPage";
import { NewPatientPage } from "@/features/patients/NewPatientPage";
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

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  {
    element: (
      <GlobalErrorBoundary>
        <AppLayout />
      </GlobalErrorBoundary>
    ),
    children: [
      { path: "/dashboard", element: <DashboardPage /> }, // F-013
      { path: "/retornos", element: <RetentionPage /> }, // F-015, F-015a, F-015b, F-015c
      { path: "/pacientes", element: <PatientsPage /> }, // F-011
      { path: "/pacientes/novo", element: <NewPatientPage /> }, // F-011
      { path: "/pacientes/:id", element: <PatientDetailPage /> }, // F-011, F-016
      { path: "/procedimentos", element: <ProceduresPage /> }, // F-012, F-012c
      { path: "/procedimentos/novo", element: <NewProcedurePage /> }, // F-012
      { path: "/procedimentos/:id", element: <ProcedureDetailPage /> }, // F-012
      { path: "/vendas/nova", element: <NewSalePage /> }, // F-014, F-019a
      { path: "/vendas/nova-pacote", element: <NewPackageSalePage /> }, // F-014b
      { path: "/agenda", element: <AgendaPage /> }, // F-017, F-017a, F-018, F-018a, F-019
      { path: "/configuracoes", element: <SettingsPage /> }, // F-012a, F-012b, F-021a
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
