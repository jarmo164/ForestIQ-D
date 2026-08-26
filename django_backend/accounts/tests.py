from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from accounts.models import (
    DEFAULT_ORGANIZATION_ID,
    DEFAULT_ORGANIZATION_SLUG,
    Organization,
    OrganizationMembership,
    OrganizationRole,
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


class KeycloakClaimMappingTests(TestCase):
    @override_settings(
        KEYCLOAK_OIDC_ENABLED=True,
        KEYCLOAK_ISSUER="https://sso.example.test/realms/forestiq",
        KEYCLOAK_CLIENT_ID="forestiq-web",
        KEYCLOAK_ORGANIZATION_CLAIM="organization_id",
    )
    @patch("accounts.oidc._verified_claims")
    @patch("accounts.oidc.requests.post")
    @patch("accounts.oidc.discovery_document")
    def test_keycloak_roles_create_an_oidc_managed_membership(self, mocked_discovery, mocked_post, mocked_claims):
        from accounts.oidc import exchange_authorization_code

        organization = Organization.objects.create(slug="keycloak-org", name="Keycloak organization")
        mocked_discovery.return_value = {
            "authorization_endpoint": "https://sso.example.test/auth",
            "token_endpoint": "https://sso.example.test/token",
            "jwks_uri": "https://sso.example.test/jwks",
            "issuer": "https://sso.example.test/realms/forestiq",
        }
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"id_token": "signed-provider-token"}
        mocked_post.return_value = response
        mocked_claims.return_value = {
            "sub": "keycloak-subject-123",
            "name": "Keycloak User",
            "organization_id": str(organization.id),
            "realm_access": {"roles": ["ORG_MEMBER", "CRM_MANAGER", "EVALUATOR"]},
        }

        user, membership = exchange_authorization_code(
            code="authorization-code",
            code_verifier="pkce-verifier",
            redirect_uri="https://app.example/login",
            nonce="browser-nonce",
        )

        self.assertEqual(user.id, "keycloak-subject-123")
        self.assertEqual(membership.organization, organization)
        self.assertTrue(membership.oidc_managed)
        self.assertEqual(
            membership.role_codes,
            [OrganizationRole.MEMBER, OrganizationRole.CRM_MANAGER, OrganizationRole.EVALUATOR],
        )
        self.assertTrue(membership.has_privilege(PrivilegeCode.OWNER_PROFILE))
        self.assertTrue(membership.has_privilege(PrivilegeCode.EVALUATION))
        self.assertFalse(membership.has_privilege(PrivilegeCode.ADMIN))

    @override_settings(
        KEYCLOAK_OIDC_ENABLED=True,
        KEYCLOAK_ISSUER="https://sso.example.test/realms/forestiq",
        KEYCLOAK_CLIENT_ID="forestiq-web",
        KEYCLOAK_ORGANIZATION_CLAIM="organization_id",
    )
    @patch("accounts.oidc._verified_claims")
    @patch("accounts.oidc.requests.post")
    @patch("accounts.oidc.discovery_document")
    def test_keycloak_rejects_unknown_roles_before_creating_membership(self, mocked_discovery, mocked_post, mocked_claims):
        from accounts.oidc import OIDCAuthenticationError, exchange_authorization_code

        organization = Organization.objects.create(slug="keycloak-denied-org", name="Keycloak denied organization")
        mocked_discovery.return_value = {
            "authorization_endpoint": "https://sso.example.test/auth",
            "token_endpoint": "https://sso.example.test/token",
            "jwks_uri": "https://sso.example.test/jwks",
            "issuer": "https://sso.example.test/realms/forestiq",
        }
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"id_token": "signed-provider-token"}
        mocked_post.return_value = response
        mocked_claims.return_value = {
            "sub": "keycloak-denied-subject",
            "organization_id": str(organization.id),
            "realm_access": {"roles": ["UNRELATED_ROLE"]},
        }

        with self.assertRaises(OIDCAuthenticationError):
            exchange_authorization_code(
                code="authorization-code",
                code_verifier="pkce-verifier",
                redirect_uri="https://app.example/login",
            )

        self.assertFalse(User.objects.filter(id="keycloak-denied-subject").exists())
