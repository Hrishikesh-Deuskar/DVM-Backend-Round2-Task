from decimal import Decimal

from django import forms


class WalletTopUpForm(forms.Form):

    amount = forms.DecimalField(
        label="Amount (₹)",
        min_value=Decimal("0.01"),
        max_value=Decimal("10000.00"),
        max_digits=7,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter amount",
                "step": "0.01",
                "min": "0.01",
                "max": "10000.00",
            }
        ),
    )