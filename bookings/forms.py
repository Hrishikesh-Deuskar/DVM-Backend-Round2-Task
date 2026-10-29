from django import forms


class TicketPurchaseForm(forms.Form):

    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "max": 10,
            }
        ),
    )


class SlotBookingForm(forms.Form):

    slot_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )