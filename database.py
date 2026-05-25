from datetime import datetime
from pathlib import Path
import csv
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "meal_recommender.db"
FEEDBACK_CSV = BASE_DIR / "feedback.csv"


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT DEFAULT '',
                region TEXT DEFAULT '',
                dietary_preference TEXT DEFAULT '',
                favorite_ingredients TEXT DEFAULT '',
                disliked_ingredients TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                entered_ingredients TEXT NOT NULL,
                recommended_meal TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                region TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

    demo_user = get_user_by_username("demo")
    if demo_user is None:
        create_user(
            username="demo",
            password="demo123",
            full_name="Demo User",
            region="Nationwide",
            dietary_preference="",
            favorite_ingredients="",
            disliked_ingredients="",
        )
        demo_user = get_user_by_username("demo")

    import_feedback_csv_once(demo_user["id"])


def create_user(
    username,
    password,
    full_name="",
    region="",
    dietary_preference="",
    favorite_ingredients="",
    disliked_ingredients="",
):
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username,
                    password_hash,
                    full_name,
                    region,
                    dietary_preference,
                    favorite_ingredients,
                    disliked_ingredients,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username.strip().lower(),
                    generate_password_hash(password),
                    full_name.strip(),
                    region.strip(),
                    dietary_preference.strip(),
                    favorite_ingredients.strip(),
                    disliked_ingredients.strip(),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

        return get_user_by_id(cursor.lastrowid)
    except sqlite3.IntegrityError:
        return None


def authenticate_user(username, password):
    user = get_user_by_username(username)

    if user and check_password_hash(user["password_hash"], password):
        return user

    return None


def get_user_by_username(username):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()

    return row


def get_user_by_id(user_id):
    if not user_id:
        return None

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return row


def update_user_profile(
    user_id,
    full_name,
    region,
    dietary_preference,
    favorite_ingredients,
    disliked_ingredients,
):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET full_name = ?,
                region = ?,
                dietary_preference = ?,
                favorite_ingredients = ?,
                disliked_ingredients = ?
            WHERE id = ?
            """,
            (
                full_name.strip(),
                region.strip(),
                dietary_preference.strip(),
                favorite_ingredients.strip(),
                disliked_ingredients.strip(),
                user_id,
            ),
        )


def save_feedback(user_id, ingredients_text, meal, feedback_type, region):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO feedback (
                user_id,
                timestamp,
                entered_ingredients,
                recommended_meal,
                feedback_type,
                region
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                datetime.now().isoformat(timespec="seconds"),
                ingredients_text,
                meal,
                feedback_type,
                region,
            ),
        )


def get_feedback_rows(user_id):
    if not user_id:
        return []

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM feedback
            WHERE user_id = ?
            ORDER BY timestamp DESC
            """,
            (user_id,),
        ).fetchall()

    return rows


def import_feedback_csv_once(demo_user_id):
    if not FEEDBACK_CSV.exists():
        return

    with get_connection() as connection:
        already_imported = connection.execute(
            "SELECT value FROM app_meta WHERE key = 'feedback_csv_imported'"
        ).fetchone()

        if already_imported:
            return

        with FEEDBACK_CSV.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                meal = (row.get("recommended_meal") or "").strip()
                feedback_type = (row.get("feedback_type") or "").strip()

                if not meal or not feedback_type:
                    continue

                connection.execute(
                    """
                    INSERT INTO feedback (
                        user_id,
                        timestamp,
                        entered_ingredients,
                        recommended_meal,
                        feedback_type,
                        region
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        demo_user_id,
                        row.get("timestamp") or datetime.now().isoformat(timespec="seconds"),
                        row.get("entered_ingredients") or "",
                        meal,
                        feedback_type,
                        row.get("region") or "",
                    ),
                )

        connection.execute(
            """
            INSERT INTO app_meta (key, value)
            VALUES ('feedback_csv_imported', ?)
            """,
            (datetime.now().isoformat(timespec="seconds"),),
        )
