from datetime import datetime
from pathlib import Path
import csv
import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data_set.csv"
FEEDBACK_FILE = BASE_DIR / "feedback.csv"


IGNORE_INGREDIENTS = {
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

WORD_REPLACEMENTS = {
    "peppers": "pepper",
    "eggs": "egg",
    "plantains": "plantain",
    "tomatoes": "tomato",
    "vegetables": "vegetable",
    "onions": "onion",
    "cubes": "cube",
}

SUBSTITUTES = {
    "fresh pepper": ["grinded pepper", "ground pepper", "pepper"],
    "grinded pepper": ["fresh pepper", "ground pepper", "pepper"],
    "beef": ["chicken", "meat"],
    "chicken": ["beef", "meat"],
    "palm oil": ["vegetable oil", "groundnut oil"],
    "vegetable oil": ["palm oil", "groundnut oil"],
    "crayfish": ["fish seasoning", "fish"],
    "fish seasoning": ["crayfish", "fish"],
}

FEEDBACK_COLUMNS = [
    "timestamp",
    "entered_ingredients",
    "recommended_meal",
    "feedback_type",
    "region",
]

FEEDBACK_WEIGHTS = {
    "like": 0.03,
    "cooked": 0.05,
    "not_suitable": -0.06,
}


def normalize_ingredient(ingredient):
    ingredient = str(ingredient).lower().strip()
    ingredient = re.sub(r"\([^)]*\)", "", ingredient)
    ingredient = ingredient.replace("&", " and ")
    ingredient = ingredient.replace("/", " or ")
    ingredient = re.sub(r"[^a-z0-9\s]", " ", ingredient)
    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    words = [
        WORD_REPLACEMENTS.get(word, word)
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

    return clean_parts


def normalize_user_ingredients(ingredients_text):
    return [
        normalized
        for item in str(ingredients_text).split(",")
        if (normalized := normalize_ingredient(item))
    ]


def expand_with_substitutes(ingredients):
    expanded = set(ingredients)

    for ingredient in ingredients:
        for substitute in SUBSTITUTES.get(ingredient, []):
            expanded.add(normalize_ingredient(substitute))

    return sorted(expanded)


def build_training_text(row):
    ingredients = []

    for item in str(row["Ingredients"]).split(","):
        ingredients.extend(split_recipe_ingredient(item))

    useful_ingredients = [
        ingredient for ingredient in ingredients
        if ingredient not in IGNORE_INGREDIENTS
    ]

    return " ".join(
        [
            normalize_ingredient(row["Meal_name"]),
            normalize_ingredient(row.get("Region", "")),
            " ".join(useful_ingredients),
        ]
    )


def ensure_feedback_file():
    if FEEDBACK_FILE.exists():
        return

    with FEEDBACK_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FEEDBACK_COLUMNS)
        writer.writeheader()


class MealRecommender:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = Path(data_file)
        self.data = pd.read_csv(self.data_file).fillna("")
        self.data["training_text"] = self.data.apply(build_training_text, axis=1)
        self.vectorizer = TfidfVectorizer()
        self.meal_vectors = self.vectorizer.fit_transform(self.data["training_text"])
        ensure_feedback_file()

    def recommend(self, ingredients_text, top_n=5):
        user_ingredients = normalize_user_ingredients(ingredients_text)

        if not user_ingredients:
            return []

        expanded_ingredients = expand_with_substitutes(user_ingredients)
        user_text = " ".join(expanded_ingredients)
        user_vector = self.vectorizer.transform([user_text])
        similarities = cosine_similarity(user_vector, self.meal_vectors).flatten()
        feedback_scores = self._feedback_scores()

        recommendations = []
        for index, row in self.data.iterrows():
            meal = row["Meal_name"]
            base_score = float(similarities[index])
            feedback_adjustment = feedback_scores.get(meal, 0.0)
            final_score = max(0.0, min(1.0, base_score + feedback_adjustment))

            if final_score <= 0:
                continue

            matched_ingredients = self._matched_ingredients(row, expanded_ingredients)

            recommendations.append(
                {
                    "meal": meal,
                    "region": row["Region"] or "Not specified",
                    "score": final_score,
                    "base_score": base_score,
                    "match_percent": round(final_score * 100),
                    "base_match_percent": round(base_score * 100),
                    "feedback_adjustment": round(feedback_adjustment * 100, 1),
                    "matched_ingredients": matched_ingredients,
                }
            )

        recommendations.sort(
            key=lambda rec: (rec["score"], len(rec["matched_ingredients"])),
            reverse=True,
        )

        return recommendations[:top_n]

    def save_feedback(self, ingredients_text, meal, feedback_type, region):
        if feedback_type not in FEEDBACK_WEIGHTS:
            raise ValueError("Invalid feedback type.")

        ensure_feedback_file()

        with FEEDBACK_FILE.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FEEDBACK_COLUMNS)
            writer.writerow(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "entered_ingredients": ingredients_text,
                    "recommended_meal": meal,
                    "feedback_type": feedback_type,
                    "region": region,
                }
            )

    def _feedback_scores(self):
        ensure_feedback_file()
        feedback = pd.read_csv(FEEDBACK_FILE).fillna("")

        if feedback.empty:
            return {}

        scores = {}
        for meal, rows in feedback.groupby("recommended_meal"):
            score = 0.0

            for feedback_type in rows["feedback_type"]:
                score += FEEDBACK_WEIGHTS.get(feedback_type, 0.0)

            scores[meal] = max(-0.18, min(0.18, score))

        return scores

    def _matched_ingredients(self, row, expanded_ingredients):
        matched = []

        for item in str(row["Ingredients"]).split(","):
            options = split_recipe_ingredient(item)

            if not options:
                continue

            for option in options:
                if option in IGNORE_INGREDIENTS:
                    continue

                if option in expanded_ingredients:
                    matched.append(option)
                    break

                option_words = set(option.split())
                if len(option_words) > 1:
                    for ingredient in expanded_ingredients:
                        ingredient_words = set(ingredient.split())

                        if ingredient_words and ingredient_words.issubset(option_words):
                            matched.append(option)
                            break

        return sorted(set(matched))
