# tests/test_auth.py
# Unit tests for core.auth (PBKDF2 hashing, constant-time verify, AccountManager).

import unittest

from core.auth import AccountManager, hash_password, verify_password
from core.models import AuthError, UserNotFoundError, ValidationError


class TestAuth(unittest.TestCase):
    def test_password_hashing_salted_and_never_plaintext(self) -> None:
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        self.assertNotIn("secret123", h1)
        self.assertNotEqual(h1, h2)  # Different random salts
        self.assertTrue(verify_password("secret123", h1))
        self.assertTrue(verify_password("secret123", h2))
        self.assertFalse(verify_password("wrongpass", h1))

    def test_register_login_logout_and_uniform_error(self) -> None:
        am = AccountManager()
        user = am.register_user(
            username="Aarav_01",
            password="password123",
            full_name="Aarav Sharma",
            programme="B.Tech CSAI",
            year=2,
            bio="ML enthusiast",
            skills=["Python", "  python ", "DSA"],
            created_at=100.0,
        )
        self.assertEqual(user.username, "aarav_01")
        self.assertEqual(user.skills, ["Python", "DSA"])
        self.assertNotIn("password_hash", user.public_profile())

        # Duplicate username fails
        with self.assertRaises(ValidationError):
            am.register_user("aarav_01", "otherpass", "Other", "CSE", 1)

        # Login with wrong password vs unknown user produce identical error text.
        with self.assertRaises(AuthError) as wrong_pw:
            am.login("aarav_01", "wrongpass")
        with self.assertRaises(AuthError) as missing_user:
            am.login("ghost_user", "wrongpass")
        self.assertEqual(str(wrong_pw.exception), str(missing_user.exception))

        logged = am.login("AARAV_01", "password123")
        self.assertEqual(logged.username, "aarav_01")
        self.assertTrue(am.is_logged_in("aarav_01"))

        am.logout("aarav_01")
        self.assertFalse(am.is_logged_in("aarav_01"))

    def test_profile_update_and_unknown_user(self) -> None:
        am = AccountManager()
        am.register_user("diya", "pass1234", "Diya Nair", "B.Tech EVE", 2)
        updated = am.update_profile("diya", bio="VLSI & Python", skills=["Verilog", "Python"])
        self.assertEqual(updated.bio, "VLSI & Python")
        self.assertEqual(updated.skills, ["Verilog", "Python"])

        with self.assertRaises(UserNotFoundError):
            am.get_user("nobody")

        # Boolean year must be rejected even though bool subclasses int in Python.
        with self.assertRaises(ValidationError):
            am.register_user("bad_yr", "pass1234", "Bad Year", "CSAI", True)  # type: ignore[arg-type]
        with self.assertRaises(ValidationError):
            am.update_profile("diya", year=True)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
