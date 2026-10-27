import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Booking(models.Model):

    class BookingStatus(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    slot = models.ForeignKey(
        "events.EventSlot",
        on_delete=models.PROTECT,
        related_name="bookings",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.CONFIRMED,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="booking_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="booking_unit_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(total_price__gte=0),
                name="booking_total_price_nonnegative",
            ),
        ]

    def clean(self):
        super().clean()

        if self.event_id:
            if self.event.event_type == "slot" and not self.slot_id:
                raise ValidationError(
                    "Slot-based bookings must have a selected slot."
                )

            if self.event.event_type == "ticket" and self.slot_id:
                raise ValidationError(
                    "Ticket-based bookings cannot have a slot."
                )

            if self.slot_id and self.slot.event_id != self.event_id:
                raise ValidationError(
                    "Selected slot does not belong to this event."
                )

    def __str__(self):
        return f"Booking #{self.pk} - {self.event.title}"

class Ticket(models.Model):

    class TicketStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        CONSUMED = "consumed", "Consumed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="tickets",
    )

    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    consumed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Ticket {self.id} - {self.booking.event.title}"