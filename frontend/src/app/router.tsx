import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/app/layout/AppLayout";
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
import { ExpensesPage } from "@/features/expenses/ExpensesPage";
import { NewExpensePage } from "@/features/expenses/NewExpensePage";
import { ExpenseDetailPage } from "@/features/expenses/ExpenseDetailPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { PlaceholderPage } from "@/ui/PlaceholderPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> }, // F-013
      { path: "retornos", element: <PlaceholderPage title="Quem devo chamar hoje?" /> }, // F-015
      { path: "pacientes", element: <PatientsPage /> }, // F-011
      { path: "pacientes/novo", element: <NewPatientPage /> }, // F-011
      { path: "pacientes/:id", element: <PatientDetailPage /> }, // F-011
      { path: "procedimentos", element: <ProceduresPage /> }, // F-012
      { path: "procedimentos/novo", element: <NewProcedurePage /> }, // F-012
      { path: "procedimentos/:id", element: <ProcedureDetailPage /> }, // F-012
      { path: "vendas/nova", element: <NewSalePage /> }, // F-014
      { path: "vendas/nova-pacote", element: <NewPackageSalePage /> }, // F-014b
      { path: "agenda", element: <PlaceholderPage title="Agenda" /> }, // F-017
      { path: "configuracoes", element: <SettingsPage /> }, // hub mínimo p/ F-012b; F-012a segue placeholder
      { path: "configuracoes/despesas", element: <ExpensesPage /> }, // F-012b
      { path: "configuracoes/despesas/nova", element: <NewExpensePage /> }, // F-012b
      { path: "configuracoes/despesas/:id", element: <ExpenseDetailPage /> }, // F-012b
    ],
  },
]);
