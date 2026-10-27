from django.contrib import admin

from .models import Booking, Ticket


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = (
        "id",
        "status",
        "created_at",
        "consumed_at",
    )

    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "quantity",
        "total_price",
        "status",
        "created_at",
    )

    list_filter = ("status", "event", "created_at")
    search_fields = ("user__username", "event__title")
    readonly_fields = (
        "user",
        "event",
        "slot",
        "quantity",
        "unit_price",
        "total_price",
        "status",
        "created_at",
    )

    inlines = [TicketInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "status",
        "created_at",
        "consumed_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("id", "booking__user__username")
    readonly_fields = (
        "id",
        "booking",
        "status",
        "created_at",
        "consumed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False