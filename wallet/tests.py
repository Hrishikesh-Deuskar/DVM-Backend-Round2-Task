from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Wallet, WalletTransaction
from .services import add_wallet_money


User = get_user_model()


class WalletServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="wallet_test_user",
            password="test-password-123",
        )

    def test_successful_topup(self):
        add_wallet_money(self.user, Decimal("500.00"))

        wallet = Wallet.objects.get(user=self.user)

        self.assertEqual(
            wallet.balance,
            Decimal("500.00"),
        )

        self.assertEqual(
            wallet.transactions.count(),
            1,
        )

    def test_multiple_topups(self):
        add_wallet_money(self.user, Decimal("500.00"))
        add_wallet_money(self.user, Decimal("250.00"))

        wallet = Wallet.objects.get(user=self.user)

        self.assertEqual(
            wallet.balance,
            Decimal("750.00"),
        )

        self.assertEqual(
            wallet.transactions.count(),
            2,
        )

    def test_negative_topup_rejected(self):
        with self.assertRaises(ValidationError):
            add_wallet_money(self.user, Decimal("-100.00"))

        self.assertFalse(
            WalletTransaction.objects.exists()
        )

    def test_zero_topup_rejected(self):
        with self.assertRaises(ValidationError):
            add_wallet_money(self.user, Decimal("0.00"))

        self.assertFalse(
            WalletTransaction.objects.exists()
        )

    def test_excessive_topup_rejected(self):
        with self.assertRaises(ValidationError):
            add_wallet_money(self.user, Decimal("10000.01"))

        self.assertFalse(
            WalletTransaction.objects.exists()
        )