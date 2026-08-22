"""Create the minimal data set required for a usable development environment."""

from django.core.management.base import BaseCommand

from accounts.models import Privilege, PrivilegeCode, User
from forestry.models import OwnerStatus


DEFAULT_STATUSES = {
    "ASSIGNED": (60, "c5edc8", True),
    "WAITS_FOR_EVALUATION": (60, "cfeaed", True),
    "IN_PROGRESS": (60, "edc69b", True),
    "EVALUATED_NEEDS_ACTION": (60, "e6d9ed", True),
    "DEAL": (175, "95ed6b", True),
    "LARGE_OWNER": (36500, "ed7a6f", False),
    "NO_LAND": (730, "ed7a6f", False),
    "DEAD": (36500, "ed7a6f", False),
    "WRONG_NUMBER": (730, "ed7a6f", False),
    "UNREACHABLE": (175, "ed7a6f", False),
    "NOT_INTERESTED": (175, "ed7a6f", False),
    "DOES_NOT_WANT_TO_TALK": (730, "ed7a6f", False),
    "TOO_EXPENSIVE": (175, "ed7a6f", False),
    "BUYER": (36500, "ed7a6f", False),
    "OWNER_WONT_SELL": (175, "ed7a6f", False),
}


class Command(BaseCommand):
    help = "Create the development administrator and default owner statuses."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            id="autocreated",
            defaults={"full_name": "Create a new admin and delete me!", "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password("autocreated")
            user.save(update_fields=["password"])
            self.stdout.write(self.style.WARNING("Created development user autocreated/autocreated; replace it immediately."))
        Privilege.objects.get_or_create(user=user, code=PrivilegeCode.ADMIN)

        for status_id, (days, color, protected) in DEFAULT_STATUSES.items():
            OwnerStatus.objects.update_or_create(
                id=status_id,
                defaults={"days_out_of_search": days, "color_hex": color, "protected": protected},
            )
        self.stdout.write(self.style.SUCCESS("Default ForestIQ development data is ready."))
