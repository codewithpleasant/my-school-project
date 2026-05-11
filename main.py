import pandas as pd

# Load dataset
data = pd.read_csv("data_set.csv")

# Ingredient substitutes
substitutes = {
    "fresh pepper": "grinded pepper",
    "beef": "chicken",
    "palm oil": "vegetable oil",
    "crayfish": "fish seasoning"
}

# Ingredients to ignore during matching
ignore_ingredients = ["water", "salt", "oil", "seasoning"]

# Get user input
user_input = input("Enter available ingredients (comma separated): ").lower()

# Convert input into a clean list
available_ingredients = [
    item.strip() for item in user_input.split(",")
]

# Recommendation function


def recommend_meals():

    recommendations = []

    # Loop through all meals
    for index, row in data.iterrows():

        # Get meal name
        meal = row["Meal_name"]

        # Convert recipe ingredients into list
        recipe_ingredients = [
            item.strip().lower()
            for item in row["Ingredients"].split(",")
        ]

        # Remove ignored ingredients
        valid_ingredients = [
            ing for ing in recipe_ingredients
            if ing not in ignore_ingredients
        ]

        matched = 0
        substitutions_used = []

        # Check ingredient matches
        for ingredient in valid_ingredients:

            # Exact match
            if ingredient in available_ingredients:
                matched += 1

            # Substitute match
            elif ingredient in substitutes:

                if substitutes[ingredient] in available_ingredients:
                    matched += 1

                    substitutions_used.append(
                        f"{ingredient} → {substitutes[ingredient]}"
                    )

        # Avoid division by zero
        if len(valid_ingredients) == 0:
            continue

        # Calculate match score
        score = matched / len(valid_ingredients)

        # Keep only strong matches
        if score >= 0.3:
            recommendations.append(
                (meal, score, substitutions_used)
            )

    # Sort recommendations by highest score
    recommendations.sort(
        key=lambda x: x[1],
        reverse=True
    )

    # Display results
    print("\nRecommended Meals:\n")

    if len(recommendations) == 0:
        print("No suitable meals found.")

    else:
        for i, rec in enumerate(recommendations[:5], start=1):

            print(
                f"{i}. {rec[0]} "
                f"(Match: {round(rec[1] * 100)}%)"
            )

            # Show substitutes if used
            if rec[2]:

                print("   Substitutes used:")

                for sub in rec[2]:
                    print("   -", sub)


# Run the system
recommend_meals()
