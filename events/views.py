from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .models import Event


@login_required
def event_list(request):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    events = (
        Event.objects.filter(is_active=True)
        .select_related("organization")
        .order_by("start_time")
    )

    return render(
        request,
        "events/event_list.html",
        {"events": events},
    )


@login_required
def event_detail(request, event_id):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    event = get_object_or_404(
        Event.objects.select_related("organization"),
        id=event_id,
        is_active=True,
    )

    slots = []

    if event.event_type == Event.EventType.SLOT:
        slots = event.slots.order_by("start_time")

    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "slots": slots,
        },
    )