from django import forms

from events.models import Event, EventSlot


class EventForm(forms.ModelForm):

    class Meta:
        model = Event

        fields = [
            "title",
            "description",
            "event_type",
            "price",
            "start_time",
            "end_time",
            "capacity",
            "is_active",
        ]

        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

        self.fields["start_time"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]
        self.fields["end_time"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]

    def clean(self):
        cleaned = super().clean()

        event_type = cleaned.get("event_type")
        capacity = cleaned.get("capacity")

        if event_type == Event.EventType.SLOT:
            if capacity != 0:
                self.add_error(
                    "capacity",
                    "Slot-based events must use event capacity 0. "
                    "Set capacity on individual slots.",
                )

        if self.instance.pk:
            if event_type != self.instance.event_type:
                self.add_error(
                    "event_type",
                    "Changing an existing event's type is not supported.",
                )

        return cleaned

class EventSlotForm(forms.ModelForm):

    class Meta:
        model = EventSlot

        fields = [
            "start_time",
            "end_time",
            "capacity",
        ]

        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "capacity": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in ("start_time", "end_time"):
            self.fields[field].input_formats = [
                "%Y-%m-%dT%H:%M"
            ]

import uuid


class TicketConsumeForm(forms.Form):

    ticket_id = forms.UUIDField(
        label="Ticket UUID",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter ticket UUID",
            }
        ),
    )