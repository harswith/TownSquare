# TownSquare
Official project for the 2025-2026 FBLA "Coding and Programming" event done alongside Suhas Rallabhandi
Alright let's elaborate:

The program runs fully offline, uses a local SQLite database for persistence, and presents a modern, high‑contrast Tkinter interface that is easy for judges and everyday users to understand.

- **Business directory**
  - Shows each business’s **name, category (Food / Retail / Services), rating, review count, deal/coupon, and favorite status**.
  - Uses a **clean table view** so judges can see many businesses at once.

- **Sorting & filtering**
  - Filter by **category** (`All`, `Food`, `Retail`, `Services`).
  - Optional checkbox to **sort by rating (high → low)**.

- **Reviews & ratings**
  - Users may select any business and **add a rating (1–5) and written review**.
  - Inputs are **validated** (correct range, required length, and clear error messages).
  - Ratings automatically update the business’s **average rating and review count**.

- **Favorites system**
  - Gold **“Mark as Favorite”** button under each selected business.
  - Favorites are shown with a **star icon** in the directory, recommendations, and reports.
  - **Favorites screen** shows only favorited businesses for quick access.

- **Coupons / deals display**
  - Every business has a **“Special deal or coupon”** text field.
  - Deals are shown in the directory table and in the business details panel.

- **Human‑verification before reviews**
  - Before submitting a review, users must complete a **simple math challenge** (e.g., “What is 7 + 3?”).
  - Incorrect answers **block submission** and show a helpful error.

- **Intelligent recommendation system**
  - **Recommendations screen** suggests businesses using an **explainable rule‑based system**:
    1. Favorites appear first.
    2. Within the user’s **preferred category**, higher‑rated businesses are ranked higher.
    3. If there are few matches, the app falls back to the **highest‑rated options overall**.

- **Reports & analytics**
  - **Reports screen** displays:
    - Total number of businesses.
    - Average rating (for businesses with at least one review).
    - Number of favorited businesses.
    - **Top 3 highest‑rated businesses** in a clear table.

- **In‑app Help / Instructions**
  - Dedicated **Help screen** accessible from the sidebar.
  - Explains navigation, review workflow, favorites, recommendations, and accessibility choices.


## File Structure

- `main.py` – Simple, readable program entry point that runs the GUI.
- `ui.py` – All **Tkinter UI** components: navigation sidebar, directory, favorites, recommendations, reports, and help screens.
- `database.py` – **SQLite database layer**, contains schema setup, queries, and report calculations.
- `models.py` – `dataclass` models (`Business`, `Review`, `ReportSummary`) to keep data organized and typed.
- `utils.py` – Reusable helpers for **input validation**, timestamps, and **human‑verification challenges**.
- `town_square.db` – SQLite database file, created automatically on first run (no manual setup needed).


## Installation & Run Instructions

### Requirements

- **Python 3.10+** (standard CPython build)
- No external internet access required.
- Uses only Python’s **standard library** (no third‑party packages).

### How to Run

1. Make sure you are in the project folder:
   - On Windows: open a terminal (Command Prompt or PowerShell) and run:  
     `cd "TownSquare 4.0"`

2. Start the program with:

   ```bash
   python main.py
   ```

3. The **Town Square** window will open.  
   You can now browse the directory, mark favorites, add reviews, view recommendations, and open the reports screen.

The SQLite database file `town_square.db` is created **automatically** on first launch and persists your data between sessions.


## Intelligent Recommendation System (for Judges)

The **Recommendations** screen implements an **intelligent but easy‑to‑explain** algorithm.  
It relies on three signals:

1. **Favorites** – Whether the user has starred the business.
2. **Preferred category** – The category chosen from the recommendations screen (`All`, `Food`, `Retail`, `Services`).
3. **Community rating** – Average rating and number of reviews.

**Logic (in simple steps):**

- The app first looks for businesses in the **preferred category**.
- Within that set, it sorts by:
  1. **Favorites first** (`is_favorite` descending),
  2. Then **average rating descending**,
  3. Then **review count descending**, and finally
  4. Business name (alphabetical) to break ties.
- If there are **no matches** in the chosen category, Town Square **falls back** to all businesses using the same ranking rules.

This creates a recommendation list that **feels smart** but remains completely transparent and easy to defend in an FBLA interview.

Implementation is in `database.py` in the `get_recommended_businesses` function, and the UI is in `ui.py` in the `RecommendationScreen` class.


## Human-Verification System (Bot Prevention)

Before users can submit a review, they must pass a **small logic‑based challenge**:

- The app randomly generates a **simple addition or subtraction** question, such as:
  - “What is 4 + 5?” or “What is 9 − 3?”
- The challenge is displayed next to a small entry box.
- The user must click **“New Challenge”**, read the question, and type the correct answer before clicking **“Submit Review”**.

If the answer is **missing, non‑numeric, or incorrect**:

- The review **is not saved**.
- A **clear error message** explains that the verification failed and invites the user to try again.
- A new challenge is generated to avoid simple brute‑force guessing.

Implementation details:

- Challenge creation: `generate_verification_challenge()` in `utils.py` (uses small integers and non‑negative subtraction).
- Checking answers: `check_verification_answer()` in `utils.py`.
- Integrated in the UI: `DirectoryScreen` in `ui.py` (methods `_new_challenge` and `_submit_review_clicked`).

This satisfies the rubric’s **bot prevention / verification** requirement without adding unnecessary complexity.


## Input Validation & Error Handling

The application validates both **syntax** and **meaning** of user inputs:

- **Rating validation (`utils.validate_rating`)**
  - Must be provided.
  - Must be a whole number between **1 and 5**.
  - Shows a friendly message if anything is incorrect.

- **Review text validation (`utils.validate_review_text`)**
  - Enforces a **minimum length** (to avoid empty or meaningless reviews).
  - Enforces a **maximum length** to avoid very long text that can clutter the UI.

- **Human‑verification validation**
  - Requires a challenge to have been generated.
  - Requires a correct numeric answer.

- **Error messages**
  - Use `tkinter.messagebox` with clear titles and short, friendly explanations.
  - Database operations are wrapped in `try / except` blocks with safe fallback messages.

All validation logic lives in `utils.py` and is used from the `DirectoryScreen` in `ui.py`.


## Accessibility & User Experience

The UI is intentionally designed for **clarity during competitions**:

- **High‑contrast color palette**
  - Dark background with light text and a warm gold accent (`#F2AA4C`).
  - Works well on projectors and classroom screens.

- **Readable typography**
  - Uses **Segoe UI** fonts with **large sizes** for headings and body text.
  - Tables and labels are easy to read from a distance.

- **Clear layout**
  - Left **sidebar navigation** with descriptive icons and labels.
  - Right content area dedicated to a **single screen at a time** (directory, favorites, etc.).
  - Avoids clutter and overwhelming information.

- **Obvious actions**
  - Gold **accent buttons** for key actions like “Apply Filters”, “Mark as Favorite”, and “Submit Review”.
  - Descriptive labels and helper text for the human‑verification step.

These design choices make the app **demo‑friendly** and accessible for a wide range of users and judges.


## Libraries Used

All dependencies are from the **Python standard library**:

- `tkinter` – GUI toolkit for the desktop interface.
- `sqlite3` – Local SQLite database for persistence across sessions.
- `dataclasses` – Clean and typed data models (`Business`, `Review`, `ReportSummary`).
- `pathlib`, `contextlib` – Safe file handling and context managers for database access.
- `datetime`, `random`, `typing` – Utility modules for timestamps, challenges, and type hints.

No external network access or third‑party packages are required, which keeps setup simple for FBLA judges.
