"""Command line movie application using SQLite storage, OMDb API and user profiles."""

import os
import random
import statistics
from pathlib import Path

import requests

from storage import movie_storage_sql as storage


current_user = None


OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def print_menu():
    """Print the main menu for the active user."""
    global current_user
    user_label = current_user["name"] if current_user else "No user selected"
    print(f"\n== Movie Database ({user_label}) ==")
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
    print("10. Switch user")




def choose_user():
    """Zeige Userliste, lass Auswahl zu oder erstelle neuen User.

    Returns:
        dict: {'id': int, 'name': str}
    """
    while True:
        users = storage.list_users()

        print("\nWelcome to the Movie App")
        print("Select a user:")

        if not users:
            print("No users yet. You need to create one.")
            name = input("Enter new username: ").strip()
            if not name:
                print("Username cannot be empty.")
                continue
            return storage.get_or_create_user(name)

        
        for idx, user in enumerate(users, start=1):
            print(f"{idx}. {user['name']}")
        print(f"{len(users) + 1}. Create new user")

        choice = input("Enter choice: ").strip()

        try:
            number = int(choice)
        except ValueError:
            print("Please enter a number.")
            continue

        if 1 <= number <= len(users):
            return users[number - 1]
        elif number == len(users) + 1:
            name = input("Enter new username: ").strip()
            if not name:
                print("Username cannot be empty.")
                continue
            return storage.get_or_create_user(name)
        else:
            print("Invalid choice. Try again.")




def fetch_movie_from_omdb(title):
    """Fetch movie information from OMDb by title."""
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
    """Extract title, year, rating and poster URL from OMDb response."""
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
    """Retrieve and display all movies from the database for current user."""
    global current_user
    movies = storage.list_movies(current_user["id"])

    if not movies:
        print(f"{current_user['name']}, your movie collection is empty.")
        return

    print(f"\n{len(movies)} movies in total for {current_user['name']}")
    for title, data in movies.items():
        print(f"{title} ({data['year']}): {data['rating']}")


def command_add_movie():
    """Ask the user for a title, fetch data from OMDb, and add movie for current user."""
    global current_user
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

    try:
        storage.add_movie(title, year, rating, poster_url, current_user["id"])
    except Exception as exc:
        print(f"Error while adding movie: {exc}")


def command_delete_movie():
    """Ask the user for a movie title and delete it from the database."""
    global current_user
    title = input("Enter movie name to delete: ").strip()
    if not title:
        print("Error: Title cannot be empty.")
        return

    storage.delete_movie(title, current_user["id"])


def command_update_movie():
    """Ask the user for a movie title and update its rating."""
    global current_user
    title = input("Enter movie name to update: ").strip()
    if not title:
        print("Error: Title cannot be empty.")
        return

    try:
        rating = float(input("Enter new rating (1-10): ").strip())
    except ValueError:
        print("Invalid rating (expected a number).")
        return

    storage.update_movie(title, rating, current_user["id"])


def command_stats():
    """Calculate and print statistics about all movies for current user."""
    global current_user
    movies = storage.list_movies(current_user["id"])
    if not movies:
        print(f"{current_user['name']}, your movie collection is empty.")
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
    """Pick and print a random movie from the database for current user."""
    global current_user
    movies = storage.list_movies(current_user["id"])
    if not movies:
        print(f"{current_user['name']}, your movie collection is empty.")
        return

    title = random.choice(list(movies.keys()))
    data = movies[title]
    print(f"Random pick for {current_user['name']}: {title} ({data['year']}), {data['rating']}")


def command_search_movie():
    """Search for movies whose title contains a user provided substring."""
    global current_user
    query = input("Enter part of movie name: ").strip().lower()
    if not query:
        print("Error: Search string cannot be empty.")
        return

    movies = storage.list_movies(current_user["id"])
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
    """Display all movies sorted by rating in descending order for current user."""
    global current_user
    movies = storage.list_movies(current_user["id"])
    if not movies:
        print(f"{current_user['name']}, your movie collection is empty.")
        return

    sorted_items = sorted(
        movies.items(),
        key=lambda item: item[1]["rating"],
        reverse=True,
    )
    for title, data in sorted_items:
        print(f"{title} ({data['year']}): {data['rating']}")


def sanitize_filename(name: str) -> str:
    """Ein einfacher Sanitizer für Dateinamen."""
    cleaned = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    return cleaned.replace(" ", "_") or "user"


def command_generate_website():
    """Generate an HTML website from the template and stored movies for current user."""
    global current_user
    movies = storage.list_movies(current_user["id"])

    base_dir = Path(__file__).resolve().parent
    template_path = base_dir / "static" / "index_template.html"

    
    safe_name = sanitize_filename(current_user["name"])
    output_path = base_dir / "static" / f"{safe_name}.html"

    try:
        with open(template_path, "r", encoding="utf-8") as file:
            template = file.read()
    except FileNotFoundError:
        print(f"Error: template file not found at {template_path}")
        return

    title_text = f"{current_user['name']}'s Movie App"

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
                <div class="movie-rating">Rating: {rating}</div>
            </div>
        </li>
        """

    html_content = template.replace("__TEMPLATE_TITLE__", title_text)
    html_content = html_content.replace("__TEMPLATE_MOVIE_GRID__", movie_grid_html)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"Website for {current_user['name']} was generated successfully: {output_path.name}")




def main():
    global current_user

    
    current_user = choose_user()
    print(f"\nWelcome, {current_user['name']}")

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
        "10": None,  
    }

    while True:
        if current_user is None:
            current_user = choose_user()
            print(f"\nWelcome, {current_user['name']}")

        print_menu()
        choice = input("Choose an option (0-10): ").strip()

        if choice == "0":
            print("Goodbye")
            break

        if choice == "10":
           
            current_user = None
            continue

        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice. Please select 0-10.")


if __name__ == "__main__":
    main()
