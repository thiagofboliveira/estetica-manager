from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.coupon import Coupon


class CouponRepository:
    """Repositório de cupons promocionais da plataforma."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Coupon | None:
        clean = code.strip().lower()
        stmt = select(Coupon).where(func.lower(Coupon.code) == clean)
        return self._session.scalars(stmt).one_or_none()

    def get_by_id(self, coupon_id: UUID) -> Coupon | None:
        return self._session.scalars(
            select(Coupon).where(Coupon.id == coupon_id)
        ).one_or_none()

    def increment_redemption(self, coupon_id: UUID) -> None:
        """Incremento atômico para evitar race conditions (cupons são globais com RLS estrito)."""
        from app.db.session import unsafe_session_without_tenant

        with unsafe_session_without_tenant("increment coupon redemption") as sys_sess:
            stmt = (
                update(Coupon)
                .where(Coupon.id == coupon_id)
                .values(times_redeemed=Coupon.times_redeemed + 1)
            )
            sys_sess.execute(stmt)

    def add(self, coupon: Coupon) -> Coupon:
        self._session.add(coupon)
        self._session.flush()
        return coupon

    def flush(self) -> None:
        self._session.flush()
