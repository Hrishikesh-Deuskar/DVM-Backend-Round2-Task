from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.permissions import require_organization_membership
from events.models import Event

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from .forms import EventForm

from events.models import EventSlot
from .forms import EventForm, EventSlotForm

from django.core.exceptions import ValidationError

from django.db import DatabaseError

from .forms import TicketConsumeForm
from .services import consume_ticket

from decimal import Decimal

from django.db.models import Count, Sum
from bookings.models import Booking, Ticket


@login_required
def dashboard(request, organization_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
    )

    events = (
        Event.objects.filter(
            organization_id=organization_id
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "organization/dashboard.html",
        {
            "organization": membership.organization,
            "membership": membership,
            "events": events,
        },
    )

@login_required
def event_list(request, organization_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
    )

    events = Event.objects.filter(
        organization_id=organization_id
    ).order_by("-created_at")

    return render(
        request,
        "organization/event_list.html",
        {
            "organization": membership.organization,
            "membership": membership,
            "events": events,
        },
    )


@login_required
def event_detail(request, organization_id, event_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
    )

    event = get_object_or_404(
        Event.objects.prefetch_related("slots"),
        pk=event_id,
        organization_id=organization_id,
    )

    return render(
        request,
        "organization/event_detail.html",
        {
            "organization": membership.organization,
            "membership": membership,
            "event": event,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def event_create(request, organization_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
        manager_only=True,
    )

    if request.method == "POST":
        form = EventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)

            event.organization = membership.organization
            event.booked_count = 0

            event.save()

            messages.success(
                request,
                "Event created successfully.",
            )

            return redirect(
                "organization:event_detail",
                organization_id=organization_id,
                event_id=event.pk,
            )

    else:
        form = EventForm()

    return render(
        request,
        "organization/event_form.html",
        {
            "organization": membership.organization,
            "form": form,
            "heading": "Create Event",
        },
    )

@login_required
@require_http_methods(["GET", "POST"])
def event_edit(request, organization_id, event_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
        manager_only=True,
    )

    with transaction.atomic():
        event = get_object_or_404(
            Event.objects.select_for_update(),
            pk=event_id,
            organization_id=organization_id,
        )

        has_bookings = event.bookings.exists()

        if request.method == "POST":
            if has_bookings:
                form = EventForm(
                    request.POST,
                    instance=event,
                )

                locked_fields = [
                    "title",
                    "event_type",
                    "price",
                    "start_time",
                    "end_time",
                    "capacity",
                ]

                for field in locked_fields:
                    form.fields[field].disabled = True
            else:
                form = EventForm(
                    request.POST,
                    instance=event,
                )

            if form.is_valid():
                form.save()

                messages.success(
                    request,
                    "Event updated successfully.",
                )

                return redirect(
                    "organization:event_detail",
                    organization_id=organization_id,
                    event_id=event.pk,
                )

        else:
            form = EventForm(instance=event)

            if has_bookings:
                for field in [
                    "title",
                    "event_type",
                    "price",
                    "start_time",
                    "end_time",
                    "capacity",
                ]:
                    form.fields[field].disabled = True

    return render(
        request,
        "organization/event_form.html",
        {
            "organization": membership.organization,
            "form": form,
            "heading": "Edit Event",
        },
    )

@login_required
@require_http_methods(["GET", "POST"])
def slot_create(request, organization_id, event_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
        manager_only=True,
    )

    event = get_object_or_404(
        Event,
        pk=event_id,
        organization_id=organization_id,
        event_type=Event.EventType.SLOT,
    )

    if request.method == "POST":
        form = EventSlotForm(request.POST)

        if form.is_valid():
            slot = form.save(commit=False)
            slot.event = event

            try:
                slot.full_clean()
            except ValidationError as error:
                form.add_error(None, error)
            else:
                slot.save()

                messages.success(request, "Slot created.")

                return redirect(
                    "organization:event_detail",
                    organization_id=organization_id,
                    event_id=event_id,
                )

    else:
        form = EventSlotForm()

    return render(
        request,
        "organization/slot_form.html",
        {
            "organization": membership.organization,
            "event": event,
            "form": form,
            "heading": "Create Slot",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def slot_edit(request, organization_id, event_id, slot_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
        manager_only=True,
    )

    with transaction.atomic():
        slot = get_object_or_404(
            EventSlot.objects.select_for_update().select_related("event"),
            pk=slot_id,
            event_id=event_id,
            event__organization_id=organization_id,
            event__event_type=Event.EventType.SLOT,
        )

        if request.method == "POST":
            form = EventSlotForm(request.POST, instance=slot)

            if slot.booked_count > 0:
                form.fields["start_time"].disabled = True
                form.fields["end_time"].disabled = True

            if form.is_valid():
                updated_slot = form.save(commit=False)
                updated_slot.event = slot.event

                try:
                    updated_slot.full_clean()
                except ValidationError as error:
                    form.add_error(None, error)
                else:
                    updated_slot.save()

                    messages.success(request, "Slot updated.")

                    return redirect(
                        "organization:event_detail",
                        organization_id=organization_id,
                        event_id=event_id,
                    )

        else:
            form = EventSlotForm(instance=slot)

            if slot.booked_count > 0:
                form.fields["start_time"].disabled = True
                form.fields["end_time"].disabled = True

    return render(
        request,
        "organization/slot_form.html",
        {
            "organization": membership.organization,
            "event": slot.event,
            "form": form,
            "heading": "Edit Slot",
        },
    )

@login_required
@require_http_methods(["GET", "POST"])
def ticket_consume(request, organization_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
    )

    if request.method == "POST":
        form = TicketConsumeForm(request.POST)

        if form.is_valid():
            try:
                ticket = consume_ticket(
                    organization_id,
                    form.cleaned_data["ticket_id"],
                )
            except ValidationError as error:
                for message in error.messages:
                    form.add_error(None, message)
            except DatabaseError:
                form.add_error(
                    None,
                    "Database error. Please try again.",
                )
            else:
                messages.success(
                    request,
                    f"Ticket {ticket.pk} consumed successfully.",
                )

                return redirect(
                    "organization:ticket_consume",
                    organization_id=organization_id,
                )

    else:
        form = TicketConsumeForm()

    return render(
        request,
        "organization/ticket_consume.html",
        {
            "organization": membership.organization,
            "form": form,
        },
    )

@login_required
def analytics(request, organization_id):

    membership = require_organization_membership(
        request.user,
        organization_id,
    )

    events = Event.objects.filter(
        organization_id=organization_id
    )

    confirmed_bookings = Booking.objects.filter(
        event__organization_id=organization_id,
        status=Booking.BookingStatus.CONFIRMED,
    )

    totals = confirmed_bookings.aggregate(
        booking_count=Count("id"),
        tickets_sold=Sum("quantity"),
        revenue=Sum("total_price"),
    )

    consumed_count = Ticket.objects.filter(
        booking__event__organization_id=organization_id,
        booking__status=Booking.BookingStatus.CONFIRMED,
        status=Ticket.TicketStatus.CONSUMED,
    ).count()

    event_sales = (
        confirmed_bookings
        .values("event__title")
        .annotate(
            bookings=Count("id"),
            tickets=Sum("quantity"),
            revenue=Sum("total_price"),
        )
        .order_by("-revenue")
    )

    return render(
        request,
        "organization/analytics.html",
        {
            "organization": membership.organization,
            "event_count": events.count(),
            "booking_count": totals["booking_count"] or 0,
            "tickets_sold": totals["tickets_sold"] or 0,
            "revenue": totals["revenue"] or Decimal("0.00"),
            "consumed_count": consumed_count,
            "event_sales": event_sales,
        },
    )