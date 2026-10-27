from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wallet",
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(balance__gte=0),
                name="wallet_balance_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.user.username}'s wallet"

class WalletTransaction(models.Model):

    class TransactionType(models.TextChoices):
        CREDIT = "credit", "Money Added"
        PURCHASE = "purchase", "Ticket Purchase"
        REFUND = "refund", "Refund"

    wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="wallet_transaction_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(balance_after__gte=0),
                name="wallet_transaction_balance_nonnegative",
            ),
        ]

    def __str__(self):
        return(
            f"{self.wallet.user.username}: "
            f"{self.transaction_type} ₹{self.amount}"
        )
    