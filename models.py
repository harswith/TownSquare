"""
Data models used by the Town Square application.

These models are simple containers for information
read from and written to the SQLite database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Business:
    """Represents a local business shown in the directory."""

    id: int
    name: str
    category: str  # e.g. "Food", "Retail", "Services"
    average_rating: float
    review_count: int
    deal_text: str
    is_favorite: bool


@dataclass
class Review:
    """Represents a single user review for a business."""

    id: int
    business_id: int
    rating: int
    text: str
    created_at: str  # ISO string stored in the database


@dataclass
class ReportSummary:
    """Aggregated information for the Reports screen."""

    total_businesses: int
    average_rating: float
    top_businesses: list[Business]
    favorite_count: int

