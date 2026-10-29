from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Organization, OrganizationMembership
from events.models import Event


User = get_user_model()


class OrganizationPermissionTests(TestCase):

    def setUp(self):
        self.manager = User.objects.create_user(
            username="test_manager",
            password="test-password-123",
        )

        self.staff = User.objects.create_user(
            username="test_staff",
            password="test-password-123",
        )

        self.outsider = User.objects.create_user(
            username="test_outsider",
            password="test-password-123",
        )

        group, _ = Group.objects.get_or_create(
            name="Organization"
        )

        for user in (self.manager, self.staff, self.outsider):
            user.groups.add(group)

        self.organization = Organization.objects.create(
            name="Test Sports Club"
        )

        self.other_organization = Organization.objects.create(
            name="Other Organization"
        )

        OrganizationMembership.objects.create(
            user=self.manager,
            organization=self.organization,
            role=OrganizationMembership.Role.MANAGER,
        )

        OrganizationMembership.objects.create(
            user=self.staff,
            organization=self.organization,
            role=OrganizationMembership.Role.STAFF,
        )

        self.event = Event.objects.create(
            organization=self.organization,
            title="Test Concert",
            description="Test description",
            event_type=Event.EventType.TICKET,
            price=Decimal("500.00"),
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=2),
            capacity=20,
        )

    def test_manager_can_access_dashboard(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse(
                "organization:dashboard",
                args=[self.organization.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_access_dashboard(self):
        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse(
                "organization:dashboard",
                args=[self.organization.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_create_event(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse(
                "organization:event_create",
                args=[self.organization.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_can_access_event_creation(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse(
                "organization:event_create",
                args=[self.organization.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_manager_cannot_access_other_organization(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse(
                "organization:analytics",
                args=[self.other_organization.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_can_view_own_event(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse(
                "organization:event_detail",
                args=[
                    self.organization.pk,
                    self.event.pk,
                ],
            )
        )

        self.assertEqual(response.status_code, 200)