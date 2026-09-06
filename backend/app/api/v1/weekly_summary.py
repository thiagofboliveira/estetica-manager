"""API endpoints para o resumo semanal (A-12 / V5-01 / V5-02).

Rotas:
- GET /weekly-summary: Geração do resumo semanal da profissional autenticada (V5-01).
- PATCH /weekly-summary/settings: Opt-in / opt-out do resumo nas configurações (V5-02).
- GET /public/weekly-summary/unsubscribe: Descadastro em 1 clique via link seguro no WhatsApp (V5-02).
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.api.deps import WeeklySummarySvc
from app.core.config import settings
from app.db.session import unsafe_session_without_tenant
from app.models.professional import Professional
from app.schemas.weekly_summary import (
    WeeklySummaryOut,
    WeeklySummarySettingsUpdate,
    WeeklySummaryUnsubscribeOut,
)

router = APIRouter(tags=["weekly-summary"])


@router.get("/weekly-summary", response_model=WeeklySummaryOut)
def get_weekly_summary(
    svc: WeeklySummarySvc,
    use_current_week: bool = Query(
        default=False,
        description="Se true, calcula a semana corrente até hoje; se false, calcula a semana passada fechada.",
    ),
    reference_date: date | None = Query(
        default=None,
        description="Data de referência para testes/retroativo (fuso da profissional).",
    ),
) -> WeeklySummaryOut:
    """Retorna o resumo consolidado da semana (faturamento, lucro real, atendimentos e pacientes a chamar)."""
    return svc.get_summary(reference_date=reference_date, use_current_week=use_current_week)


@router.patch("/weekly-summary/settings", response_model=WeeklySummarySettingsUpdate)
def update_weekly_summary_settings(
    body: WeeklySummarySettingsUpdate,
    svc: WeeklySummarySvc,
) -> WeeklySummarySettingsUpdate:
    """Atualiza o opt-in / opt-out de recebimento do resumo semanal."""
    prof = svc.update_settings(body.weekly_summary_enabled)
    return WeeklySummarySettingsUpdate(weekly_summary_enabled=prof.weekly_summary_enabled)


@router.get(
    "/public/weekly-summary/unsubscribe",
    response_model=WeeklySummaryUnsubscribeOut,
)
def unsubscribe_weekly_summary(
    token: str = Query(..., min_length=10, description="Token seguro de descadastro da profissional"),
    request: Request = None,
) -> Response:
    """Descadastro em 1 clique (opt-out) acessível publicamente via token opaco sem expor login."""
    with unsafe_session_without_tenant("weekly_summary public unsubscribe") as db_sess:
        prof = db_sess.scalars(
            select(Professional).where(Professional.weekly_summary_token == token.strip())
        ).one_or_none()

        if prof is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link de cancelamento inválido ou expirado.",
            )

        prof.weekly_summary_enabled = False
        db_sess.add(prof)
        db_sess.commit()

        accept_header = request.headers.get("accept", "") if request else ""
        if "text/html" in accept_header:
            html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Resumo Semanal Cancelado — Lumina</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 16px; color: #1e293b; }}
        .card {{ background: #fff; max-width: 440px; padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; border: 1px solid #e2e8f0; }}
        h1 {{ font-size: 1.25rem; color: #0f172a; margin-bottom: 8px; }}
        p {{ font-size: 0.95rem; color: #64748b; line-height: 1.5; }}
        .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #d97706; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="card">
        <div style="font-size: 40px; margin-bottom: 12px;">✅</div>
        <h1>Resumo semanal pausado</h1>
        <p>Você cancelou o recebimento do resumo semanal no WhatsApp com sucesso. Você pode reativá-lo a qualquer momento nas configurações da sua clínica.</p>
        <a href="{settings.FRONTEND_URL}/financeiro" class="btn">Voltar para o Sistema</a>
    </div>
</body>
</html>"""
            return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)

        return WeeklySummaryUnsubscribeOut(
            status="unsubscribed",
            message="Resumo semanal cancelado com sucesso.",
        )
