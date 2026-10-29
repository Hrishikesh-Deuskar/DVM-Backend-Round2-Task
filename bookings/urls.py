from django.urls import path

from . import views


app_name = "bookings"

urlpatterns = [
    path(
        "purchase/<int:event_id>/",
        views.purchase,
        name="purchase",
    ),
    path(
        "<int:booking_id>/",
        views.booking_detail,
        name="detail",
    ),
    path(
        "history/",
        views.booking_history,
        name="history",
    ),
    path(
        "tickets/",
        views.active_tickets,
        name="active_tickets",
    ),
]