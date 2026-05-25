from pathlib import Path
import re

import pandas as pd


# Load dataset from the same folder as this file.
DATA_FILE = Path(__file__).with_name("data_set.csv")
data = pd.read_csv(DATA_FILE)

# Ingredient substitutes
substitutes = {
    "fresh pepper": ["grinded pepper", "ground pepper", "pepper"],
    "grinded pepper": ["fresh pepper", "ground pepper", "pepper"],
    "beef": ["chicken", "meat"],
    "chicken": ["beef", "meat"],
    "palm oil": ["vegetable oil", "groundnut oil"],
    "vegetable oil": ["palm oil", "groundnut oil"],
    "crayfish": ["fish seasoning", "fish"],
    "fish seasoning": ["crayfish", "fish"],
}

# Ingredients that should not control the recommendation strongly.
ignore_ingredients = {
    "water",
    "salt",
    "oil",
    "seasoning",
    "seasoning cube",
    "seasoning cubes",
    "curry powder",
    "thyme",
    "stock",
    "meat stock",
    "chicken stock",
}

word_replacements = {
    "peppers": "pepper",
    "eggs": "egg",
    "plantains": "plantain",
    "tomatoes": "tomato",
    "vegetables": "vegetable",
    "onions": "onion",
    "cubes": "cube",
}


def normalize_ingredient(ingredient):
    ingredient = ingredient.lower().strip()
    ingredient = re.sub(r"\([^)]*\)", "", ingredient)
    ingredient = ingredient.replace("&", " and ")
    ingredient = ingredient.replace("/", " or ")
    ingredient = re.sub(r"[^a-z0-9\s]", " ", ingredient)
    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    words = [
        word_replacements.get(word, word)
        for word in ingredient.split()
    ]

    return " ".join(words)


def split_recipe_ingredient(ingredient):
    ingredient = normalize_ingredient(ingredient)

    if not ingredient:
        return []

    if "optional" in ingredient or "for serving" in ingredient or ingredient == "etc":
        return []

    if ingredient == "vegetable or palm oil":
        ingredient = "vegetable oil or palm oil"

    ingredient = ingredient.replace(" of choice", "")

    parts = re.split(r"\s+(?:or|and|like|with)\s+", ingredient)

    clean_parts = []
    for part in parts:
        part = part.strip()

        if not part or part.startswith("other "):
            continue

        clean_parts.append(part)

    return [clean_parts]


def ingredient_matches(recipe_ingredient, available_ingredients):
    if recipe_ingredient in available_ingredients:
        return True, None

    recipe_words = set(recipe_ingredient.split())

    for available in available_ingredients:
        available_words = set(available.split())

        if len(recipe_words) > 1 and available_words.issubset(recipe_words):
            return True, None

    for substitute in substitutes.get(recipe_ingredient, []):
        substitute = normalize_ingredient(substitute)

        if substitute in available_ingredients:
            return True, f"{recipe_ingredient} -> {substitute}"

    return False, None


# Get user input
user_input = input("Enter available ingredients (comma separated): ")

# Convert input into a clean list
available_ingredients = [
    normalized
    for item in user_input.split(",")
    if (normalized := normalize_ingredient(item))
]


def recommend_meals():
    recommendations = []

    # Loop through all meals
    for index, row in data.iterrows():
        meal = row["Meal_name"]

        # Convert recipe ingredients into normalized ingredient options.
        recipe_requirements = [
            requirement
            for item in row["Ingredients"].split(",")
            for requirement in split_recipe_ingredient(item)
        ]

        valid_ingredients = [
            requirement for requirement in recipe_requirements
            if any(option not in ignore_ingredients for option in requirement)
        ]

        matched = 0
        substitutions_used = []

        for ingredient_options in valid_ingredients:
            is_match = False
            substitute_text = None

            for ingredient in ingredient_options:
                if ingredient in ignore_ingredients:
                    continue

                is_match, substitute_text = ingredient_matches(
                    ingredient,
                    available_ingredients
                )

                if is_match:
                    break

            if is_match:
                matched += 1

                if substitute_text:
                    substitutions_used.append(substitute_text)

        if len(valid_ingredients) == 0:
            continue

        score = matched / len(valid_ingredients)

        if score >= 0.25:
            recommendations.append(
                (meal, score, matched, substitutions_used)
            )

    # Prefer the highest match percentage, then ingredient count for ties.
    recommendations.sort(
        key=lambda x: (x[1], x[2]),
        reverse=True
    )

    print("\nRecommended Meals:\n")

    if len(recommendations) == 0:
        print("No suitable meals found.")
        return

    for i, rec in enumerate(recommendations[:5], start=1):
        print(
            f"{i}. {rec[0]} "
            f"(Match: {round(rec[1] * 100)}%, "
            f"Ingredients matched: {rec[2]})"
        )

        if rec[3]:
            print("   Substitutes used:")

            for sub in rec[3]:
                print("   -", sub)


# Run the system
recommend_meals()
