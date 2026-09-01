"""Export API — Endpoints para exportação de dados em CSV (EPIC-S3-02, LGPD)."""

from fastapi import APIRouter, Response

from app.api.deps import ExportSvc

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/patients.csv")
def export_patients(svc: ExportSvc) -> Response:
    """Exporta lista de pacientes em formato CSV (UTF-8 com BOM para Excel)."""
    content = svc.export_patients_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="pacientes.csv"',
        },
    )


@router.get("/sales.csv")
def export_sales(svc: ExportSvc) -> Response:
    """Exporta histórico financeiro de vendas em formato CSV."""
    content = svc.export_sales_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="vendas.csv"',
        },
    )


@router.get("/sessions.csv")
def export_sessions(svc: ExportSvc) -> Response:
    """Exporta atendimentos e sessões em formato CSV."""
    content = svc.export_sessions_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="sessoes.csv"',
        },
    )
