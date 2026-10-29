from django.urls import path

from . import views


app_name = "organization"

urlpatterns = [
    path(
        "<int:organization_id>/",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "<int:organization_id>/events/",
        views.event_list,
        name="event_list",
    ),
    path(
        "<int:organization_id>/events/create/",
        views.event_create,
        name="event_create",
    ),
    path(
        "<int:organization_id>/events/<int:event_id>/",
        views.event_detail,
        name="event_detail",
    ),
    path(
        "<int:organization_id>/events/<int:event_id>/edit/",
        views.event_edit,
        name="event_edit",
    ),
    path(
        "<int:organization_id>/events/<int:event_id>/slots/create/",
        views.slot_create,
        name="slot_create",
    ),
    path(
        "<int:organization_id>/events/<int:event_id>/slots/<int:slot_id>/edit/",
        views.slot_edit,
        name="slot_edit",
    ),
    path(
        "<int:organization_id>/tickets/consume/",
        views.ticket_consume,
        name="ticket_consume",
    ),
    path(
        "<int:organization_id>/analytics/",
        views.analytics,
        name="analytics",
    ),
]