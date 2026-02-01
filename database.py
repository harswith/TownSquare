"""
Database layer for the Town Square application.

All direct interaction with SQLite is contained in this module so the
rest of the code can work with clear, high‑level functions.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from models import Business, Review, ReportSummary


DB_FILE = Path(__file__).with_name("town_square.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row access by name."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create tables if they do not already exist and insert starter data."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                deal_text TEXT NOT NULL,
                average_rating REAL NOT NULL DEFAULT 0.0,
                review_count INTEGER NOT NULL DEFAULT 0,
                is_favorite INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (business_id) REFERENCES businesses (id)
                    ON DELETE CASCADE
            )
            """
        )

        # If there are no businesses yet, insert a small starter set so
        # the directory feels alive on first launch.
        cur = conn.execute("SELECT COUNT(*) AS count FROM businesses")
        if cur.fetchone()["count"] == 0:
            starter_businesses = [
                ("Sunrise Café", "Food", "Buy 1 breakfast, get 2nd 50% off"),
                ("Corner Book Nook", "Retail", "10% off local authors"),
                ("Sparkle Cleaners", "Services", "First shirt pressed for free"),
                ("Green Leaf Market", "Food", "Free fruit sample with purchase"),
                ("TechFix Repair", "Services", "Free diagnostics for laptops"),
                ("Tiny Treasures Gifts", "Retail", "Free gift wrapping this week"),
            ]
            conn.executemany(
                """
                INSERT INTO businesses (name, category, deal_text)
                VALUES (?, ?, ?)
                """,
                starter_businesses,
            )


def _row_to_business(row: sqlite3.Row) -> Business:
    return Business(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        average_rating=float(row["average_rating"]),
        review_count=int(row["review_count"]),
        deal_text=row["deal_text"],
        is_favorite=bool(row["is_favorite"]),
    )


def add_business(name: str, category: str, deal_text: str) -> Business:
    """
    Insert a new business into the directory and return the created record.

    The UI is responsible for validating the inputs and restricting the
    category to the allowed values (Food, Retail, Services).
    """
    with closing(get_connection()) as conn, conn:
        cur = conn.execute(
            """
            INSERT INTO businesses (name, category, deal_text)
            VALUES (?, ?, ?)
            """,
            (name.strip(), category.strip(), deal_text.strip()),
        )
        new_id = cur.lastrowid

        cur = conn.execute("SELECT * FROM businesses WHERE id = ?", (new_id,))
        row = cur.fetchone()

    return _row_to_business(row)


def get_businesses(
    category_filter: Optional[str] = None,
    sort_by_rating_desc: bool = False,
    favorites_only: bool = False,
) -> List[Business]:
    """Return a list of businesses matching the provided filters."""
    query = "SELECT * FROM businesses"
    clauses = []
    params: list = []

    if category_filter and category_filter != "All":
        clauses.append("category = ?")
        params.append(category_filter)

    if favorites_only:
        clauses.append("is_favorite = 1")

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    if sort_by_rating_desc:
        query += " ORDER BY average_rating DESC, review_count DESC, name ASC"
    else:
        query += " ORDER BY name ASC"

    with closing(get_connection()) as conn:
        cur = conn.execute(query, params)
        return [_row_to_business(row) for row in cur.fetchall()]


def toggle_favorite(business_id: int, make_favorite: bool) -> None:
    """Set or clear the favorite flag for a business."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            "UPDATE businesses SET is_favorite = ? WHERE id = ?",
            (1 if make_favorite else 0, business_id),
        )


def add_review(business_id: int, rating: int, text: str, created_at: str) -> None:
    """
    Store a new review and update the business's average rating.

    The UI is responsible for validating rating range and text length.
    """
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            INSERT INTO reviews (business_id, rating, text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (business_id, rating, text, created_at),
        )

        # Recalculate average rating for the business.
        cur = conn.execute(
            """
            SELECT AVG(rating) AS avg_rating, COUNT(*) AS review_count
            FROM reviews
            WHERE business_id = ?
            """,
            (business_id,),
        )
        row = cur.fetchone()
        avg_rating = float(row["avg_rating"] or 0.0)
        count = int(row["review_count"] or 0)

        conn.execute(
            """
            UPDATE businesses
            SET average_rating = ?, review_count = ?
            WHERE id = ?
            """,
            (avg_rating, count, business_id),
        )


def get_reports_summary() -> ReportSummary:
    """Compute aggregate values used by the Reports screen."""
    with closing(get_connection()) as conn:
        cur = conn.execute("SELECT COUNT(*) AS count FROM businesses")
        total_businesses = int(cur.fetchone()["count"])

        cur = conn.execute(
            """
            SELECT AVG(average_rating) AS avg_rating
            FROM businesses
            WHERE review_count > 0
            """
        )
        row = cur.fetchone()
        average_rating = float(row["avg_rating"] or 0.0)

        cur = conn.execute(
            """
            SELECT * FROM businesses
            WHERE review_count > 0
            ORDER BY average_rating DESC, review_count DESC, name ASC
            LIMIT 3
            """
        )
        top_businesses = [_row_to_business(r) for r in cur.fetchall()]

        cur = conn.execute(
            "SELECT COUNT(*) AS count FROM businesses WHERE is_favorite = 1"
        )
        favorite_count = int(cur.fetchone()["count"])

        return ReportSummary(
            total_businesses=total_businesses,
            average_rating=average_rating,
            top_businesses=top_businesses,
            favorite_count=favorite_count,
        )


def get_recommended_businesses(preferred_category: Optional[str]) -> List[Business]:
    """
    Recommend businesses based on favorites, preferred category, and ratings.

    Simple, explainable strategy:
    1. Show favorited businesses in the preferred category first.
    2. Then show high‑rated businesses in that category.
    3. Finally, fall back to overall high‑rated favorites or all businesses.
    """
    with closing(get_connection()) as conn:
        params: list = []
        where_clauses = []
        order_clause = " ORDER BY is_favorite DESC, average_rating DESC, review_count DESC, name ASC"

        if preferred_category and preferred_category != "All":
            where_clauses.append("category = ?")
            params.append(preferred_category)

        base_query = "SELECT * FROM businesses"
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        cur = conn.execute(base_query + order_clause, params)
        results = [_row_to_business(r) for r in cur.fetchall()]

        # If there are no results for the requested category,
        # fall back to all businesses ranked by favorites and rating.
        if not results:
            cur = conn.execute(
                "SELECT * FROM businesses" + order_clause,
            )
            results = [_row_to_business(r) for r in cur.fetchall()]

    return results

