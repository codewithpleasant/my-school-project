# ML Meal Recommender

This is a hybrid machine-learning meal recommendation system for Nigerian meals.

It uses:

- TF-IDF vectorization to convert meal ingredients into numeric features.
- Cosine similarity to compare available ingredients with meals in the dataset.
- Password-based user profiles stored in SQLite.
- Feedback learning to boost or reduce meal rankings per user over time.
- Saved profile preferences for region, dietary preference, favorite ingredients, and disliked ingredients.

## Setup

```bash
pip install -r requirements.txt
```

## Run the web app

```bash
python app.py
```

Open the local Flask URL shown in the terminal.

The first run creates `meal_recommender.db` automatically. Existing rows in
`feedback.csv` are imported into a default demo account once.

Demo login:

```text
username: demo
password: demo123
```

## Run the terminal version

```bash
python main.py
```

Enter ingredients separated by commas, for example:

```text
rice,tomatoes,pepper,onions,vegetable oil,chicken
```
