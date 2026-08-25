from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.models import Privilege, PrivilegeCode, User


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
