# ML Meal Recommender

This is a hybrid machine-learning meal recommendation system for Nigerian meals.

It uses:

- TF-IDF vectorization to convert meal ingredients into numeric features.
- Cosine similarity to compare available ingredients with meals in the dataset.
- Feedback learning to boost or reduce meal rankings over time.

## Setup

```bash
pip install -r requirements.txt
```

## Run the web app

```bash
python app.py
```

Open the local Flask URL shown in the terminal.

## Run the terminal version

```bash
python main.py
```

Enter ingredients separated by commas, for example:

```text
rice,tomatoes,pepper,onions,vegetable oil,chicken
```
