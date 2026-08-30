from datetime import datetime
from uuid import UUID

from app.domain.bookings.enums import BookingStatus
from app.models.booking import Booking
from app.repositories.base import TenantRepository


class BookingRepository(TenantRepository[Booking]):
    model = Booking

    def get_by_id(self, booking_id: UUID) -> Booking | None:
        stmt = self._scoped().where(Booking.id == booking_id)
        return self._session.scalar(stmt)

    def list_in_range(
        self, start_dt: datetime, end_dt: datetime, status: BookingStatus | None = None
    ) -> list[Booking]:
        stmt = self._scoped().where(
            Booking.scheduled_at >= start_dt,
            Booking.scheduled_at <= end_dt,
        )
        if status:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.scheduled_at.asc())
        return list(self._session.scalars(stmt))

    def find_conflicts(
        self, scheduled_at: datetime, exclude_booking_id: UUID | None = None
    ) -> list[Booking]:
        stmt = self._scoped().where(
            Booking.scheduled_at == scheduled_at,
            Booking.status == BookingStatus.SCHEDULED,
        )
        if exclude_booking_id:
            stmt = stmt.where(Booking.id != exclude_booking_id)
        return list(self._session.scalars(stmt))
