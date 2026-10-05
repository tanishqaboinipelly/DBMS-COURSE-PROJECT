"""Input validation helpers for the HIPCMS console application."""
import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value.strip()))


def is_valid_phone(value: str) -> bool:
    return bool(PHONE_RE.match(value.strip()))


def is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_positive_number(value: str) -> bool:
    try:
        return float(value) > 0
    except ValueError:
        return False


def is_non_empty(value: str) -> bool:
    return bool(value and value.strip())


def prompt(label, validator=None, error_msg="Invalid input, please try again.", allow_blank=False):
    """Prompt until a valid value is entered. Returns the trimmed string."""
    while True:
        value = input(label).strip()
        if allow_blank and value == "":
            return value
        if validator is None or validator(value):
            return value
        print(f"  ! {error_msg}")


def prompt_choice(label, choices):
    """Prompt until the value entered is one of `choices` (case-insensitive)."""
    choices_upper = [c.upper() for c in choices]
    while True:
        value = input(f"{label} {choices}: ").strip().upper()
        if value in choices_upper:
            return value
        print(f"  ! Please enter one of: {', '.join(choices)}")
