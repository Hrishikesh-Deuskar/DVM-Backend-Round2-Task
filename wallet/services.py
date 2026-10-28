from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Wallet, WalletTransaction


MAX_TOPUP = Decimal("10000.00")


@transaction.atomic
def add_wallet_money(user, amount):

    if isinstance(amount, bool) or not isinstance(amount, Decimal):
        raise ValidationError("Amount must be a Decimal.")

    if not amount.is_finite():
        raise ValidationError("Amount must be finite.")

    if amount.as_tuple().exponent != -2:
        raise ValidationError("Amount must have exactly two decimal places.")

    if amount <= Decimal("0.00"):
        raise ValidationError("Amount must be greater than zero.")

    if amount > MAX_TOPUP:
        raise ValidationError("Maximum top-up is ₹10,000.")

    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={"balance": Decimal("0.00")},
    )

    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    wallet.balance += amount

    wallet.save(update_fields=["balance"])

    wallet_transaction = WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TransactionType.CREDIT,
        amount=amount,
        balance_after=wallet.balance,
        description="Wallet top-up",
    )

    return wallet_transaction