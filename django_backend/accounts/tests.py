from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import (
    DEFAULT_ORGANIZATION_ID,
    DEFAULT_ORGANIZATION_SLUG,
    Organization,
    OrganizationMembership,
    Privilege,
    PrivilegeCode,
    User,
)
from forestry.models import Cadastre, Owner, OwnerCadastre, OwnerLog
from operations.models import Contract, Deal, DealOffer, InheritanceCase, InheritanceCaseEvent, InheritanceHeir


class DjangoGroupCompatibilityTests(TestCase):
    def test_legacy_privilege_creates_the_equivalent_django_group(self):
        user = User.objects.create_user("group-user", "Group user", "strong-password")
        Privilege.objects.create(user=user, code=PrivilegeCode.EVALUATION)
        self.assertTrue(user.groups.filter(name="ForestIQ Evaluators").exists())

    def test_removing_privilege_removes_managed_group(self):
        user = User.objects.create_user("group-user-2", "Group user", "strong-password")
        privilege = Privilege.objects.create(user=user, code=PrivilegeCode.PHONES)
        privilege.delete()
        self.assertFalse(user.groups.filter(name="ForestIQ Phone Directory").exists())
        self.assertTrue(Group.objects.filter(name="ForestIQ Phone Directory").exists())


class OrganizationOwnershipTests(TestCase):
    def setUp(self):
        self.legacy = Organization.objects.get(id=DEFAULT_ORGANIZATION_ID, slug=DEFAULT_ORGANIZATION_SLUG)
        self.organization = Organization.objects.create(slug="north-forest", name="North Forest OÜ")
        self.other_organization = Organization.objects.create(slug="south-forest", name="South Forest OÜ")
        self.user = User.objects.create_user("org-user", "Organization user", "strong-password", default_organization=self.organization)
        self.owner = Owner.objects.create(id="owner-org-1", name="Organization owner", organization=self.organization)
        self.cadastre = Cadastre.objects.create(id="79501:001:1001", organization=self.organization)
        self.other_cadastre = Cadastre.objects.create(id="79501:001:1002", organization=self.other_organization)

    def test_user_membership_is_created_for_default_organization(self):
        self.assertTrue(
            OrganizationMembership.objects.filter(organization=self.organization, user=self.user).exists()
        )

    def test_children_inherit_their_aggregate_organization(self):
        relationship = OwnerCadastre.objects.create(owner=self.owner, cadastre=self.cadastre, organization=self.legacy)
        log = OwnerLog.objects.create(owner=self.owner, creator=self.user, message="Organization-bound activity", organization=self.legacy)
        deal = Deal.objects.create(owner=self.owner, sale_subject="FOREST", organization=self.legacy)
        offer = DealOffer.objects.create(deal=deal, revision=1, kind=DealOffer.Kind.OFFER, amount="1000.00", organization=self.legacy)
        contract = Contract.objects.create(id="organization-contract", source_deal=deal, source_offer=offer, organization=self.legacy)
        inheritance_case = InheritanceCase.objects.create(owner=self.owner, organization=self.legacy)
        heir = InheritanceHeir.objects.create(inheritance_case=inheritance_case, display_name="Test heir", organization=self.legacy)
        event = InheritanceCaseEvent.objects.create(inheritance_case=inheritance_case, type="CREATED", description="Organization-bound event", organization=self.legacy)

        for record in (relationship, log, deal, offer, contract, inheritance_case, heir, event):
            self.assertEqual(record.organization_id, self.organization.id)

    def test_cross_organization_owner_cadastre_link_is_rejected(self):
        with self.assertRaises(ValidationError):
            OwnerCadastre.objects.create(owner=self.owner, cadastre=self.other_cadastre)
        with self.assertRaises(ValidationError):
            self.owner.cadastres.add(self.other_cadastre)

    def test_inheritance_notice_uniqueness_is_organization_scoped_without_blocking_manual_cases(self):
        InheritanceCase.objects.create(owner=self.owner)
        InheritanceCase.objects.create(owner=self.owner)
        InheritanceCase.objects.create(owner=self.owner, source_notice_number="NOTICE-1")
        with self.assertRaises(IntegrityError):
            InheritanceCase.objects.create(owner=self.owner, source_notice_number="NOTICE-1")
