"""SQLite based movie storage using SQLAlchemy with project folder structure.

"""

import os
from pathlib import Path

from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parent.parent


DB_PATH = BASE_DIR / "data" / "movies.db"
DB_URL = f"sqlite:///{DB_PATH}"


engine = create_engine(DB_URL, echo=False)


with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL,
            poster_url TEXT
        )
    """))
    connection.commit()


def list_movies():
    """Retrieve all movies from the database.

    Returns:
        dict: {"Title": {"year": int, "rating": float, "poster_url": str}, ...}
    """
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT title, year, rating, poster_url FROM movies")
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


def add_movie(title, year, rating, poster_url):
    """Add a new movie to the database."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text(
                    "INSERT INTO movies (title, year, rating, poster_url) "
                    "VALUES (:title, :year, :rating, :poster_url)"
                ),
                {
                    "title": title,
                    "year": year,
                    "rating": rating,
                    "poster_url": poster_url,
                },
            )
            connection.commit()
            print(f"Movie '{title}' added successfully.")
        except Exception as exc:
            print(f"Error: {exc}")


def delete_movie(title):
    """Delete a movie from the database by title."""
    with engine.connect() as connection:
        result = connection.execute(
            text("DELETE FROM movies WHERE title = :title"),
            {"title": title},
        )
        connection.commit()

        if result.rowcount == 0:
            print(f"Movie '{title}' not found.")
        else:
            print(f"Movie '{title}' deleted successfully.")


def update_movie(title, rating):
    """Update a movie rating in the database by title."""
    with engine.connect() as connection:
        result = connection.execute(
            text("UPDATE movies SET rating = :rating WHERE title = :title"),
            {"rating": rating, "title": title},
        )
        connection.commit()

        if result.rowcount == 0:
            print(f"Movie '{title}' not found.")
        else:
            print(f"Movie '{title}' updated successfully.")
