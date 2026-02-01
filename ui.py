"""
Tkinter user interface for the Town Square application.

The design aims to be:
- visually clean and high‑contrast
- easy to navigate with a sidebar
- clear and friendly for FBLA judges and users
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

import database
from database import (
    add_business,
    add_review,
    get_businesses,
    get_recommended_businesses,
    get_reports_summary,
    initialize_database,
    toggle_favorite,
)
from models import Business
from utils import (
    VerificationChallenge,
    check_verification_answer,
    generate_verification_challenge,
    get_current_timestamp,
    validate_business_name,
    validate_deal_text,
    validate_rating,
    validate_review_text,
)


APP_TITLE = "TownSquare – Local Business Guide"

# Color palette (white + blue) chosen for clarity and modern UX.
# Main surfaces are bright and clean; navigation uses deep blue for contrast.
COLOR_BG_MAIN = "#FFFFFF"
COLOR_BG_SIDEBAR = "#0B2D5B"  # Deep blue
COLOR_ACCENT = "#1E66D0"  # Primary blue accent for key actions
COLOR_TEXT_PRIMARY = "#0F172A"  # Near-black for readability on white
COLOR_TEXT_SECONDARY = "#475569"  # Muted slate
COLOR_CARD_BG = "#F1F7FF"  # Soft blue-tinted card background
COLOR_INPUT_BG = "#FFFFFF"

FONT_HEADING = ("Segoe UI", 16, "bold")
FONT_SUBHEADING = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 10)


class TownSquareApp(tk.Tk):
    """Main Tkinter application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1100x700")
        self.minsize(1000, 650)

        # High‑contrast background
        self.configure(bg=COLOR_BG_MAIN)

        # Apply a modern ttk style.
        self._configure_style()

        # Layout: sidebar on the left, content on the right.
        self.sidebar = Sidebar(self, on_nav=self.show_screen)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.container = tk.Frame(self, bg=COLOR_BG_MAIN)
        self.container.grid(row=0, column=1, sticky="nsew")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Screens
        self.screens: dict[str, tk.Frame] = {}
        self._create_screens()

        self.show_screen("directory")

    # ------------------------- style ---------------------------------#

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        # Use the system's default theme then customize.
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TFrame",
            background=COLOR_BG_MAIN,
        )
        style.configure(
            "Card.TFrame",
            background=COLOR_CARD_BG,
        )
        style.configure(
            "Accent.TButton",
            font=FONT_BODY,
            padding=6,
            foreground="#FFFFFF",
            background=COLOR_ACCENT,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#2A73DE")],
        )
        style.configure(
            "Nav.TButton",
            font=FONT_BODY,
            padding=8,
            foreground="#FFFFFF",
            background=COLOR_BG_SIDEBAR,
        )
        style.map(
            "Nav.TButton",
            background=[("active", "#123D77")],
        )

        style.configure(
            "Treeview",
            background=COLOR_INPUT_BG,
            foreground=COLOR_TEXT_PRIMARY,
            fieldbackground=COLOR_INPUT_BG,
            rowheight=26,
            borderwidth=0,
            font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            font=FONT_SUBHEADING,
            background=COLOR_BG_SIDEBAR,
            foreground="#FFFFFF",
        )

    # ------------------------- screens --------------------------------#

    def _create_screens(self) -> None:
        self.screens["directory"] = DirectoryScreen(self.container)
        self.screens["favorites"] = DirectoryScreen(
            self.container, favorites_only=True
        )
        self.screens["recommendations"] = RecommendationScreen(self.container)
        self.screens["reports"] = ReportsScreen(self.container)
        self.screens["help"] = HelpScreen(self.container)

        for frame in self.screens.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, name: str) -> None:
        """Bring a screen to the front."""
        frame = self.screens.get(name)
        if frame is not None:
            if isinstance(frame, DataAwareScreen):
                frame.refresh()
            frame.tkraise()


