import random
import statistics

def print_menu():
    print("\n== Movie Database ==")
    print("1. List movies")
    print("2. Add movie")
    print("3. Delete movie")
    print("4. Update movie rating")
    print("5. Stats")
    print("6. Random movie")
    print("7. Search movie")
    print("8. Movies sorted by rating (desc)")
    print("9. Exit")

def list_movies(movies):
    print(f"\n{len(movies)} movies in total")
    for title, rating in movies.items():
        print(f"{title}: {rating}")

def add_movie(movies):
    title = input("Enter movie name: ").strip()
    if title in movies:
        print("Error: Movie already exists.")
        return
    try:
        rating = float(input("Enter rating (1-10): ").strip())
    except ValueError:
        print("Invalid rating (expected a number).")
        return
    movies[title] = rating
    print(f"Added: {title} with rating {rating}")

def delete_movie(movies):
    title = input("Enter movie name to delete: ").strip()
    if title not in movies:
        print("Error: Movie not found.")
        return
    del movies[title]
    print(f"Deleted: {title}")

def update_movie(movies):
    title = input("Enter movie name to update: ").strip()
    if title not in movies:
        print("Error: Movie not found.")
        return
    try:
        rating = float(input("Enter new rating (1-10): ").strip())
    except ValueError:
        print("Invalid rating (expected a number).")
        return
    movies[title] = rating
    print(f"Updated: {title} now has rating {rating}")

def stats(movies):
    if not movies:
        print("No movies in database.")
        return
    ratings = list(movies.values())
    avg = sum(ratings) / len(ratings)
    med = statistics.median(ratings)

    max_rating = max(ratings)
    min_rating = min(ratings)
    best = [t for t, r in movies.items() if r == max_rating]
    worst = [t for t, r in movies.items() if r == min_rating]

    print("\n== Stats ==")
    print(f"Average rating: {avg:.2f}")
    print(f"Median rating: {med:.2f}")
    print(f"Best ({max_rating}): " + ", ".join(best))
    print(f"Worst ({min_rating}): " + ", ".join(worst))

def random_movie(movies):
    if not movies:
        print("No movies in database.")
        return
    title = random.choice(list(movies.keys()))
    print(f"Random pick: {title}, {movies[title]}")

def search_movie(movies):
    q = input("Enter part of movie name: ").strip().lower()
    matches = [(t, r) for t, r in movies.items() if q in t.lower()]
    if not matches:
        print("No matches found.")
        return
    for t, r in matches:
        print(f"{t}, {r}")

def movies_sorted(movies):
    sorted_items = sorted(movies.items(), key=lambda x: x[1], reverse=True)
    for title, rating in sorted_items:
        print(f"{title}: {rating}")

def main():
    # Dictionary to store the movies and the rating
    movies = {
        "The Shawshank Redemption": 9.5,
        "Pulp Fiction": 8.8,
        "The Room": 3.6,
        "The Godfather": 9.2,
        "The Godfather: Part II": 9.0,
        "The Dark Knight": 9.0,
        "12 Angry Men": 8.9,
        "Everything Everywhere All At Once": 8.9,
        "Forrest Gump": 8.8,
        "Star Wars: Episode V": 8.7
    }

    actions = {
        "1": lambda: list_movies(movies),
        "2": lambda: add_movie(movies),
        "3": lambda: delete_movie(movies),
        "4": lambda: update_movie(movies),
        "5": lambda: stats(movies),
        "6": lambda: random_movie(movies),
        "7": lambda: search_movie(movies),
        "8": lambda: movies_sorted(movies),
    }

    while True:
        print_menu()
        choice = input("Choose an option (1-9): ").strip()
        if choice == "9":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice. Please select 1-9.")

if __name__ == "__main__":
    main()
