"""Command line movie application using SQLite storage and OMDb API."""

import os
import random
import statistics
from pathlib import Path

import requests

from storage import movie_storage_sql as storage


OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def print_menu():
    """Print the main menu."""
    print("\n== Movie Database ==")
    print("0. Exit")
    print("1. List movies")
    print("2. Add movie (from OMDb)")
    print("3. Delete movie")
    print("4. Update movie rating")
    print("5. Stats")
    print("6. Random movie")
    print("7. Search movie")
    print("8. Movies sorted by rating (desc)")
    print("9. Generate website")


def fetch_movie_from_omdb(title):
    """Fetch movie information from OMDb by title.

    Args:
        title (str): Movie title to search for.

    Returns:
        dict | None: Parsed OMDb JSON data or None on error.
    """
    if not OMDB_API_KEY:
        print("Error: OMDb API key not set. Please set OMDB_API_KEY env variable.")
        return None

    url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "t": title,
        "plot": "short",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"Error: could not reach OMDb API ({exc}).")
        return None

    data = response.json()

    if data.get("Response") == "False":
        print(f"OMDb error: {data.get('Error', 'Unknown error')}")
        return None

    return data


def parse_omdb_result(data):
    """Extract title, year, rating and poster URL from OMDb response.

    Args:
        data (dict): OMDb JSON result.

    Returns:
        tuple[str, int, float, str]: (title, year, rating, poster_url)
    """
    title = data.get("Title", "").strip()

    year_str = (data.get("Year") or "").strip()
    try:
        year = int(year_str[:4])
    except (ValueError, TypeError):
        year = 0

    rating_str = (data.get("imdbRating") or "").strip()
    if rating_str in ("N/A", ""):
        rating = 0.0
    else:
        try:
            rating = float(rating_str)
        except ValueError:
            rating = 0.0

    poster_url = data.get("Poster") or ""

    return title, year, rating, poster_url


def command_list_movies():
    """Retrieve and display all movies from the database."""
    movies = storage.list_movies()

    if not movies:
        print("No movies in database.")
        return

    print(f"\n{len(movies)} movies in total")
    for title, data in movies.items():
        print(f"{title} ({data['year']}): {data['rating']}")


def command_add_movie():
    """Ask the user for a title, fetch data from OMDb, and add movie."""
    user_title = input("Enter movie name: ").strip()
    if not user_title:
        print("Error: Title cannot be empty.")
        return

    omdb_data = fetch_movie_from_omdb(user_title)
    if not omdb_data:
        return

    title, year, rating, poster_url = parse_omdb_result(omdb_data)

    if not title:
        print("Error: could not extract title from OMDb response.")
        return

    if year == 0:
        print("Warning: could not parse year, storing 0.")

    storage.add_movie(title, year, rating, poster_url)


def command_delete_movie():
    """Ask the user for a movie title and delete it from the database."""
    title = input("Enter movie name to delete: ").strip()
    if not title:
        print("Error: Title cannot be empty.")
        return

    storage.delete_movie(title)


def command_update_movie():
    """Ask the user for a movie title and update its rating."""
    title = input("Enter movie name to update: ").strip()
    if not title:
        print("Error: Title cannot be empty.")
        return

    try:
        rating = float(input("Enter new rating (1-10): ").strip())
    except ValueError:
        print("Invalid rating (expected a number).")
        return

    storage.update_movie(title, rating)


def command_stats():
    """Calculate and print statistics about all movies."""
    movies = storage.list_movies()
    if not movies:
        print("No movies in database.")
        return

    ratings = [data["rating"] for data in movies.values()]
    avg = sum(ratings) / len(ratings)
    med = statistics.median(ratings)

    max_rating = max(ratings)
    min_rating = min(ratings)

    best = [t for t, d in movies.items() if d["rating"] == max_rating]
    worst = [t for t, d in movies.items() if d["rating"] == min_rating]

    print("\n== Stats ==")
    print(f"Average rating: {avg:.2f}")
    print(f"Median rating: {med:.2f}")
    print(f"Best ({max_rating}): " + ", ".join(best))
    print(f"Worst ({min_rating}): " + ", ".join(worst))


def command_random_movie():
    """Pick and print a random movie from the database."""
    movies = storage.list_movies()
    if not movies:
        print("No movies in database.")
        return

    title = random.choice(list(movies.keys()))
    data = movies[title]
    print(f"Random pick: {title} ({data['year']}), {data['rating']}")


def command_search_movie():
    """Search for movies whose title contains a user provided substring."""
    query = input("Enter part of movie name: ").strip().lower()
    if not query:
        print("Error: Search string cannot be empty.")
        return

    movies = storage.list_movies()
    matches = [
        (t, d)
        for t, d in movies.items()
        if query in t.lower()
    ]

    if not matches:
        print("No matches found.")
        return

    for title, data in matches:
        print(f"{title} ({data['year']}), {data['rating']}")


def command_movies_sorted():
    """Display all movies sorted by rating in descending order."""
    movies = storage.list_movies()
    if not movies:
        print("No movies in database.")
        return

    sorted_items = sorted(
        movies.items(),
        key=lambda item: item[1]["rating"],
        reverse=True,
    )
    for title, data in sorted_items:
        print(f"{title} ({data['year']}): {data['rating']}")


def command_generate_website():
    """Generate an HTML website from the template and stored movies."""
    movies = storage.list_movies()

    base_dir = Path(__file__).resolve().parent
  
    template_path = base_dir / "static" / "index_template.html"
    output_path = base_dir / "static" / "index.html"

    try:
        with open(template_path, "r", encoding="utf-8") as file:
            template = file.read()
    except FileNotFoundError:
        print(f"Error: template file not found at {template_path}")
        return

    title_text = "My Movie App"

    movie_grid_html = ""
    for title, data in movies.items():
        year = data.get("year", "N/A")
        rating = data.get("rating", "N/A")
        poster_url = data.get("poster_url") or ""

        movie_grid_html += f"""
        <li>
            <div class="movie">
                <img class="movie-poster" src="{poster_url}" alt="Poster for {title}">
                <div class="movie-title">{title}</div>
                <div class="movie-year">{year}</div>
            </div>
        </li>
        """

    html_content = template.replace("__TEMPLATE_TITLE__", title_text)
    html_content = html_content.replace("__TEMPLATE_MOVIE_GRID__", movie_grid_html)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    print("Website was generated successfully.")


def main():
    """Run the main interactive loop of the movie application."""
    actions = {
        "1": command_list_movies,
        "2": command_add_movie,
        "3": command_delete_movie,
        "4": command_update_movie,
        "5": command_stats,
        "6": command_random_movie,
        "7": command_search_movie,
        "8": command_movies_sorted,
        "9": command_generate_website,
    }

    while True:
        print_menu()
        choice = input("Choose an option (0-9): ").strip()
        if choice == "0":
            print("Goodbye!")
            break

        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice. Please select 0-9.")


if __name__ == "__main__":
    main()
