from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from events.models import Event, EventSlot
from wallet.models import Wallet, WalletTransaction

from .models import Booking, Ticket


MAX_TICKETS_PER_BOOKING = 10


@transaction.atomic
def purchase_event(user, event_id, quantity=1, slot_id=None):

    # 1. Validate the requested quantity.
    if type(quantity) is not int:
        raise ValidationError("Quantity must be an integer.")

    if quantity < 1 or quantity > MAX_TICKETS_PER_BOOKING:
        raise ValidationError(
            "Quantity must be between 1 and 10."
        )

    # 2. Lock the wallet first.
    # Using the same lock order across services reduces deadlock risk.
    try:
        wallet = Wallet.objects.select_for_update().get(user=user)
    except Wallet.DoesNotExist:
        raise ValidationError(
            "Wallet not found. Open your wallet page first."
        )

    # 3. Lock the event inventory.
    try:
        event = Event.objects.select_for_update().get(pk=event_id)
    except Event.DoesNotExist:
        raise ValidationError("Event not found.")

    now = timezone.now()

    if not event.is_active:
        raise ValidationError("This event is inactive.")

    if event.end_time <= now:
        raise ValidationError("This event has already ended.")

    slot = None

    # 4. Validate inventory based on event type.
    if event.event_type == Event.EventType.TICKET:

        if slot_id is not None:
            raise ValidationError(
                "Ticket-based events cannot have a slot."
            )

        if event.booked_count + quantity > event.capacity:
            raise ValidationError(
                "Not enough tickets are available."
            )

    elif event.event_type == Event.EventType.SLOT:

        if quantity != 1:
            raise ValidationError(
                "Only one slot reservation is allowed per booking."
            )

        if slot_id is None:
            raise ValidationError("Please select a slot.")

        try:
            slot = EventSlot.objects.select_for_update().get(
                pk=slot_id,
                event=event,
            )
        except EventSlot.DoesNotExist:
            raise ValidationError(
                "Selected slot does not belong to this event."
            )

        if slot.start_time <= now:
            raise ValidationError(
                "This slot has already started."
            )

        if slot.booked_count >= slot.capacity:
            raise ValidationError(
                "This slot is fully booked."
            )

    else:
        raise ValidationError("Invalid event type.")

    # 5. Calculate the amount on the server.
    unit_price = event.price
    total_price = unit_price * quantity

    if wallet.balance < total_price:
        raise ValidationError(
            "Insufficient wallet balance."
        )

    # 6. Update the wallet.
    wallet.balance -= total_price
    wallet.save(update_fields=["balance"])

    # 7. Update inventory.
    if event.event_type == Event.EventType.TICKET:
        event.booked_count += quantity
        event.save(update_fields=["booked_count"])

    else:
        slot.booked_count += 1
        slot.save(update_fields=["booked_count"])

    # 8. Create the booking.
    booking = Booking.objects.create(
        user=user,
        event=event,
        slot=slot,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        status=Booking.BookingStatus.CONFIRMED,
    )

    # 9. Issue the tickets.
    Ticket.objects.bulk_create(
        [
            Ticket(
                booking=booking,
                status=Ticket.TicketStatus.ACTIVE,
            )
            for _ in range(quantity)
        ]
    )

    # 10. Record the wallet deduction.
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TransactionType.PURCHASE,
        amount=total_price,
        balance_after=wallet.balance,
        description=f"Booking #{booking.pk}: {event.title}",
    )

    return booking