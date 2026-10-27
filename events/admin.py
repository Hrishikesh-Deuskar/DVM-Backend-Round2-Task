from django.contrib import admin

from .models import Event, EventSlot


class EventSlotInline(admin.TabularInline):
    model = EventSlot
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "event_type",
        "price",
        "capacity",
        "booked_count",
        "is_active",
    )

    list_filter = ("event_type", "is_active", "organization")
    search_fields = ("title", "organization__name")
    inlines = [EventSlotInline]


@admin.register(EventSlot)
class EventSlotAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "start_time",
        "end_time",
        "capacity",
        "booked_count",
    )

    list_filter = ("event",)