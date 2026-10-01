"""
Main triage logic for the Urgent Message Router.

The system:
1. Validates the incoming text.
2. Gets a recommendation from the machine-learning model.
3. Checks for critical safety indicators.
4. Routes low-confidence, non-critical predictions to Uncertain.
5. Creates an explainable recommendation for a human officer.

The system does not make the final decision.
"""

from functools import lru_cache
from pathlib import Path

import joblib

from safety_rules import check_safety_rules


MODEL_PATH = Path("models/urgency_model_v2.joblib")

# Non-critical predictions below this confidence level are routed
# to Uncertain for human clarification.
#
# A Critical model prediction is not lowered automatically because
# doing so could delay a potentially dangerous message.
LOW_CONFIDENCE_THRESHOLD = 0.50

MAXIMUM_MESSAGE_LENGTH = 5000


@lru_cache(maxsize=1)
def load_model():
    """
    Load the trained model once and keep it available in memory.

    The cache prevents the application from loading the same model
    file again every time a message is assessed.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run train_model.py before using triage.py."
        )

    return joblib.load(MODEL_PATH)


def validate_message(message):
    """
    Check that the incoming message is safe to process as text.
    """

    if not isinstance(message, str):
        raise TypeError("The message must be text.")

    cleaned_message = " ".join(message.split())

    if not cleaned_message:
        raise ValueError("The message cannot be empty.")

    if len(cleaned_message) > MAXIMUM_MESSAGE_LENGTH:
        raise ValueError(
            f"The message is longer than "
            f"{MAXIMUM_MESSAGE_LENGTH} characters."
        )

    return cleaned_message


def get_human_action(category, immediate_escalation):
    """
    Return the action shown to the human officer.
    """

    if immediate_escalation:
        return "Immediate human escalation required"

    actions = {
        "Critical": "Immediate human escalation required",
        "Urgent": "Priority human review required",
        "Routine": "Add to the normal human review queue",
        "Uncertain": "Human clarification and review required",
    }

    return actions.get(
        category,
        "Human review required",
    )


def triage_message(message):
    """
    Assess one fictional incoming message.

    Returns both the raw model result and the combined recommendation
    so the human officer can see how the result was produced.
    """

    cleaned_message = validate_message(message)

    model = load_model()

    # Ask the model for its predicted category.
    model_category = model.predict([cleaned_message])[0]

    # Obtain the probability assigned to every category.
    probabilities = model.predict_proba([cleaned_message])[0]

    probability_by_category = {
        category: float(probability)
        for category, probability in zip(
            model.classes_,
            probabilities,
        )
    }

    # The largest probability becomes the displayed model confidence.
    model_confidence = max(probability_by_category.values())

    low_confidence = (
        model_confidence < LOW_CONFIDENCE_THRESHOLD
    )

    # Check the same message using the explainable safety rules.
    safety_result = check_safety_rules(cleaned_message)

    safety_rule_triggered = safety_result["rule_triggered"]

    # Combine the model prediction, confidence and safety rules.
    #
    # Priority 1: A safety trigger always raises the recommendation
    # to Critical.
    #
    # Priority 2: A low-confidence non-critical prediction is routed
    # to Uncertain for human clarification.
    #
    # Priority 3: Otherwise, retain the model prediction.
    if safety_rule_triggered:
        recommended_category = "Critical"
        recommendation_source = "critical_safety_rule"

    elif low_confidence and model_category != "Critical":
        recommended_category = "Uncertain"
        recommendation_source = "low_confidence_fallback"

    else:
        recommended_category = model_category
        recommendation_source = "machine_learning_model"

    # Critical recommendations must reach a human immediately.
    immediate_escalation = (
        recommended_category == "Critical"
        or safety_rule_triggered
    )

    human_action = get_human_action(
        recommended_category,
        immediate_escalation,
    )

    # Create a plain-language explanation for the human officer.
    explanation = []

    if safety_rule_triggered:
        explanation.extend(safety_result["reasons"])
        explanation.append(
            "A safety rule raised this message for immediate review."
        )

    elif recommendation_source == "low_confidence_fallback":
        explanation.append(
            f"The text model predicted {model_category}, but its "
            f"confidence was below "
            f"{LOW_CONFIDENCE_THRESHOLD:.0%}."
        )
        explanation.append(
            "The message was routed to Uncertain for human "
            "clarification."
        )

    else:
        explanation.append(
            f"The text model recommended {model_category}."
        )

    # A low-confidence Critical prediction remains Critical, but the
    # officer is warned that the model evidence is weak.
    if (
        low_confidence
        and recommendation_source != "low_confidence_fallback"
    ):
        explanation.append(
            "The model confidence is low, so the recommendation "
            "requires careful human review."
        )

    explanation.append(
        "A human officer must make the final decision."
    )

    return {
        "message": cleaned_message,

        # Original machine-learning result
        "model_category": model_category,
        "model_confidence": model_confidence,
        "probabilities": probability_by_category,

        # Safety-layer information
        "safety_rule_triggered": safety_rule_triggered,
        "safety_reasons": safety_result["reasons"],

        # Combined recommendation shown to the officer
        "recommended_category": recommended_category,
        "recommendation_source": recommendation_source,
        "low_confidence": low_confidence,

        # Human accountability
        "immediate_escalation": immediate_escalation,
        "human_decision_required": True,
        "human_action": human_action,
        "explanation": explanation,
    }


if __name__ == "__main__":
    example_messages = [
        "A child has fallen into the water tank.",
        "Our only toilet is blocked and overflowing.",
        "Please change my postal address.",
        "Something happened and I need help.",
        "Someone is blackmailing me.",
    ]

    for example in example_messages:
        result = triage_message(example)

        print("\n" + "=" * 60)
        print(f"Message: {result['message']}")
        print(f"Raw model category: {result['model_category']}")
        print(
            f"Model confidence: "
            f"{result['model_confidence']:.2%}"
        )
        print(
            f"Safety rule triggered: "
            f"{result['safety_rule_triggered']}"
        )
        print(
            f"Recommended category: "
            f"{result['recommended_category']}"
        )
        print(
            f"Recommendation source: "
            f"{result['recommendation_source']}"
        )
        print(f"Human action: {result['human_action']}")

        print("Explanation:")

        for reason in result["explanation"]:
            print(f"- {reason}")