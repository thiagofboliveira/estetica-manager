import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "@/app/layout/AppLayout";
import { LoginPage } from "@/features/onboarding/LoginPage";
import { PatientsPage } from "@/features/patients/PatientsPage";
import { NewPatientPage } from "@/features/patients/NewPatientPage";
import { PatientDetailPage } from "@/features/patients/PatientDetailPage";
import { ProceduresPage } from "@/features/procedures/ProceduresPage";
import { NewProcedurePage } from "@/features/procedures/NewProcedurePage";
import { ProcedureDetailPage } from "@/features/procedures/ProcedureDetailPage";
import { PlaceholderPage } from "@/ui/PlaceholderPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <PlaceholderPage title="Dashboard" /> }, // F-013
      { path: "retornos", element: <PlaceholderPage title="Quem devo chamar hoje?" /> }, // F-015
      { path: "pacientes", element: <PatientsPage /> }, // F-011
      { path: "pacientes/novo", element: <NewPatientPage /> }, // F-011
      { path: "pacientes/:id", element: <PatientDetailPage /> }, // F-011
      { path: "procedimentos", element: <ProceduresPage /> }, // F-012
      { path: "procedimentos/novo", element: <NewProcedurePage /> }, // F-012
      { path: "procedimentos/:id", element: <ProcedureDetailPage /> }, // F-012
      { path: "agenda", element: <PlaceholderPage title="Agenda" /> }, // F-017
      { path: "configuracoes", element: <PlaceholderPage title="Configurações" /> }, // F-012a
    ],
  },
]);
