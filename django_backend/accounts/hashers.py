"""Password hash compatibility for the legacy Java BCrypt format."""

import bcrypt
from django.contrib.auth.hashers import BasePasswordHasher, mask_hash


class LegacyBCryptPasswordHasher(BasePasswordHasher):
    """Verify hashes stored by the former Java service (for example ``$2a$10$...``)."""

    algorithm = "legacy_bcrypt"

    def salt(self) -> str:
        return ""

    def encode(self, password: str, salt: str) -> str:
        if password is None:
            raise TypeError("Password must not be None")
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, encoded: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), encoded.encode("utf-8"))
        except (TypeError, ValueError):
            return False

    def safe_summary(self, encoded: str) -> dict[str, str]:
        return {"algorithm": self.algorithm, "hash": mask_hash(encoded, show=6)}

    def must_update(self, encoded: str) -> bool:
        return True

    def harden_runtime(self, password: str, encoded: str) -> None:
        return None

    @classmethod
    def identify(cls, encoded: str) -> bool:
        return encoded.startswith(("$2a$", "$2b$", "$2y$"))
