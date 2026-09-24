"""
Compare the machine-learning model with the combined safety system.

System A:
    TF-IDF and Logistic Regression only.

System B:
    TF-IDF and Logistic Regression plus explainable safety rules.

The combined recommendation still requires a human decision.
"""

from pathlib import Path
import json

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
)

from safety_rules import check_safety_rules


# ---------------------------------------------------------
# 1. File locations
# ---------------------------------------------------------

MODEL_PATH = Path("models/urgency_model_v2.joblib")
VALIDATION_PATH = Path("data/validation_messages.csv")
RESULTS_FOLDER = Path("results")

COMPARISON_PATH = RESULTS_FOLDER / "safety_comparison.csv"
SUMMARY_PATH = RESULTS_FOLDER / "safety_comparison_summary.json"
MATRIX_PATH = RESULTS_FOLDER / "safety_comparison_matrix.png"

RESULTS_FOLDER.mkdir(exist_ok=True)


# ---------------------------------------------------------
# 2. Load the trained model and validation dataset
# ---------------------------------------------------------

model = joblib.load(MODEL_PATH)
validation_data = pd.read_csv(VALIDATION_PATH)

messages = validation_data["message"]
expected_labels = validation_data["label"]

print(f"Validation messages: {len(validation_data)}")


# ---------------------------------------------------------
# 3. Get predictions from the machine-learning model
# ---------------------------------------------------------

model_predictions = model.predict(messages)
model_probabilities = model.predict_proba(messages)
model_confidences = model_probabilities.max(axis=1)


# ---------------------------------------------------------
# 4. Apply the safety rules to every message
# ---------------------------------------------------------

combined_predictions = []
rule_triggered_values = []
rule_reasons = []
overridden_values = []

for message, model_prediction in zip(messages, model_predictions):

    safety_result = check_safety_rules(message)

    rule_triggered = safety_result["rule_triggered"]

    # Start with the machine-learning recommendation.
    combined_prediction = model_prediction

    # If a critical safety rule is triggered, escalate the
    # recommendation to Critical for immediate human review.
    if rule_triggered:
        combined_prediction = "Critical"

    # Record whether the rule changed the model recommendation.
    overridden = (
        rule_triggered
        and model_prediction != combined_prediction
    )

    combined_predictions.append(combined_prediction)
    rule_triggered_values.append(rule_triggered)
    overridden_values.append(overridden)

    # Convert the list of reasons into readable text.
    rule_reasons.append(
        "; ".join(safety_result["reasons"])
    )


# ---------------------------------------------------------
# 5. Calculate performance before and after safety rules
# ---------------------------------------------------------

label_order = ["Critical", "Urgent", "Routine", "Uncertain"]

model_accuracy = accuracy_score(
    expected_labels,
    model_predictions,
)

combined_accuracy = accuracy_score(
    expected_labels,
    combined_predictions,
)

model_report = classification_report(
    expected_labels,
    model_predictions,
    labels=label_order,
    output_dict=True,
    zero_division=0,
)

combined_report = classification_report(
    expected_labels,
    combined_predictions,
    labels=label_order,
    output_dict=True,
    zero_division=0,
)

model_critical_recall = model_report["Critical"]["recall"]
combined_critical_recall = combined_report["Critical"]["recall"]


# ---------------------------------------------------------
# 6. Print the comparison
# ---------------------------------------------------------

print("\nMODEL ONLY")
print(f"Accuracy: {model_accuracy:.2%}")
print(f"Critical recall: {model_critical_recall:.2%}")

print("\nMODEL PLUS SAFETY RULES")
print(f"Accuracy: {combined_accuracy:.2%}")
print(f"Critical recall: {combined_critical_recall:.2%}")

rules_triggered_count = sum(rule_triggered_values)
overridden_count = sum(overridden_values)

print(f"\nMessages triggering safety rules: {rules_triggered_count}")
print(f"Model recommendations overridden: {overridden_count}")


# ---------------------------------------------------------
# 7. Save a row-by-row comparison
# ---------------------------------------------------------

comparison = pd.DataFrame(
    {
        "message_id": validation_data["message_id"],
        "message": messages,
        "expected_label": expected_labels,
        "model_prediction": model_predictions,
        "model_confidence": model_confidences,
        "safety_rule_triggered": rule_triggered_values,
        "safety_reason": rule_reasons,
        "combined_recommendation": combined_predictions,
        "recommendation_overridden": overridden_values,
    }
)

comparison["model_correct"] = (
    comparison["expected_label"]
    == comparison["model_prediction"]
)

comparison["combined_correct"] = (
    comparison["expected_label"]
    == comparison["combined_recommendation"]
)

comparison.to_csv(COMPARISON_PATH, index=False)

print(f"\nSaved detailed comparison to: {COMPARISON_PATH}")


# ---------------------------------------------------------
# 8. Save the summary as JSON
# ---------------------------------------------------------

summary = {
    "validation_messages": len(validation_data),
    "model_only": {
        "accuracy": model_accuracy,
        "critical_recall": model_critical_recall,
    },
    "model_plus_safety_rules": {
        "accuracy": combined_accuracy,
        "critical_recall": combined_critical_recall,
    },
    "safety_rules_triggered": rules_triggered_count,
    "model_recommendations_overridden": overridden_count,
}

with open(SUMMARY_PATH, "w", encoding="utf-8") as summary_file:
    json.dump(summary, summary_file, indent=4)

print(f"Saved summary to: {SUMMARY_PATH}")


# ---------------------------------------------------------
# 9. Create two confusion matrices for comparison
# ---------------------------------------------------------

figure, axes = plt.subplots(
    nrows=1,
    ncols=2,
    figsize=(13, 5),
)

ConfusionMatrixDisplay.from_predictions(
    expected_labels,
    model_predictions,
    labels=label_order,
    cmap="Blues",
    values_format="d",
    ax=axes[0],
    colorbar=False,
)

axes[0].set_title("Model Only")

ConfusionMatrixDisplay.from_predictions(
    expected_labels,
    combined_predictions,
    labels=label_order,
    cmap="Greens",
    values_format="d",
    ax=axes[1],
    colorbar=False,
)

axes[1].set_title("Model Plus Safety Rules")

figure.suptitle(
    "Urgent Message Router: Safety-Layer Comparison"
)

plt.tight_layout()
plt.savefig(MATRIX_PATH, dpi=300)
plt.close()

print(f"Saved comparison matrix to: {MATRIX_PATH}")


# ---------------------------------------------------------
# 10. Important interpretation
# ---------------------------------------------------------

print(
    "\nImportant: A safety-rule trigger does not make the final "
    "decision. It escalates the message for immediate human review."
)