class Sidebar(tk.Frame):
    """Left navigation bar with icons and clear labels."""

    def __init__(self, master: tk.Misc, on_nav) -> None:
        super().__init__(master, bg=COLOR_BG_SIDEBAR, width=220)
        self.on_nav = on_nav

        title = tk.Label(
            self,
            text="Town Square",
            font=FONT_HEADING,
            fg="#FFFFFF",
            bg=COLOR_BG_SIDEBAR,
        )
        title.pack(padx=16, pady=(20, 4), anchor="w")

        subtitle = tk.Label(
            self,
            text="Byte‑Sized Business Boost",
            font=FONT_SMALL,
            fg="#D6E6FF",
            bg=COLOR_BG_SIDEBAR,
            wraplength=180,
            justify="left",
        )
        subtitle.pack(padx=16, pady=(0, 20), anchor="w")

        self._add_nav_button("📚  Directory", "directory")
        self._add_nav_button("⭐  Favorites", "favorites")
        self._add_nav_button("💡  Recommendations", "recommendations")
        self._add_nav_button("📊  Reports", "reports")

        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=12, pady=18)

        self._add_nav_button("❓  Help & Instructions", "help")

        footer = tk.Label(
            self,
            text="Designed for FBLA\n2025–2026",
            font=FONT_SMALL,
            fg="#D6E6FF",
            bg=COLOR_BG_SIDEBAR,
            justify="left",
        )
        footer.pack(side="bottom", padx=16, pady=18, anchor="w")

    def _add_nav_button(self, text: str, screen_name: str) -> None:
        btn = ttk.Button(
            self,
            text=text,
            style="Nav.TButton",
            command=lambda: self.on_nav(screen_name),
        )
        btn.pack(fill="x", padx=12, pady=4)


class DataAwareScreen(tk.Frame):
    """Base class for screens that can refresh their data."""

    def refresh(self) -> None:  # pragma: no cover - UI glue
        pass


