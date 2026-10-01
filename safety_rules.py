"""
Safety rules for the Urgent Message Router.

These rules look for clear danger indicators that the statistical
model might miss. A triggered rule escalates the message to a human.

The rules do not make the final decision.
"""

import re


# Each safety concern contains:
# 1. A name that can be shown to the officer.
# 2. Regular-expression patterns describing dangerous situations.
CRITICAL_RULES = {
    "person may be unconscious or unresponsive": [
    (
        r"\b(person|child|baby|infant|man|woman|mother|father|"
        r"son|daughter|resident|pedestrian|worker|passenger|someone|"
        r"he|she|they|i)\b.{0,50}"
        r"\b(unconscious|unresponsive|motionless|not moving|"
        r"not responding|not waking up|will not wake up|"
        r"fainted|fainting|passed out|passing out|"
        r"going to faint|gonna faint|about to faint)\b"
    ),
    r"\b(unconscious|unresponsive)\s+(person|child|resident|worker)\b",
    r"\b(gonna|going to|about to)\s+(faint|pass out|collapse)\b",
],
  "severe breathing difficulty or choking": [
    (
        r"\b(not breathing|cannot breathe|can't breathe|"
        r"unable to breathe|barely breathing)\b"
    ),
    (
        r"\b(breathing problem|breathing problems|"
        r"difficulty breathing|trouble breathing|"
        r"hard to breathe|shortness of breath)\b"
    ),
    r"\bbreathing is (hard|difficult|getting worse)\b",
    r"\b(cannot|can't)\s+catch\s+(my|his|her|their)?\s*breath\b",
    r"\b(gasping for air|choking|choked)\b",
    r"\bstruggling to breathe\b",
    r"\blips (look |are )?blue\b",
],

   "active fire, explosion or dangerous smoke": [
    r"\b(on fire|burning|flames are|flames coming|fire is spreading)\b",
    (
        r"\bfire\b.{0,30}"
        r"\b(house|home|building|unit|apartment|room|kitchen|property)\b"
    ),
    (
        r"\b(house|home|building|unit|apartment|room|kitchen)\b"
        r".{0,30}\b(fire|burning|flames|filled with smoke)\b"
    ),
    r"\b(thick black smoke|smoke is filling|smoke filling)\b",
    r"\b(exploded|explosion)\b",
    r"\bfire\b.{0,40}\b(trapped|cannot get out|can't get out)\b",
],

    "active violence or weapon threat": [
        r"\b(stabbed|stabbing|shot|shooting)\b",
        r"\b(attacking|assaulting|chasing)\b.{0,40}\b(now|knife|gun|machete)\b",
        r"\b(knife|gun|machete|weapon)\b.{0,40}\b(threatening|coming here|fired)\b",
        r"\btrying to break in\b",
        r"\bforcing the (front|back)?\s*door open\b",
    ],

    "drowning or person trapped": [
        r"\b(fell|fallen) into the (pool|river|water tank)\b",
        r"\b(caught in the current|swept away)\b",
        r"\b(trapped under|trapped inside|people are trapped|person is trapped)\b",
        r"\bboat has overturned\b",
    ],

    "poisoning or overdose": [
        r"\b(swallowed|drank|took)\b.{0,40}\b(cleaning liquid|poison|tablets)\b",
        r"\b(overdose|too many tablets|too many pills)\b",
    ],

    "immediate self-harm concern": [
        r"\b(will|going to|plans? to)\b.{0,30}\b(harm|hurt|kill)\s+(myself|himself|herself|themselves)\b",
        r"\b(suicide|suicidal)\b",
        r"\bsaying (he|she|they) will jump\b",
        r"\bon the roof\b.{0,30}\bjump\b",
    ],

    "serious electrical or gas hazard": [
        r"\b(live wire|fallen power line)\b",
        r"\bpower line\b.{0,30}\b(sparking|sparks)\b",
        r"\belectrical\b.{0,30}\b(exploded|smoke|sparking)\b",
        r"\bgas\b.{0,40}\b(hissing|open flame|dizzy|dizziness)\b",
        r"\bstrong gas smell\b",
    ],

    "severe structural danger": [
        r"\b(ceiling|roof|wall|balcony|veranda)\b.{0,30}\b(collapsing|collapsed)\b",
        r"\bretaining wall\b.{0,30}\bcollapsing\b",
    ],
        "fall from height or major traumatic injury": [
        (
            r"\b(i|person|child|baby|girl|boy|man|woman|someone|"
            r"worker|resident|he|she|they)\b.{0,40}"
            r"\b(fell|fallen|fall|jumped)\b.{0,30}"
            r"\b(from|off)\b.{0,25}"
            r"\b(first|second|third|fourth|1st|2nd|3rd|4th|"
            r"floor|storey|story|roof|balcony|ladder|scaffold|height)\b"
        ),
        r"\b(hit|struck|run over)\b.{0,25}\b(car|truck|bus|vehicle|motorbike)\b",
        r"\b(heavy|severe|uncontrolled)\b.{0,20}\b(bleeding|blood loss)\b",
        r"\b(head injury|crushed|severed limb|amputation)\b",
    ],
}


def check_safety_rules(message):
    """
    Check one message for critical safety indicators.

    Parameters
    ----------
    message : str
        The incoming message written by the person.

    Returns
    -------
    dict
        Information about triggered rules and human escalation.
    """

    # Convert the message to lowercase so capitalisation does not matter.
    normalised_message = str(message).lower().strip()

    triggered_reasons = []

    # Check every pattern inside every safety concern.
    for reason, patterns in CRITICAL_RULES.items():
        for pattern in patterns:
            if re.search(pattern, normalised_message):
                triggered_reasons.append(reason)

                # Stop checking other patterns for the same reason.
                break

    # Remove repeated reasons while retaining their original order.
    triggered_reasons = list(dict.fromkeys(triggered_reasons))

    rule_triggered = len(triggered_reasons) > 0

    return {
        "rule_triggered": rule_triggered,

        # This is a recommendation, not the human's final decision.
        "recommended_category": "Critical" if rule_triggered else None,

        # Any safety flag must be reviewed by a human immediately.
        "human_review_required": rule_triggered,

        # These reasons explain why the rule was triggered.
        "reasons": triggered_reasons,
    }


# This section runs only when safety_rules.py is executed directly.
# It provides a small test without affecting other Python files.
if __name__ == "__main__":
    example_messages = [
        "A child has fallen into the water tank.",
        "Someone has been stabbed outside the hall.",
        "My baby cannot breathe.",
        "Please update the spelling of my name.",
        "There is a crack near the roof.",
    ]

    for example in example_messages:
        result = check_safety_rules(example)

        print("\nMessage:")
        print(example)

        print("Rule triggered:")
        print(result["rule_triggered"])

        print("Recommended category:")
        print(result["recommended_category"])

        print("Reasons:")
        print(result["reasons"])