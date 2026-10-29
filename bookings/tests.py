from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Organization
from events.models import Event
from wallet.models import Wallet, WalletTransaction

from .models import Booking, Ticket
from .services import purchase_event

from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse


User = get_user_model()


class PurchaseServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer",
            password="test-password-123",
        )

        self.organization = Organization.objects.create(
            name="Test Organization",
        )

        self.event = Event.objects.create(
            organization=self.organization,
            title="Test Concert",
            description="Test event",
            event_type=Event.EventType.TICKET,
            price=Decimal("500.00"),
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=3),
            capacity=5,
        )

        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal("1500.00"),
        )

    def test_successful_purchase(self):
        booking = purchase_event(
            self.user,
            self.event.pk,
            quantity=2,
        )

        self.wallet.refresh_from_db()
        self.event.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            Decimal("500.00"),
        )

        self.assertEqual(self.event.booked_count, 2)
        self.assertEqual(booking.tickets.count(), 2)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(
            WalletTransaction.objects.filter(
                transaction_type="purchase"
            ).count(),
            1,
        )

    def test_insufficient_balance(self):
        with self.assertRaises(ValidationError):
            purchase_event(
                self.user,
                self.event.pk,
                quantity=4,
            )

        self.wallet.refresh_from_db()
        self.event.refresh_from_db()

        self.assertEqual(
            self.wallet.balance,
            Decimal("1500.00"),
        )

        self.assertEqual(self.event.booked_count, 0)
        self.assertEqual(Booking.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_capacity_limit(self):
        self.event.capacity = 1
        self.event.save(update_fields=["capacity"])

        with self.assertRaises(ValidationError):
            purchase_event(
                self.user,
                self.event.pk,
                quantity=2,
            )

        self.assertEqual(Booking.objects.count(), 0)

class BookingPageTests(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer_one",
            password="test-password-123",
        )

        self.other_customer = User.objects.create_user(
            username="customer_two",
            password="test-password-123",
        )

        self.manager = User.objects.create_user(
            username="organization_manager",
            password="test-password-123",
        )

        customer_group, _ = Group.objects.get_or_create(
            name="Customer"
        )

        organization_group, _ = Group.objects.get_or_create(
            name="Organization"
        )

        self.customer.groups.add(customer_group)
        self.other_customer.groups.add(customer_group)
        self.manager.groups.add(organization_group)

        organization = Organization.objects.create(
            name="Test Sports Club",
        )

        self.event = Event.objects.create(
            organization=organization,
            title="Test Music Concert",
            description="Test event",
            event_type=Event.EventType.TICKET,
            price=Decimal("500.00"),
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=3),
            capacity=10,
        )

        Wallet.objects.create(
            user=self.customer,
            balance=Decimal("2000.00"),
        )

        Wallet.objects.create(
            user=self.other_customer,
            balance=Decimal("2000.00"),
        )

        self.booking = purchase_event(
            self.customer,
            self.event.pk,
            quantity=2,
        )

        self.other_booking = purchase_event(
            self.other_customer,
            self.event.pk,
            quantity=1,
        )

        self.client = Client()

    def test_customer_can_view_booking_history(self):
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("bookings:history")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            f"Booking #{self.booking.pk}",
        )

        self.assertNotContains(
            response,
            f"Booking #{self.other_booking.pk}",
        )

    def test_customer_can_view_active_tickets(self):
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("bookings:active_tickets")
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.context["tickets"]),
            2,
        )

    def test_customer_cannot_view_another_booking(self):
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse(
                "bookings:detail",
                args=[self.other_booking.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_organization_cannot_view_customer_history(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("bookings:history")
        )

        self.assertEqual(response.status_code, 403)

    def test_organization_cannot_view_customer_tickets(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("bookings:active_tickets")
        )

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(
            reverse("bookings:history")
        )

        self.assertEqual(response.status_code, 302)

        self.assertIn(
            "/accounts/login/",
            response.url,
        )

    def test_consumed_ticket_not_shown_as_active(self):
        ticket = self.booking.tickets.first()

        ticket.status = Ticket.TicketStatus.CONSUMED
        ticket.consumed_at = timezone.now()

        ticket.save(
            update_fields=["status", "consumed_at"]
        )

        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("bookings:active_tickets")
        )

        self.assertEqual(
            len(response.context["tickets"]),
            1,
        )

    def test_cancelled_booking_tickets_not_active(self):
        self.booking.status = Booking.BookingStatus.CANCELLED
        self.booking.save(update_fields=["status"])

        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("bookings:active_tickets")
        )

        self.assertEqual(
            len(response.context["tickets"]),
            0,
        )