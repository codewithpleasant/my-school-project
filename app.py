from flask import Flask, flash, redirect, render_template, request, url_for

from recommender import MealRecommender


app = Flask(__name__)
app.config["SECRET_KEY"] = "meal-recommender-dev-key"

recommender = MealRecommender()


@app.route("/", methods=["GET", "POST"])
def index():
    ingredients = ""
    recommendations = []

    if request.method == "POST":
        ingredients = request.form.get("ingredients", "").strip()
        recommendations = recommender.recommend(ingredients)

        if ingredients and not recommendations:
            flash("No close meal match was found for those ingredients.", "warning")

    return render_template(
        "index.html",
        ingredients=ingredients,
        recommendations=recommendations,
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    ingredients = request.form.get("ingredients", "").strip()
    meal = request.form.get("meal", "").strip()
    region = request.form.get("region", "").strip()
    feedback_type = request.form.get("feedback_type", "").strip()

    recommender.save_feedback(
        ingredients_text=ingredients,
        meal=meal,
        feedback_type=feedback_type,
        region=region,
    )

    flash("Feedback saved. The model will use it in future rankings.", "success")
    return redirect(url_for("index_with_ingredients", ingredients=ingredients))


@app.route("/search")
def index_with_ingredients():
    ingredients = request.args.get("ingredients", "").strip()

    return render_template(
        "index.html",
        ingredients=ingredients,
        recommendations=recommender.recommend(ingredients) if ingredients else [],
    )


if __name__ == "__main__":
    app.run(debug=True)
