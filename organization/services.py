from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking, Ticket


@transaction.atomic
def consume_ticket(organization_id, ticket_id):

    try:
        ticket = (
            Ticket.objects.select_for_update()
            .select_related("booking__event")
            .get(pk=ticket_id)
        )
    except (Ticket.DoesNotExist, ValueError, TypeError):
        raise ValidationError("Invalid ticket ID.")

    if ticket.booking.event.organization_id != organization_id:
        raise ValidationError(
            "This ticket does not belong to your organization."
        )

    if ticket.booking.status != Booking.BookingStatus.CONFIRMED:
        raise ValidationError("Booking is not confirmed.")

    if ticket.status != Ticket.TicketStatus.ACTIVE:
        raise ValidationError(
            "Ticket has already been used or cancelled."
        )

    now = timezone.now()

    event = ticket.booking.event

    if event.event_type == event.EventType.SLOT:
        if ticket.booking.slot_id is None:
            raise ValidationError("Ticket has no reserved slot.")

        start_time = ticket.booking.slot.start_time
        end_time = ticket.booking.slot.end_time
    else:
        start_time = event.start_time
        end_time = event.end_time

    if not (start_time <= now <= end_time):
        raise ValidationError(
            "Ticket can only be consumed during its event or slot."
        )

    ticket.status = Ticket.TicketStatus.CONSUMED
    ticket.consumed_at = now

    ticket.save(
        update_fields=["status", "consumed_at"]
    )

    return ticket