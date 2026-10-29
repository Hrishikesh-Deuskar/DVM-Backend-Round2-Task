from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .forms import TicketPurchaseForm, SlotBookingForm
from .services import purchase_event

from django.shortcuts import get_object_or_404

from .models import Booking, Ticket

@login_required
@require_POST
def purchase(request, event_id):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    event_type = request.POST.get("event_type")

    if event_type == "ticket":
        form = TicketPurchaseForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid ticket quantity.")
            return redirect("events:event_detail", event_id=event_id)

        quantity = form.cleaned_data["quantity"]
        slot_id = None

    elif event_type == "slot":
        form = SlotBookingForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid slot selection.")
            return redirect("events:event_detail", event_id=event_id)

        quantity = 1
        slot_id = form.cleaned_data["slot_id"]

    else:
        messages.error(request, "Invalid booking request.")
        return redirect("events:event_detail", event_id=event_id)

    try:
        booking = purchase_event(
            user=request.user,
            event_id=event_id,
            quantity=quantity,
            slot_id=slot_id,
        )

    except ValidationError as error:
        messages.error(
            request,
            "; ".join(error.messages),
        )
        return redirect("events:event_detail", event_id=event_id)

    except DatabaseError:
        messages.error(
            request,
            "Booking failed. Please try again.",
        )
        return redirect("events:event_detail", event_id=event_id)

    messages.success(
        request,
        f"Booking #{booking.pk} confirmed!",
    )

    return redirect("bookings:detail", booking_id=booking.pk)

@login_required
def booking_detail(request, booking_id):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    from .models import Booking

    booking = get_object_or_404(
        Booking.objects.select_related(
            "event",
            "slot",
        ).prefetch_related("tickets"),
        pk=booking_id,
        user=request.user,
    )

    return render(
        request,
        "bookings/booking_detail.html",
        {"booking": booking},
    )

@login_required
def booking_history(request):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related("event", "slot")
        .prefetch_related("tickets")
        .order_by("-created_at")
    )

    return render(
        request,
        "bookings/booking_history.html",
        {"bookings": bookings},
    )

@login_required
def active_tickets(request):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    tickets = (
        Ticket.objects.filter(
            booking__user=request.user,
            booking__status=Booking.BookingStatus.CONFIRMED,
            status=Ticket.TicketStatus.ACTIVE,
        )
        .select_related(
            "booking",
            "booking__event",
            "booking__slot",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "bookings/active_tickets.html",
        {"tickets": tickets},
    )