class DirectoryScreen(DataAwareScreen):
    """
    Shows businesses in a table, with sorting, filtering,
    favorite toggling, and review submission.
    """

    def __init__(self, master: tk.Misc, favorites_only: bool = False) -> None:
        super().__init__(master, bg=COLOR_BG_MAIN)
        self.favorites_only = favorites_only
        self.current_challenge: Optional[VerificationChallenge] = None
        self.selected_business: Optional[Business] = None

        title_text = "Business Directory" if not favorites_only else "Favorite Businesses"
        subtitle_text = (
            "Browse all small, local businesses in Town Square."
            if not favorites_only
            else "Your bookmarked local favorites, at a glance."
        )

        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", padx=20, pady=(18, 8))

        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text=subtitle_text,
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_label.pack(anchor="w", pady=(2, 8))

        controls_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        controls_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Category filter
        tk.Label(
            controls_frame,
            text="Category:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).pack(side="left", padx=(0, 6))

        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.category_var,
            state="readonly",
            values=["All", "Food", "Retail", "Services"],
            width=12,
        )
        self.category_combo.pack(side="left")

        # Rating sort
        self.sort_var = tk.BooleanVar(value=False)
        sort_check = tk.Checkbutton(
            controls_frame,
            text="Sort by rating (high to low)",
            variable=self.sort_var,
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
            activebackground=COLOR_BG_MAIN,
            activeforeground=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_CARD_BG,
        )
        sort_check.pack(side="left", padx=(20, 0))

        apply_btn = ttk.Button(
            controls_frame,
            text="Apply Filters",
            style="Accent.TButton",
            command=self.refresh,
        )
        apply_btn.pack(side="right")

        add_btn = ttk.Button(
            controls_frame,
            text="Add New Business",
            style="Accent.TButton",
            command=self._open_add_business_dialog,
        )
        add_btn.pack(side="right", padx=(0, 10))

        # Main content: list on the left, detail + review on the right
        main_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)

        self._build_business_table(main_frame)
        self._build_detail_and_review(main_frame)

        self.refresh()

    def _build_business_table(self, master: tk.Frame) -> None:
        table_frame = ttk.Frame(master, style="Card.TFrame")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        columns = ("name", "category", "rating", "deal", "favorite")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("name", text="Business")
        self.tree.heading("category", text="Category")
        self.tree.heading("rating", text="Rating")
        self.tree.heading("deal", text="Special Deal")
        self.tree.heading("favorite", text="★")

        self.tree.column("name", width=160, anchor="w")
        self.tree.column("category", width=80, anchor="center")
        self.tree.column("rating", width=70, anchor="center")
        self.tree.column("deal", width=200, anchor="w")
        self.tree.column("favorite", width=40, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def _build_detail_and_review(self, master: tk.Frame) -> None:
        right_frame = ttk.Frame(master, style="Card.TFrame")
        right_frame.grid(row=0, column=1, sticky="nsew")

        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(3, weight=1)

        self.detail_title = tk.Label(
            right_frame,
            text="Select a business to see details",
            font=FONT_SUBHEADING,
            fg=COLOR_ACCENT,
            bg=COLOR_CARD_BG,
            anchor="w",
        )
        self.detail_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))

        self.detail_info = tk.Label(
            right_frame,
            text="",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            justify="left",
            wraplength=420,
        )
        self.detail_info.grid(row=1, column=0, sticky="ew", padx=14)

        self.favorite_var = tk.BooleanVar(value=False)
        self.favorite_btn = ttk.Button(
            right_frame,
            text="Mark as Favorite",
            style="Accent.TButton",
            command=self._toggle_favorite_clicked,
        )
        self.favorite_btn.grid(row=2, column=0, sticky="w", padx=14, pady=(8, 6))

        separator = ttk.Separator(right_frame, orient="horizontal")
        separator.grid(row=3, column=0, sticky="ew", padx=10, pady=(4, 6))

        review_label = tk.Label(
            right_frame,
            text="Share your experience (review & rating):",
            font=FONT_SUBHEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="w",
        )
        review_label.grid(row=4, column=0, sticky="ew", padx=14)

        rating_frame = tk.Frame(right_frame, bg=COLOR_CARD_BG)
        rating_frame.grid(row=5, column=0, sticky="ew", padx=14, pady=(4, 0))

        tk.Label(
            rating_frame,
            text="Rating (1–5):",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        ).pack(side="left")

        self.rating_entry = ttk.Entry(rating_frame, width=5)
        self.rating_entry.pack(side="left", padx=(6, 0))

        self.review_text = tk.Text(
            right_frame,
            height=6,
            wrap="word",
            font=FONT_BODY,
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT_PRIMARY,
        )
        self.review_text.grid(row=6, column=0, sticky="nsew", padx=14, pady=(6, 2))

        # Verification area
        verify_frame = tk.Frame(right_frame, bg=COLOR_CARD_BG)
        verify_frame.grid(row=7, column=0, sticky="ew", padx=14, pady=(4, 0))

        self.verify_label = tk.Label(
            verify_frame,
            text="Human check: click 'New Challenge' before submitting.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
            wraplength=350,
            justify="left",
        )
        self.verify_label.grid(row=0, column=0, columnspan=3, sticky="w")

        self.verify_question_label = tk.Label(
            verify_frame,
            text="",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        self.verify_question_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        tk.Label(
            verify_frame,
            text="Your answer:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        ).grid(row=1, column=1, sticky="e", padx=(10, 4))

        self.verify_entry = ttk.Entry(verify_frame, width=8)
        self.verify_entry.grid(row=1, column=2, sticky="w")

        challenge_btn = ttk.Button(
            verify_frame,
            text="New Challenge",
            command=self._new_challenge,
        )
        challenge_btn.grid(row=2, column=0, sticky="w", pady=(6, 0))

        submit_btn = ttk.Button(
            verify_frame,
            text="Submit Review",
            style="Accent.TButton",
            command=self._submit_review_clicked,
        )
        submit_btn.grid(row=2, column=2, sticky="e", pady=(6, 0))

    # --------------------- data operations ----------------------------#

    def refresh(self) -> None:
        """Reload the business list from the database."""
        self.tree.delete(*self.tree.get_children())
        category = self.category_var.get()
        sort_by_rating = self.sort_var.get()

        businesses = get_businesses(
            category_filter=category,
            sort_by_rating_desc=sort_by_rating,
            favorites_only=self.favorites_only,
        )

        for biz in businesses:
            rating_display = (
                f"{biz.average_rating:.1f} ({biz.review_count})"
                if biz.review_count > 0
                else "No reviews yet"
            )
            favorite_icon = "★" if biz.is_favorite else ""
            self.tree.insert(
                "",
                "end",
                iid=str(biz.id),
                values=(
                    biz.name,
                    biz.category,
                    rating_display,
                    biz.deal_text,
                    favorite_icon,
                ),
            )

        # If we are in the favorites screen and there are no favorites yet,
        # gently guide the user back to the directory.
        if self.favorites_only and not businesses:
            self.detail_title.config(text="No favorites yet")
            self.detail_info.config(
                text=(
                    "You have not marked any businesses as favorites.\n\n"
                    "Tip: Go to the Directory screen and look for the gold "
                    "“Mark as Favorite” button under a business you love."
                )
            )
        else:
            self.detail_title.config(text="Select a business to see details")
            self.detail_info.config(text="")

        self.selected_business = None
        self._clear_review_form()

    def _on_tree_select(self, event) -> None:  # pragma: no cover - UI callback
        item_id = self.tree.selection()
        if not item_id:
            return
        biz_id = int(item_id[0])

        # We only need one business, so filter quickly.
        businesses = get_businesses(
            category_filter="All",
            sort_by_rating_desc=False,
            favorites_only=False,
        )
        for biz in businesses:
            if biz.id == biz_id:
                self._set_selected_business(biz)
                return

    def _set_selected_business(self, biz: Business) -> None:
        self.selected_business = biz

        rating_text = (
            f"Average rating: {biz.average_rating:.1f} from {biz.review_count} review(s)"
            if biz.review_count > 0
            else "This business has not been rated yet."
        )

        info = (
            f"Category: {biz.category}\n"
            f"{rating_text}\n\n"
            f"Special deal or coupon:\n{biz.deal_text}"
        )

        self.detail_title.config(text=biz.name)
        self.detail_info.config(text=info)
        self.favorite_var.set(biz.is_favorite)
        self._update_favorite_button_text()

    def _update_favorite_button_text(self) -> None:
        if self.favorite_var.get():
            self.favorite_btn.config(text="★ Favorited – click to remove")
        else:
            self.favorite_btn.config(text="Mark as Favorite")

    def _toggle_favorite_clicked(self) -> None:
        if not self.selected_business:
            messagebox.showinfo(
                "No business selected",
                "Please select a business from the list first.",
            )
            return

        new_state = not self.favorite_var.get()
        try:
            toggle_favorite(self.selected_business.id, new_state)
            self.favorite_var.set(new_state)
            self._update_favorite_button_text()
            self.refresh()
        except Exception as exc:  # pragma: no cover - defensive
            messagebox.showerror(
                "Error updating favorite",
                f"Something went wrong while saving your favorite.\n\nDetails: {exc}",
            )
            return

    def _new_challenge(self) -> None:
        self.current_challenge = generate_verification_challenge()
        self.verify_question_label.config(text=self.current_challenge.prompt)
        self.verify_entry.delete(0, tk.END)

    def _clear_review_form(self) -> None:
        self.rating_entry.delete(0, tk.END)
        self.review_text.delete("1.0", tk.END)
        self.verify_entry.delete(0, tk.END)
        self.verify_question_label.config(text="")
        self.current_challenge = None

    def _submit_review_clicked(self) -> None:
        if not self.selected_business:
            messagebox.showinfo(
                "No business selected",
                "Please select a business before submitting a review.",
            )
            return

        rating_str = self.rating_entry.get()
        review_body = self.review_text.get("1.0", tk.END)

        rating_ok, rating_msg = validate_rating(rating_str)
        if not rating_ok:
            messagebox.showwarning("Check your rating", rating_msg)
            return

        text_ok, text_msg = validate_review_text(review_body)
        if not text_ok:
            messagebox.showwarning("Review needs attention", text_msg)
            return

        if not self.current_challenge:
            messagebox.showwarning(
                "Verification required",
                "Please click “New Challenge” and answer the human‑check "
                "question before submitting your review.",
            )
            return

        if not check_verification_answer(
            self.current_challenge, self.verify_entry.get()
        ):
            messagebox.showerror(
                "Verification failed",
                "The answer to the human‑check question was not correct.\n\n"
                "This step helps prevent bots from spamming fake reviews.\n"
                "Please try again with a new challenge.",
            )
            self._new_challenge()
            return

        rating_value = int(rating_str)

        try:
            add_review(
                business_id=self.selected_business.id,
                rating=rating_value,
                text=review_body.strip(),
                created_at=get_current_timestamp(),
            )
        except Exception as exc:  # pragma: no cover - defensive
            messagebox.showerror(
                "Error saving review",
                f"Something went wrong while saving your review.\n\nDetails: {exc}",
            )
            return

        messagebox.showinfo(
            "Thank you!",
            "Your review has been saved and will help others discover this business.",
        )
        self._clear_review_form()
        self.refresh()

    def _open_add_business_dialog(self) -> None:
        """Open the dialog used to add a new business to the platform."""

        def on_added(new_business: Business) -> None:
            # Refresh the list and highlight the newly added business.
            self.refresh()
            item_id = str(new_business.id)
            if item_id in self.tree.get_children():
                self.tree.selection_set(item_id)
                self.tree.see(item_id)
                self._set_selected_business(new_business)

        AddBusinessDialog(self, on_added=on_added)


class RecommendationScreen(DataAwareScreen):
    """Shows recommended businesses using simple, explainable rules."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=COLOR_BG_MAIN)

        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", padx=20, pady=(18, 8))

        title_label = tk.Label(
            header_frame,
            text="Smart Recommendations",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text=(
                "Town Square suggests businesses by looking at your favorites, "
                "preferred category, and high community ratings."
            ),
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
            wraplength=700,
            justify="left",
        )
        subtitle_label.pack(anchor="w", pady=(2, 6))

        controls_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        controls_frame.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(
            controls_frame,
            text="Preferred category:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).pack(side="left", padx=(0, 6))

        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.category_var,
            state="readonly",
            values=["All", "Food", "Retail", "Services"],
            width=12,
        )
        self.category_combo.pack(side="left")

        refresh_btn = ttk.Button(
            controls_frame,
            text="Show Suggestions",
            style="Accent.TButton",
            command=self.refresh,
        )
        refresh_btn.pack(side="left", padx=(12, 0))

        explanation_label = tk.Label(
            self,
            text=(
                "How it works:\n"
                "1. Businesses you have marked as favorites appear first.\n"
                "2. Within your selected category, places with higher ratings are "
                "ranked above others.\n"
                "3. If there are not many matches, Town Square falls back to the "
                "highest‑rated options overall.\n\n"
                "This makes the logic easy to explain to judges while still "
                "feeling smart to users."
            ),
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
            justify="left",
            wraplength=760,
        )
        explanation_label.pack(fill="x", padx=20, pady=(4, 10))

        table_frame = ttk.Frame(self, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        columns = ("name", "category", "rating", "deal", "favorite")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("name", text="Business")
        self.tree.heading("category", text="Category")
        self.tree.heading("rating", text="Rating")
        self.tree.heading("deal", text="Special Deal")
        self.tree.heading("favorite", text="★")

        self.tree.column("name", width=180, anchor="w")
        self.tree.column("category", width=90, anchor="center")
        self.tree.column("rating", width=90, anchor="center")
        self.tree.column("deal", width=260, anchor="w")
        self.tree.column("favorite", width=40, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        category = self.category_var.get()
        businesses = get_recommended_businesses(preferred_category=category)

        for biz in businesses:
            rating_display = (
                f"{biz.average_rating:.1f} ({biz.review_count})"
                if biz.review_count > 0
                else "No reviews yet"
            )
            favorite_icon = "★" if biz.is_favorite else ""
            self.tree.insert(
                "",
                "end",
                iid=str(biz.id),
                values=(
                    biz.name,
                    biz.category,
                    rating_display,
                    biz.deal_text,
                    favorite_icon,
                ),
            )


class ReportsScreen(DataAwareScreen):
    """Shows key analytics about the local business community."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=COLOR_BG_MAIN)

        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", padx=20, pady=(18, 8))

        title_label = tk.Label(
            header_frame,
            text="Community Snapshot & Reports",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text=(
                "Quickly see how many local businesses are listed, "
                "how well they are rated, and which ones stand out."
            ),
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_label.pack(anchor="w", pady=(2, 8))

        content_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Summary metrics
        summary_card = ttk.Frame(content_frame, style="Card.TFrame")
        summary_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        summary_title = tk.Label(
            summary_card,
            text="Key Numbers",
            font=FONT_SUBHEADING,
            fg=COLOR_ACCENT,
            bg=COLOR_CARD_BG,
        )
        summary_title.pack(anchor="w", padx=14, pady=(12, 6))

        self.total_label = tk.Label(
            summary_card,
            text="Total businesses: –",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="w",
        )
        self.total_label.pack(fill="x", padx=14, pady=2)

        self.average_label = tk.Label(
            summary_card,
            text="Average rating (all businesses): –",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="w",
        )
        self.average_label.pack(fill="x", padx=14, pady=2)

        self.favorite_label = tk.Label(
            summary_card,
            text="Number of favorited businesses: –",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="w",
        )
        self.favorite_label.pack(fill="x", padx=14, pady=(2, 12))

        # Top businesses table
        top_card = ttk.Frame(content_frame, style="Card.TFrame")
        top_card.grid(row=0, column=1, sticky="nsew", pady=(0, 10))

        top_title = tk.Label(
            top_card,
            text="Top 3 Highest‑Rated Businesses",
            font=FONT_SUBHEADING,
            fg=COLOR_ACCENT,
            bg=COLOR_CARD_BG,
        )
        top_title.pack(anchor="w", padx=14, pady=(12, 6))

        columns = ("rank", "name", "category", "rating")
        self.tree = ttk.Treeview(
            top_card,
            columns=columns,
            show="headings",
            selectmode="none",
        )
        self.tree.heading("rank", text="#")
        self.tree.heading("name", text="Business")
        self.tree.heading("category", text="Category")
        self.tree.heading("rating", text="Average Rating")

        self.tree.column("rank", width=30, anchor="center")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("category", width=100, anchor="center")
        self.tree.column("rating", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        self.refresh()

    def refresh(self) -> None:
        summary = get_reports_summary()

        self.total_label.config(text=f"Total businesses: {summary.total_businesses}")
        self.average_label.config(
            text=f"Average rating (businesses with reviews): {summary.average_rating:.2f}"
        )
        self.favorite_label.config(
            text=f"Number of favorited businesses: {summary.favorite_count}"
        )

        self.tree.delete(*self.tree.get_children())
        for index, biz in enumerate(summary.top_businesses, start=1):
            self.tree.insert(
                "",
                "end",
                values=(
                    index,
                    biz.name,
                    biz.category,
                    f"{biz.average_rating:.2f} ({biz.review_count})",
                ),
            )


class HelpScreen(tk.Frame):
    """In‑app instructions screen."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=COLOR_BG_MAIN)

        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", padx=20, pady=(18, 8))

        title_label = tk.Label(
            header_frame,
            text="Help & Instructions",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame,
            text="A quick tour of how to use Town Square during judging or in real life.",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        subtitle_label.pack(anchor="w", pady=(2, 8))

        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        text = (
            "Overview\n"
            "────────\n"
            "Town Square is a small‑business discovery tool built specifically for the "
            "FBLA Coding & Programming topic “Byte‑Sized Business Boost”.\n\n"
            "Navigation\n"
            "──────────\n"
            "• Directory – Browse all local businesses, see their deals, and read ratings.\n"
            "• Favorites – Quickly jump to businesses you have marked with a star.\n"
            "• Recommendations – See smart suggestions based on favorites, category, and ratings.\n"
            "• Reports – View summary statistics and the top three highest‑rated businesses.\n"
            "• Help – The screen you are reading now.\n\n"
            "Adding Reviews & Ratings\n"
            "────────────────────────\n"
            "1. Go to the Directory screen.\n"
            "2. Click a business in the list on the left.\n"
            "3. Enter a rating from 1 to 5 and type a short review.\n"
            "4. Click “New Challenge” and answer the simple math question.\n"
            "5. Click “Submit Review”. If any input is invalid, a friendly error message "
            "will explain what to fix.\n\n"
            "Favorites & Deals\n"
            "────────────────\n"
            "• Use the gold “Mark as Favorite” button to bookmark a business.\n"
            "• The Directory and Recommendations screens show a star icon next to favorites.\n"
            "• Each business includes a clearly displayed special deal or coupon.\n\n"
            "Accessibility\n"
            "─────────────\n"
            "• Large, high‑contrast fonts make text readable from a distance during judging.\n"
            "• Clear button labels explain exactly what each action does.\n"
            "• The layout avoids clutter so users can focus on a single panel at a time.\n"
        )

        instructions = tk.Label(
            card,
            text=text,
            justify="left",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="nw",
        )
        instructions.pack(fill="both", expand=True, padx=16, pady=16)


class AddBusinessDialog(tk.Toplevel):
    """
    Dialog for adding a new business.

    This dialog uses a two‑step human verification (two math challenges)
    before the business is actually added to the directory.
    """

    CATEGORIES = ("Food", "Retail", "Services")

    def __init__(self, master: tk.Misc, on_added) -> None:
        super().__init__(master)
        self.title("Add New Business")
        self.configure(bg=COLOR_BG_MAIN)
        self.resizable(False, False)
        self.on_added = on_added

        self.challenge_one: Optional[VerificationChallenge] = None
        self.challenge_two: Optional[VerificationChallenge] = None

        # Ensure the dialog appears above the main window and grabs focus.
        self.transient(master.winfo_toplevel())
        self.grab_set()

        container = tk.Frame(self, bg=COLOR_BG_MAIN)
        container.pack(fill="both", expand=True, padx=20, pady=16)

        title = tk.Label(
            container,
            text="Add a New Local Business",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        subtitle = tk.Label(
            container,
            text=(
                "Use this form to list a new small business in Town Square.\n"
                "To keep entries trustworthy, a quick two‑step human check is required."
            ),
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
            justify="left",
            wraplength=420,
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Business name
        tk.Label(
            container,
            text="Business name:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).grid(row=2, column=0, sticky="e", padx=(0, 8), pady=(4, 2))

        self.name_entry = ttk.Entry(container, width=40)
        self.name_entry.grid(row=2, column=1, sticky="w", pady=(4, 2))

        # Category
        tk.Label(
            container,
            text="Category:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).grid(row=3, column=0, sticky="e", padx=(0, 8), pady=(4, 2))

        self.category_var = tk.StringVar(value="Food")
        self.category_combo = ttk.Combobox(
            container,
            textvariable=self.category_var,
            state="readonly",
            values=list(self.CATEGORIES),
            width=18,
        )
        self.category_combo.grid(row=3, column=1, sticky="w", pady=(4, 2))

        # Deal text
        tk.Label(
            container,
            text="Special deal or coupon:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).grid(row=4, column=0, sticky="ne", padx=(0, 8), pady=(6, 2))

        self.deal_text = tk.Text(
            container,
            height=4,
            width=40,
            wrap="word",
            font=FONT_BODY,
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT_PRIMARY,
        )
        self.deal_text.grid(row=4, column=1, sticky="w", pady=(6, 2))

        # Verification section
        sep = ttk.Separator(container, orient="horizontal")
        sep.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 8))

        verify_label = tk.Label(
            container,
            text="Two‑step human verification",
            font=FONT_SUBHEADING,
            fg=COLOR_ACCENT,
            bg=COLOR_BG_MAIN,
        )
        verify_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 4))

        helper = tk.Label(
            container,
            text=(
                "To prevent automated bots from listing fake businesses, please "
                "solve both quick math questions below before submitting."
            ),
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
            justify="left",
            wraplength=420,
        )
        helper.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Challenge 1
        self.challenge1_label = tk.Label(
            container,
            text="Step 1 question will appear here.",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        self.challenge1_label.grid(row=8, column=0, columnspan=2, sticky="w")

        tk.Label(
            container,
            text="Your answer (step 1):",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).grid(row=9, column=0, sticky="e", padx=(0, 8), pady=(2, 2))

        self.challenge1_entry = ttk.Entry(container, width=10)
        self.challenge1_entry.grid(row=9, column=1, sticky="w", pady=(2, 2))

        # Challenge 2
        self.challenge2_label = tk.Label(
            container,
            text="Step 2 question will appear here.",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        self.challenge2_label.grid(row=10, column=0, columnspan=2, sticky="w", pady=(6, 0))

        tk.Label(
            container,
            text="Your answer (step 2):",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        ).grid(row=11, column=0, sticky="e", padx=(0, 8), pady=(2, 2))

        self.challenge2_entry = ttk.Entry(container, width=10)
        self.challenge2_entry.grid(row=11, column=1, sticky="w", pady=(2, 2))

        # Buttons
        button_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        button_frame.grid(row=12, column=0, columnspan=2, sticky="e", pady=(10, 0))

        gen_btn = ttk.Button(
            button_frame,
            text="New Questions",
            style="Accent.TButton",
            command=self._generate_challenges,
        )
        gen_btn.pack(side="left", padx=(0, 8))

        submit_btn = ttk.Button(
            button_frame,
            text="Save Business",
            style="Accent.TButton",
            command=self._submit,
        )
        submit_btn.pack(side="left")

        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
        )
        cancel_btn.pack(side="left", padx=(8, 0))

        # Start with challenges ready.
        self._generate_challenges()

    def _generate_challenges(self) -> None:
        """Create two fresh math questions."""
        self.challenge_one = generate_verification_challenge()
        self.challenge_two = generate_verification_challenge()

        self.challenge1_label.config(text=f"Step 1: {self.challenge_one.prompt}")
        self.challenge2_label.config(text=f"Step 2: {self.challenge_two.prompt}")

        self.challenge1_entry.delete(0, tk.END)
        self.challenge2_entry.delete(0, tk.END)

    def _submit(self) -> None:
        """Validate all fields, run two-step verification, and add the business."""
        name = self.name_entry.get()
        category = self.category_var.get()
        deal = self.deal_text.get("1.0", tk.END)

        # Basic field validation
        ok, msg = validate_business_name(name)
        if not ok:
            messagebox.showwarning("Check business name", msg, parent=self)
            return

        if category not in self.CATEGORIES:
            messagebox.showwarning(
                "Check category",
                "Please choose a valid category: Food, Retail, or Services.",
                parent=self,
            )
            return

        ok, msg = validate_deal_text(deal)
        if not ok:
            messagebox.showwarning("Check deal text", msg, parent=self)
            return

        # Ensure challenges exist
        if not self.challenge_one or not self.challenge_two:
            messagebox.showwarning(
                "Verification required",
                "Please click “New Questions” to generate both verification steps before saving.",
                parent=self,
            )
            return

        # Two-step human verification
        if not check_verification_answer(self.challenge_one, self.challenge1_entry.get()):
            messagebox.showerror(
                "Step 1 failed",
                "The answer to the first verification question was not correct.\n\n"
                "Both steps must be solved correctly to add a new business.",
                parent=self,
            )
            self._generate_challenges()
            return

        if not check_verification_answer(self.challenge_two, self.challenge2_entry.get()):
            messagebox.showerror(
                "Step 2 failed",
                "The answer to the second verification question was not correct.\n\n"
                "Both steps must be solved correctly to add a new business.",
                parent=self,
            )
            self._generate_challenges()
            return

        try:
            new_business = add_business(name=name, category=category, deal_text=deal)
        except Exception as exc:  # pragma: no cover - defensive
            messagebox.showerror(
                "Error saving business",
                f"Something went wrong while saving this business.\n\nDetails: {exc}",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Business added",
            "Your new business has been added to Town Square.",
            parent=self,
        )

        # Notify the parent screen and close the dialog.
        self.on_added(new_business)
        self.destroy()


def run_app() -> None:
    """
    Create the database (if needed) and start the main UI loop.

    This function is imported and called from main.py so that
    the entry point is crystal clear for judges.
    """
    try:
        initialize_database()
    except Exception as exc:  # pragma: no cover - defensive
        messagebox.showerror(
            "Database error",
            f"Town Square could not initialize its local database.\n\nDetails: {exc}",
        )
        return

    app = TownSquareApp()
    app.mainloop()

