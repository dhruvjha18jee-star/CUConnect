# core/auth.py
# Account registry (HashTable) and secure salted PBKDF2-SHA256 authentication.
# Course mapping: Session 15: Heaps and Hash Tables.

import hashlib
import hmac
import os
import re

from core.ds.hash_table import HashTable
from core.models import AuthError, User, UserNotFoundError, ValidationError

_USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")
_PBKDF2_ITERATIONS = 100_000
_SALT_BYTES = 16


def normalize_username(username: str) -> str:
    """Normalize a username to trimmed lowercase form.

    Time: O(L), where L = len(username)
    Space: O(L)
    """
    return username.strip().lower()


def validate_username(username: str) -> str:
    """Validate and return a normalized username (3-30 lowercase letters, digits, '_').

    Time: O(L), where L = len(username)
    Space: O(L)
    """
    cleaned = normalize_username(username)
    if not _USERNAME_PATTERN.match(cleaned):
        raise ValidationError(
            "Username must be 3-30 characters using only letters, numbers, or underscores."
        )
    return cleaned


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash a plain-text password using salted PBKDF2-HMAC-SHA256.

    Why salted PBKDF2 instead of plain SHA-256:
    - A unique 16-byte random salt ensures identical passwords produce different hashes,
      defeating rainbow tables.
    - 100,000 iterations deliberately slow down offline brute-force guessing.

    Time: O(iterations)
    Space: O(1)
    """
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    salt_bytes = salt if salt is not None else os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt_bytes.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a candidate password against a stored PBKDF2 hash in constant time.

    Uses `hmac.compare_digest` to prevent timing side-channel leaks.

    Time: O(iterations)
    Space: O(1)
    """
    parts = stored_hash.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    try:
        iterations = int(parts[1])
        salt_bytes = bytes.fromhex(parts[2])
        expected_hex = parts[3]
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        iterations,
    ).hex()
    return hmac.compare_digest(candidate, expected_hex)


def clean_skills(skills: list[str]) -> list[str]:
    """Trim whitespace, drop blanks, and deduplicate a list of skills preserving order.

    Time: O(S), where S = len(skills)
    Space: O(S)
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in skills:
        skill = raw.strip()
        lower = skill.lower()
        if skill and lower not in seen:
            seen.add(lower)
            cleaned.append(skill)
    return cleaned


class AccountManager:
    """Manages student accounts and active login sessions using our HashTable."""

    # Precomputed dummy hash so missing-username logins perform the same PBKDF2 work
    # and always return the same generic error message.
    _DUMMY_HASH = hash_password("dummy_password_for_timing_balance", salt=b"0" * _SALT_BYTES)

    def __init__(self) -> None:
        """Create an empty account registry and active-session table.

        Time: O(1)
        Space: O(1)
        """
        self._users: HashTable = HashTable(initial_capacity=32)
        self._active_sessions: HashTable = HashTable(initial_capacity=16)

    def register_user(
        self,
        username: str,
        password: str,
        full_name: str,
        programme: str,
        year: int,
        bio: str = "",
        skills: list[str] | None = None,
        created_at: float = 0.0,
    ) -> User:
        """Create and store a new User with a salted PBKDF2 password hash.

        Time: O(1) average HashTable insert + O(iterations) password hashing
        Space: O(1)
        """
        uname = validate_username(username)
        if self._users.contains(uname):
            raise ValidationError(f"Username '{uname}' is already taken.")

        name_clean = full_name.strip()
        prog_clean = programme.strip()
        if not name_clean:
            raise ValidationError("Full name cannot be empty.")
        if not prog_clean:
            raise ValidationError("Programme cannot be empty.")
        if isinstance(year, bool) or not isinstance(year, int) or year < 1 or year > 5:
            raise ValidationError("Year must be an integer between 1 and 5.")

        pw_hash = hash_password(password)
        user = User(
            username=uname,
            password_hash=pw_hash,
            full_name=name_clean,
            programme=prog_clean,
            year=year,
            bio=bio.strip(),
            skills=clean_skills(skills or []),
            created_at=created_at,
        )
        self._users.put(uname, user)
        return user

    def load_user(self, user: User) -> None:
        """Insert a pre-hashed User record during startup hydration from storage.

        Time: O(1) average
        Space: O(1)
        """
        self._users.put(user.username, user)

    def login(self, username: str, password: str) -> User:
        """Authenticate credentials and mark the user as logged in.

        Never reveals whether the username exists or the password was wrong.

        Time: O(1) average lookup + O(iterations) PBKDF2 verification
        Space: O(1)
        """
        uname = normalize_username(username)
        user: User | None = self._users.get(uname)
        if user is None:
            # Perform dummy verification so timing does not leak username existence.
            verify_password(password, self._DUMMY_HASH)
            raise AuthError("Invalid username or password.")

        if not verify_password(password, user.password_hash):
            raise AuthError("Invalid username or password.")

        self._active_sessions.put(uname, True)
        return user

    def logout(self, username: str) -> None:
        """End an active session for `username` (no-op if already logged out).

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(username)
        if self._active_sessions.contains(uname):
            self._active_sessions.remove(uname)

    def is_logged_in(self, username: str) -> bool:
        """Return True if `username` currently has an active session.

        Time: O(1) average
        Space: O(1)
        """
        return self._active_sessions.contains(normalize_username(username))

    def get_user(self, username: str) -> User:
        """Retrieve a User by username or raise UserNotFoundError.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(username)
        user: User | None = self._users.get(uname)
        if user is None:
            raise UserNotFoundError(f"User '{uname}' does not exist.")
        return user

    def user_exists(self, username: str) -> bool:
        """Return True if `username` is registered.

        Time: O(1) average
        Space: O(1)
        """
        return self._users.contains(normalize_username(username))

    def update_profile(
        self,
        username: str,
        full_name: str | None = None,
        programme: str | None = None,
        year: int | None = None,
        bio: str | None = None,
        skills: list[str] | None = None,
    ) -> User:
        """Update editable profile fields for an existing user and return the User.

        Time: O(1) average lookup + O(S) skill cleaning
        Space: O(S)
        """
        user = self.get_user(username)
        if full_name is not None:
            cleaned_name = full_name.strip()
            if not cleaned_name:
                raise ValidationError("Full name cannot be empty.")
            user.full_name = cleaned_name
        if programme is not None:
            cleaned_prog = programme.strip()
            if not cleaned_prog:
                raise ValidationError("Programme cannot be empty.")
            user.programme = cleaned_prog
        if year is not None:
            if isinstance(year, bool) or not isinstance(year, int) or year < 1 or year > 5:
                raise ValidationError("Year must be an integer between 1 and 5.")
            user.year = year
        if bio is not None:
            user.bio = bio.strip()
        if skills is not None:
            user.skills = clean_skills(skills)
        return user

    def all_users(self) -> list[User]:
        """Return a list of all registered User objects.

        Time: O(V + capacity)
        Space: O(V)
        """
        return self._users.values()

    def count(self) -> int:
        """Return the total number of registered users.

        Time: O(1)
        Space: O(1)
        """
        return len(self._users)

    def hash_table_load_factor(self) -> float:
        """Expose the underlying HashTable load factor for diagnostics and viva demos.

        Time: O(1)
        Space: O(1)
        """
        return self._users.load_factor()
