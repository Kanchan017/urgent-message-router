"""
Train and evaluate the Urgent Message Router.

The model learns from training_messages.csv.
It is evaluated using validation_messages.csv.
Only the message text is used as the model input.
"""

from pathlib import Path
import json

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
)
from sklearn.pipeline import Pipeline


# ---------------------------------------------------------
# 1. File locations
# ---------------------------------------------------------

TRAINING_PATH = Path("data/training_messages.csv")
VALIDATION_PATH = Path("data/validation_messages.csv")

MODEL_FOLDER = Path("models")
RESULTS_FOLDER = Path("results")

MODEL_PATH = MODEL_FOLDER / "urgency_model_v2.joblib"
REPORT_PATH = RESULTS_FOLDER / "v2_classification_report.json"
PREDICTIONS_PATH = RESULTS_FOLDER / "v2_validation_predictions.csv"
MATRIX_PATH = RESULTS_FOLDER / "v2_confusion_matrix.png"


# ---------------------------------------------------------
# 2. Create output folders if they do not exist
# ---------------------------------------------------------

MODEL_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)


# ---------------------------------------------------------
# 3. Load the datasets
# ---------------------------------------------------------

training_data = pd.read_csv(TRAINING_PATH)
validation_data = pd.read_csv(VALIDATION_PATH)

print(f"Training messages: {len(training_data)}")
print(f"Validation messages: {len(validation_data)}")


# ---------------------------------------------------------
# 4. Select the model input and correct answers
# ---------------------------------------------------------

# X contains the message text read by the model.
X_train = training_data["message"]
X_validation = validation_data["message"]

# y contains the correct human-assigned category.
y_train = training_data["label"]
y_validation = validation_data["label"]


# ---------------------------------------------------------
# 5. Build the machine-learning pipeline
# ---------------------------------------------------------

model = Pipeline(
    steps=[
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
            ),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            ),
        ),
    ]
)


# ---------------------------------------------------------
# 6. Train the model
# ---------------------------------------------------------

print("\nTraining the model...")
model.fit(X_train, y_train)
print("Model training completed.")


# ---------------------------------------------------------
# 7. Predict the validation messages
# ---------------------------------------------------------

predicted_labels = model.predict(X_validation)

# predict_proba gives the probability assigned to every category.
probabilities = model.predict_proba(X_validation)

# Keep the largest probability as the model's confidence.
confidence_scores = probabilities.max(axis=1)


# ---------------------------------------------------------
# 8. Measure model performance
# ---------------------------------------------------------

label_order = ["Critical", "Urgent", "Routine", "Uncertain"]

accuracy = accuracy_score(y_validation, predicted_labels)

print(f"\nValidation accuracy: {accuracy:.2%}")

print("\nClassification report:")
print(
    classification_report(
        y_validation,
        predicted_labels,
        labels=label_order,
        zero_division=0,
    )
)


# ---------------------------------------------------------
# 9. Save the trained model
# ---------------------------------------------------------

joblib.dump(model, MODEL_PATH)
print(f"Saved model to: {MODEL_PATH}")


# ---------------------------------------------------------
# 10. Save the classification report
# ---------------------------------------------------------

report = classification_report(
    y_validation,
    predicted_labels,
    labels=label_order,
    output_dict=True,
    zero_division=0,
)

report["validation_accuracy"] = accuracy

with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
    json.dump(report, report_file, indent=4)

print(f"Saved classification report to: {REPORT_PATH}")


# ---------------------------------------------------------
# 11. Save every validation prediction
# ---------------------------------------------------------

prediction_results = pd.DataFrame(
    {
        "message_id": validation_data["message_id"],
        "message": X_validation,
        "expected_label": y_validation,
        "predicted_label": predicted_labels,
        "confidence": confidence_scores,
    }
)

prediction_results["correct"] = (
    prediction_results["expected_label"]
    == prediction_results["predicted_label"]
)

prediction_results.to_csv(PREDICTIONS_PATH, index=False)

print(f"Saved predictions to: {PREDICTIONS_PATH}")


# ---------------------------------------------------------
# 12. Create and save the confusion matrix
# ---------------------------------------------------------

ConfusionMatrixDisplay.from_predictions(
    y_validation,
    predicted_labels,
    labels=label_order,
    cmap="Blues",
    values_format="d",
)

plt.title("Urgent Message Router – Validation Confusion Matrix")
plt.tight_layout()
plt.savefig(MATRIX_PATH, dpi=300)
plt.close()

print(f"Saved confusion matrix to: {MATRIX_PATH}")


# ---------------------------------------------------------
# 13. Display incorrect predictions
# ---------------------------------------------------------

incorrect_predictions = prediction_results[
    prediction_results["correct"] == False
]

print(f"\nIncorrect predictions: {len(incorrect_predictions)}")

if len(incorrect_predictions) > 0:
    print(
        incorrect_predictions[
            [
                "message",
                "expected_label",
                "predicted_label",
                "confidence",
            ]
        ].to_string(index=False)
    )


# ---------------------------------------------------------
# 14. Show the safety-critical recall result
# ---------------------------------------------------------

critical_recall = report["Critical"]["recall"]

print(f"\nCritical recall: {critical_recall:.2%}")
print(
    "Critical recall measures how many genuinely Critical "
    "messages the model successfully identified."
)

print(
    "\nImportant: This model provides a recommendation only. "
    "A human officer must make the final decision."
)