"""SQLite based movie storage using SQLAlchemy with user profiles.

- DB liegt in data/movies.db
- Dieses Modul liegt im Paket storage/
- Users: Tabelle users
- Movies: Tabelle movies mit user_id als Foreign Key
"""

from pathlib import Path

from sqlalchemy import create_engine, text

# Basisverzeichnis = Projektroot (eine Ebene über storage/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Pfad zur Datenbank im data Ordner
DB_PATH = BASE_DIR / "data" / "movies.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Engine erzeugen
engine = create_engine(DB_URL, echo=False)


def init_db(drop_existing: bool = False) -> None:
    """Initialisiere Datenbank und Tabellen.

    Args:
        drop_existing (bool): Wenn True, bestehende Tabellen werden gelöscht.
                              Praktisch, wenn sich das Schema ändert.
    """
    with engine.begin() as connection:
        if drop_existing:
            connection.execute(text("DROP TABLE IF EXISTS movies"))
            connection.execute(text("DROP TABLE IF EXISTS users"))

        # Users Tabelle
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
                """
            )
        )

        # Movies Tabelle mit user_id
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    rating REAL NOT NULL,
                    poster_url TEXT,
                    user_id INTEGER NOT NULL,
                    UNIQUE (title, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
        )


# Beim Import einmal sicherstellen, dass Tabellen existieren
init_db(drop_existing=False)


# ---------- User Funktionen ----------

def list_users():
    """Liefert alle User als Liste von Dicts: [{'id': 1, 'name': 'John'}, ...]."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, name FROM users ORDER BY name"))
        rows = result.fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]


def get_user_by_id(user_id: int):
    """Hole einen Nutzer anhand der ID, oder None."""
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT id, name FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.fetchone()

    if row is None:
        return None

    return {"id": row[0], "name": row[1]}


def get_or_create_user(name: str):
    """Hole einen User nach Name oder lege ihn an.

    Returns:
        dict: {'id': int, 'name': str}
    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("User name cannot be empty")

    with engine.begin() as connection:
        # Existiert der User schon?
        result = connection.execute(
            text("SELECT id, name FROM users WHERE name = :name"),
            {"name": cleaned},
        )
        row = result.fetchone()

        if row:
            return {"id": row[0], "name": row[1]}

        # Neu anlegen
        connection.execute(
            text("INSERT INTO users (name) VALUES (:name)"),
            {"name": cleaned},
        )

        result = connection.execute(
            text("SELECT id, name FROM users WHERE name = :name"),
            {"name": cleaned},
        )
        row = result.fetchone()

    return {"id": row[0], "name": row[1]}


# ---------- Movie Funktionen ----------

def list_movies(user_id: int):
    """Retrieve all movies from the database for one user.

    Returns:
        dict: {"Title": {"year": int, "rating": float, "poster_url": str}, ...}
    """
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT title, year, rating, poster_url
                FROM movies
                WHERE user_id = :user_id
                ORDER BY title
                """
            ),
            {"user_id": user_id},
        )
        rows = result.fetchall()

    return {
        row[0]: {
            "year": row[1],
            "rating": row[2],
            "poster_url": row[3],
        }
        for row in rows
    }


def add_movie(title, year, rating, poster_url, user_id: int):
    """Add a new movie to the database for a specific user."""
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO movies (title, year, rating, poster_url, user_id)
                VALUES (:title, :year, :rating, :poster_url, :user_id)
                """
            ),
            {
                "title": title,
                "year": year,
                "rating": rating,
                "poster_url": poster_url,
                "user_id": user_id,
            },
        )
    print(f"Movie '{title}' added successfully for user id {user_id}.")


def delete_movie(title, user_id: int):
    """Delete a movie from the database by title for a specific user."""
    with engine.begin() as connection:
        result = connection.execute(
            text("DELETE FROM movies WHERE title = :title AND user_id = :user_id"),
            {"title": title, "user_id": user_id},
        )

    if result.rowcount == 0:
        print(f"Movie '{title}' not found for this user.")
    else:
        print(f"Movie '{title}' deleted successfully for this user.")


def update_movie(title, rating, user_id: int):
    """Update a movie rating in the database by title for a specific user."""
    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE movies
                SET rating = :rating
                WHERE title = :title AND user_id = :user_id
                """
            ),
            {"rating": rating, "title": title, "user_id": user_id},
        )

    if result.rowcount == 0:
        print(f"Movie '{title}' not found for this user.")
    else:
        print(f"Movie '{title}' updated successfully for this user.")
