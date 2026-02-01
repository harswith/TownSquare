"""
Utility helpers for the Town Square application.

This module contains non‑UI helper functions such as
input validation and simple human‑verification logic.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


MIN_REVIEW_LENGTH = 10
MAX_REVIEW_LENGTH = 500

# Simple bounds for business fields so user input stays reasonable.
MIN_BUSINESS_NAME_LENGTH = 3
MAX_BUSINESS_NAME_LENGTH = 80
MIN_DEAL_LENGTH = 5
MAX_DEAL_LENGTH = 200


def get_current_timestamp() -> str:
    """Return the current time as an ISO‑8601 string."""
    return datetime.now().isoformat(timespec="seconds")


def validate_rating(value: str) -> Tuple[bool, str]:
    """
    Validate a rating entered in the UI.

    Returns (is_valid, message). On success, message is an empty string.
    """
    value = value.strip()
    if not value:
        return False, "Please enter a rating from 1 to 5."

    if not value.isdigit():
        return False, "Rating must be a whole number between 1 and 5."

    rating = int(value)
    if rating < 1 or rating > 5:
        return False, "Rating must be between 1 (lowest) and 5 (highest)."

    return True, ""


def validate_review_text(text: str) -> Tuple[bool, str]:
    """
    Validate review text length and content.

    Returns (is_valid, message). On success, message is an empty string.
    """
    stripped = text.strip()
    if len(stripped) < MIN_REVIEW_LENGTH:
        return (
            False,
            f"Review is too short. Please use at least {MIN_REVIEW_LENGTH} characters.",
        )
    if len(stripped) > MAX_REVIEW_LENGTH:
        return (
            False,
            f"Review is quite long. Please stay under {MAX_REVIEW_LENGTH} characters.",
        )
    return True, ""


def validate_business_name(text: str) -> Tuple[bool, str]:
    """
    Validate the name of a new business.

    Names must be present and reasonably short so they display cleanly.
    """
    stripped = text.strip()
    if len(stripped) < MIN_BUSINESS_NAME_LENGTH:
        return (
            False,
            "Business name is too short. Please use a descriptive name.",
        )
    if len(stripped) > MAX_BUSINESS_NAME_LENGTH:
        return (
            False,
            f"Business name is quite long. Please stay under {MAX_BUSINESS_NAME_LENGTH} characters.",
        )
    return True, ""


def validate_deal_text(text: str) -> Tuple[bool, str]:
    """
    Validate the special deal or coupon text for a business.
    """
    stripped = text.strip()
    if len(stripped) < MIN_DEAL_LENGTH:
        return (
            False,
            "Please describe the special deal or coupon (a few words are enough).",
        )
    if len(stripped) > MAX_DEAL_LENGTH:
        return (
            False,
            f"Deal text is quite long. Please stay under {MAX_DEAL_LENGTH} characters.",
        )
    return True, ""


@dataclass
class VerificationChallenge:
    """Represents a simple human‑verification math challenge."""

    prompt: str
    answer: int


def generate_verification_challenge() -> VerificationChallenge:
    """
    Create a small math problem that is easy for humans
    but inconvenient for automated bots.
    """
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    operation = random.choice(["+", "-"])

    if operation == "+":
        prompt = f"What is {a} + {b}?"
        answer = a + b
    else:
        # Ensure we do not go negative to keep answers simple.
        bigger, smaller = max(a, b), min(a, b)
        prompt = f"What is {bigger} - {smaller}?"
        answer = bigger - smaller

    return VerificationChallenge(prompt=prompt, answer=answer)


def check_verification_answer(challenge: VerificationChallenge, user_input: str) -> bool:
    """
    Check whether the user solved the verification challenge correctly.
    """
    user_input = user_input.strip()
    if not user_input.isdigit():
        return False
    return int(user_input) == challenge.answer

