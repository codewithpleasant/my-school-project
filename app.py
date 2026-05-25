from functools import wraps
import os

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database
from recommender import MealRecommender


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "MEAL_RECOMMENDER_SECRET_KEY",
    "meal-recommender-dev-key",
)

database.init_database()
recommender = MealRecommender()


def current_user():
    return database.get_user_by_id(session.get("user_id"))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user() is None:
            flash("Log in first so recommendations can use your profile.", "warning")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user = current_user()
    ingredients = ""
    recommendations = []

    if request.method == "POST":
        ingredients = request.form.get("ingredients", "").strip()
        recommendations = recommender.recommend(ingredients, user=user)

        if ingredients and not recommendations:
            flash("No close meal match was found for those ingredients.", "warning")

    return render_template(
        "index.html",
        ingredients=ingredients,
        recommendations=recommendations,
    )


@app.route("/search")
@login_required
def index_with_ingredients():
    user = current_user()
    ingredients = request.args.get("ingredients", "").strip()

    return render_template(
        "index.html",
        ingredients=ingredients,
        recommendations=(
            recommender.recommend(ingredients, user=user)
            if ingredients
            else []
        ),
    )


@app.route("/feedback", methods=["POST"])
@login_required
def feedback():
    user = current_user()
    ingredients = request.form.get("ingredients", "").strip()
    meal = request.form.get("meal", "").strip()
    region = request.form.get("region", "").strip()
    feedback_type = request.form.get("feedback_type", "").strip()

    recommender.save_feedback(
        user_id=user["id"],
        ingredients_text=ingredients,
        meal=meal,
        feedback_type=feedback_type,
        region=region,
    )

    flash("Feedback saved to your profile.", "success")
    return redirect(url_for("index_with_ingredients", ingredients=ingredients))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username and password are required.", "warning")
        elif password != confirm_password:
            flash("Passwords do not match.", "warning")
        else:
            user = database.create_user(
                username=username,
                password=password,
                full_name=request.form.get("full_name", ""),
                region=request.form.get("region", ""),
                dietary_preference=request.form.get("dietary_preference", ""),
                favorite_ingredients=request.form.get("favorite_ingredients", ""),
                disliked_ingredients=request.form.get("disliked_ingredients", ""),
            )

            if user is None:
                flash("That username is already taken.", "warning")
            else:
                session["user_id"] = user["id"]
                flash("Account created. Your recommendations are now personalized.", "success")
                return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = database.authenticate_user(username, password)

        if user:
            session["user_id"] = user["id"]
            flash("Welcome back. Your profile is active.", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password.", "warning")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()

    if request.method == "POST":
        database.update_user_profile(
            user_id=user["id"],
            full_name=request.form.get("full_name", ""),
            region=request.form.get("region", ""),
            dietary_preference=request.form.get("dietary_preference", ""),
            favorite_ingredients=request.form.get("favorite_ingredients", ""),
            disliked_ingredients=request.form.get("disliked_ingredients", ""),
        )
        flash("Profile preferences saved.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


if __name__ == "__main__":
    app.run(debug=True)
