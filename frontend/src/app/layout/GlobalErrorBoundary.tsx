import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

import { Logger } from "@/lib/telemetry/logger";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class GlobalErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    Logger.captureException(error, { extra: errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.href = "/";
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="page" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '100vh', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h2>Ops! Algo deu errado.</h2>
          <p className="page__subtitle">
            {this.state.error?.message || "Ocorreu um erro inesperado ao renderizar esta página."}
          </p>
          <button type="button" onClick={this.handleReset} className="button tap-target">
            Voltar ao Início
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
