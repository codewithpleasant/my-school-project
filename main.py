from recommender import MealRecommender


def main():
    recommender = MealRecommender()
    user_input = input("Enter available ingredients (comma separated): ")
    recommendations = recommender.recommend(user_input)

    print("\nRecommended Meals:\n")

    if not recommendations:
        print("No suitable meals found.")
        return

    for index, rec in enumerate(recommendations, start=1):
        print(
            f"{index}. {rec['meal']} "
            f"(Match: {rec['match_percent']}%, "
            f"Region: {rec['region']})"
        )

        if rec["matched_ingredients"]:
            print("   Matched ingredients:", ", ".join(rec["matched_ingredients"]))

        if rec["feedback_adjustment"] != 0:
            print(f"   Learning adjustment: {rec['feedback_adjustment']:+.1f}%")


if __name__ == "__main__":
    main()
