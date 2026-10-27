from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

class Event(models.Model):

    class EventType(models.TextChoices):
        TICKET = "ticket", "Ticket-based"
        SLOT = "slot", "Slot-based"

    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="events",
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    event_type = models.CharField(
        max_length=10, 
        choices=EventType.choices,
    )

    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    capacity = models.PositiveIntegerField(default=0)
    booked_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="event_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(booked_count__lte=F("capacity")),
                name="event_booked_within_capacity",
            ),
        ]

    def clean(self):
        super().clean()

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    "Event end time must be after the start time"
                )

    def __str__(self):
        return self.title

class EventSlot(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="slots",
        limit_choices_to={"event_type": Event.EventType.SLOT},
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    capacity = models.PositiveIntegerField(default=1)
    booked_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(capacity__gte=1),
                name="slot_capacity_positive",
            ),
            models.CheckConstraint(
                condition=Q(booked_count__lte=F("capacity")),
                name="slot_booked_within_capacity",
            ),
            models.UniqueConstraint(
                fields=["event", "start_time", "end_time"],
                name="unique_event_slot",
            ),
        ]
        ordering = ["start_time"]

    def clean(self):
        super().clean()

        if self.event_id:
            if self.event.event_type != Event.EventType.SLOT:
                raise ValidationError(
                    "Slots can only belong to Slot-based events"
                )

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    "Slot end time must be after the start time"
                )
            if self.event_id:
                if (
                    self.start_time < self.event.start_time
                    or self.end_time > self.event.end_time
                ):
                    raise ValidationError(
                        "Slot times must be within the event's start and end times"
                    )

    def __str__(self):
        return f"{self.event.title}: {self.start_time} - {self.end_time}"