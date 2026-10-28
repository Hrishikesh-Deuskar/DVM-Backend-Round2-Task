from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.shortcuts import redirect, render

from .forms import WalletTopUpForm
from .models import Wallet
from .services import add_wallet_money


@login_required
def wallet_dashboard(request):

    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    wallet, _ = Wallet.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        form = WalletTopUpForm(request.POST)

        if form.is_valid():
            amount = form.cleaned_data["amount"]

            try:
                add_wallet_money(request.user, amount)
            except DatabaseError:
                messages.error(
                    request,
                    "Top-up failed. Please try again.",
                )
            else:
                messages.success(
                    request,
                    f"₹{amount} added to your wallet.",
                )

                return redirect("wallet:dashboard")

    else:
        form = WalletTopUpForm()

    wallet.refresh_from_db()

    transactions = wallet.transactions.all()

    return render(
        request,
        "wallet/dashboard.html",
        {
            "wallet": wallet,
            "transactions": transactions,
            "form": form,
        },
    )