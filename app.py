import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from triage import triage_message


# =========================================================
# 1. PAGE SETTINGS
# =========================================================
st.set_page_config(
    page_title="PriorityLink | Urgent Message Router",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. CONSTANTS
# =========================================================
CATEGORIES = ["Critical", "Urgent", "Routine", "Uncertain"]

AUDIT_LOG_PATH = Path("results/human_decision_log.csv")

CATEGORY_STYLES = {
    "Critical": {
        "icon": "🚨",
        "css_class": "critical",
        "title": "Immediate escalation",
        "route": "Emergency human-review queue",
        "description": (
            "The message may describe an immediate threat to life, "
            "safety or property."
        ),
    },
    "Urgent": {
        "icon": "⚠️",
        "css_class": "urgent",
        "title": "Priority review",
        "route": "Priority human-review queue",
        "description": (
            "The message requires prompt attention from a human officer."
        ),
    },
    "Routine": {
        "icon": "✓",
        "css_class": "routine",
        "title": "Standard processing",
        "route": "Normal human-review queue",
        "description": (
            "No explicit immediate danger was identified, but a human "
            "still makes the final decision."
        ),
    },
    "Uncertain": {
        "icon": "?",
        "css_class": "uncertain",
        "title": "Clarification required",
        "route": "Human clarification queue",
        "description": (
            "The information is insufficient or conflicting. "
            "Uncertain does not mean safe or low priority."
        ),
    },
}


# =========================================================
# 3. CUSTOM USER-INTERFACE DESIGN
# =========================================================
st.markdown(
    """
    <style>
        /* Main application background */
        .stApp {
            background:
                radial-gradient(
                    circle at 90% 5%,
                    rgba(37, 99, 235, 0.12),
                    transparent 25%
                ),
                radial-gradient(
                    circle at 10% 90%,
                    rgba(14, 165, 233, 0.08),
                    transparent 25%
                ),
                #07101f;
        }

        /* Main page width */
        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #091426;
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        /* Main hero section */
        .hero {
            padding: 2rem;
            border-radius: 24px;
            background:
                linear-gradient(
                    120deg,
                    rgba(30, 64, 175, 0.34),
                    rgba(8, 145, 178, 0.17)
                );
            border: 1px solid rgba(96, 165, 250, 0.25);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
            margin-bottom: 1.5rem;
        }

        .brand-line {
            color: #7dd3fc;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }

        .hero h1 {
            color: #f8fafc;
            font-size: 2.7rem;
            line-height: 1.1;
            margin: 0;
        }

        .hero p {
            color: #cbd5e1;
            font-size: 1.05rem;
            max-width: 780px;
            margin-top: 0.8rem;
            margin-bottom: 0;
        }

        /* Small statistics */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.8rem;
            margin-top: 1.5rem;
        }

        .stat-card {
            padding: 1rem;
            background: rgba(15, 23, 42, 0.63);
            border: 1px solid rgba(148, 163, 184, 0.17);
            border-radius: 15px;
        }

        .stat-value {
            color: #f8fafc;
            font-size: 1.45rem;
            font-weight: 800;
        }

        .stat-label {
            color: #94a3b8;
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }

        /* Recommendation cards */
        .risk-card {
            padding: 1.5rem;
            border-radius: 20px;
            margin: 0.7rem 0 1.2rem 0;
            border-left: 7px solid;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        }

        .risk-card.critical {
            background: linear-gradient(
                100deg,
                rgba(127, 29, 29, 0.58),
                rgba(69, 10, 10, 0.25)
            );
            border-color: #ef4444;
        }

        .risk-card.urgent {
            background: linear-gradient(
                100deg,
                rgba(120, 53, 15, 0.58),
                rgba(69, 26, 3, 0.25)
            );
            border-color: #f59e0b;
        }

        .risk-card.routine {
            background: linear-gradient(
                100deg,
                rgba(20, 83, 45, 0.55),
                rgba(5, 46, 22, 0.25)
            );
            border-color: #22c55e;
        }

        .risk-card.uncertain {
            background: linear-gradient(
                100deg,
                rgba(30, 64, 175, 0.55),
                rgba(30, 58, 138, 0.25)
            );
            border-color: #60a5fa;
        }

        .risk-heading {
            color: #ffffff;
            font-size: 1.65rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }

        .risk-description {
            color: #e2e8f0;
            margin-bottom: 0.8rem;
        }

        .route-pill {
            display: inline-block;
            color: #f8fafc;
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            font-size: 0.8rem;
            font-weight: 700;
        }

        /* Streamlit components */
        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.17);
            border-radius: 16px;
            padding: 1rem;
        }

        div[data-testid="stMetricLabel"] {
            color: #94a3b8;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 1.2rem;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 11px;
            font-weight: 700;
            min-height: 2.8rem;
        }

        .privacy-note {
            color: #94a3b8;
            font-size: 0.82rem;
            padding: 0.8rem 1rem;
            border-left: 3px solid #38bdf8;
            background: rgba(14, 165, 233, 0.07);
            border-radius: 5px 12px 12px 5px;
        }

        .footer-note {
            color: #64748b;
            text-align: center;
            font-size: 0.78rem;
            margin-top: 3rem;
        }

        @media (max-width: 750px) {
            .stat-grid {
                grid-template-columns: 1fr;
            }

            .hero h1 {
                font-size: 2rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 4. HELPER FUNCTIONS
# =========================================================
def create_message_id(message):
    """
    Converts a message into a short anonymous identifier.

    The original message is not saved in the audit log.
    """
    return hashlib.sha256(
        message.encode("utf-8")
    ).hexdigest()[:12]


def save_human_decision(
    message,
    raw_model_category,
    recommended_category,
    confidence,
    safety_triggered,
    final_category,
    officer_reason,
):
    """Record the human decision without storing the message text."""

    AUDIT_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_has_content = (
        AUDIT_LOG_PATH.exists()
        and AUDIT_LOG_PATH.stat().st_size > 0
    )

    message_id = create_message_id(message)

    row = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "message_id": message_id,
        "raw_model_category": raw_model_category,
        "ai_recommendation": recommended_category,
        "model_confidence": round(confidence, 4),
        "safety_rule_triggered": safety_triggered,
        "human_final_category": final_category,
        "human_changed_recommendation": (
            final_category != recommended_category
        ),
        "human_reason": officer_reason,
    }

    with AUDIT_LOG_PATH.open(
        mode="a",
        newline="",
        encoding="utf-8",
    ) as log_file:
        writer = csv.DictWriter(
            log_file,
            fieldnames=row.keys(),
        )

        if not log_has_content:
            writer.writeheader()

        writer.writerow(row)

    return message_id


def load_example(example_message):
    """
    Places a fictional example into the message box.

    Any previous assessment is removed.
    """
    st.session_state["message_input"] = example_message
    st.session_state.pop("triage_result", None)
    st.session_state.pop("assessed_message", None)


def clear_case():
    """Clears the current demonstration case."""
    st.session_state["message_input"] = ""
    st.session_state.pop("triage_result", None)
    st.session_state.pop("assessed_message", None)


def confidence_description(confidence):
    """
    Converts a numeric confidence value into understandable text.

    Confidence is not the same as safety.
    """
    if confidence >= 0.75:
        return "Higher model confidence"
    if confidence >= 0.50:
        return "Moderate model confidence"
    return "Low model confidence"


# =========================================================
# 5. SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## 🛡️ PriorityLink")
    st.caption("Trusted message-triage prototype")

    st.divider()

    st.markdown("### Decision process")

    st.markdown(
        """
        **1. Receive**  
        A fictional public message is entered.

        **2. Assess**  
        The text model and safety rules examine it.

        **3. Explain**  
        The officer sees the recommendation and reasons.

        **4. Decide**  
        A human confirms or changes the category.
        """
    )

    st.divider()

    st.markdown("### System safeguards")

    st.success("Human decision required")
    st.info("Transparent safety rules")
    st.info("No automatic public response")
    st.info("Anonymous audit identifier")

    st.divider()

    st.markdown("### Prototype model")

    st.caption("TF-IDF + Logistic Regression")
    st.caption("Synthetic training messages")
    st.caption("Four recommendation categories")

    st.divider()

    st.button(
        "Clear current case",
        on_click=clear_case,
        use_container_width=True,
    )


# =========================================================
# 6. HERO SECTION
# =========================================================
hero_html = """
<div class="hero">
  <div class="brand-line">TRUSTED AI DECISION SUPPORT</div>
  <h1>Urgent Message Router</h1>
  <p>Helps correspondence officers identify messages that may require urgent human attention—without allowing AI to make the final decision.</p>
  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-value">95%</div>
      <div class="stat-label">Critical recall with safety layer*</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">4</div>
      <div class="stat-label">Transparent triage categories</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">Human</div>
      <div class="stat-label">Final decision-maker</div>
    </div>
  </div>
</div>
"""

st.markdown(
    hero_html,
    unsafe_allow_html=True,
)

st.caption(
    "*Prototype result from the 80-message synthetic validation dataset; "
    "not evidence of real-world performance."
)

st.error(
    "Emergency notice: This student prototype is not an emergency "
    "service. In Australia, call 000 when life or property is in "
    "immediate danger. Enter fictional messages only."
)


# =========================================================
# 7. MESSAGE INPUT
# =========================================================
st.markdown("## New message assessment")
st.write(
    "Enter a fictional message or select an example to demonstrate "
    "the different pathways."
)

example_column1, example_column2, example_column3 = st.columns(3)

with example_column1:
    st.button(
        "🚨 Critical example",
        on_click=load_example,
        args=(
            "A child has fallen into the water tank "
            "and is not responding.",
        ),
        use_container_width=True,
    )

with example_column2:
    st.button(
        "⚠️ Urgent example",
        on_click=load_example,
        args=(
            "Our only toilet is blocked and overflowing "
            "onto the floor.",
        ),
        use_container_width=True,
    )

with example_column3:
    st.button(
        "❓ Uncertain example",
        on_click=load_example,
        args=(
            "Something happened near my house and "
            "I need someone to help.",
        ),
        use_container_width=True,
    )

message = st.text_area(
    "Fictional incoming message",
    key="message_input",
    height=160,
    max_chars=5000,
    placeholder=(
        "Describe the fictional situation here. "
        "Do not enter real personal information."
    ),
)

character_column, privacy_column = st.columns([1, 3])

with character_column:
    st.caption(f"{len(message):,} / 5,000 characters")

with privacy_column:
    st.caption(
        "Privacy by design: the full message is not written "
        "to the decision audit log."
    )

assess_message = st.button(
    "Analyse and route message",
    type="primary",
    use_container_width=True,
)


# =========================================================
# 8. RUN MODEL AND SAFETY RULES
# =========================================================
if assess_message:
    if not message.strip():
        st.error("Enter a fictional message before assessment.")
    else:
        try:
            with st.spinner(
                "Running the text model and safety checks..."
            ):
                assessment = triage_message(message)

            st.session_state["triage_result"] = assessment
            st.session_state["assessed_message"] = message

        except (
            ValueError,
            TypeError,
            FileNotFoundError,
        ) as error:
            st.error(
                f"The assessment could not be completed: {error}"
            )


# =========================================================
# 9. DISPLAY RECOMMENDATION
# =========================================================
if "triage_result" in st.session_state:
    result = st.session_state["triage_result"]
    assessed_message = st.session_state[
        "assessed_message"
    ]

    recommended_category = result[
        "recommended_category"
    ]

    raw_category = result["model_category"]
    confidence = float(result["model_confidence"])

    safety_triggered = result[
        "safety_rule_triggered"
    ]

    style = CATEGORY_STYLES[recommended_category]

    st.divider()
    st.markdown("## Assessment result")

    risk_card_html = f"""
<div class="risk-card {style["css_class"]}">
  <div class="risk-heading">{style["icon"]} {recommended_category}: {style["title"]}</div>
  <div class="risk-description">{style["description"]}</div>
  <div class="route-pill">Route: {style["route"]}</div>
</div>
"""

    st.markdown(
        risk_card_html,
        unsafe_allow_html=True,
    )

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "AI recommendation",
            recommended_category,
        )

    with metric2:
        st.metric(
            "Raw model output",
            raw_category,
        )

    with metric3:
        st.metric(
            "Model confidence",
            f"{confidence:.1%}",
        )

    with metric4:
        st.metric(
            "Safety rule",
            "Triggered" if safety_triggered else "Not triggered",
        )

    st.caption(
        confidence_description(confidence)
        + ". Confidence describes the model prediction; "
        + "it does not prove that the message is safe."
    )

    if safety_triggered:
        st.error(
            "Safety intervention: An explicit danger indicator was "
            "detected. The message has been raised for immediate "
            "human review."
        )

    if result.get("low_confidence", confidence < 0.50):
        st.warning(
            "Low-confidence warning: The officer should inspect the "
            "message especially carefully."
        )

    result_column1, result_column2 = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    # -----------------------------------------------------
    # Explanation panel
    # -----------------------------------------------------
    with result_column1:
        with st.container(border=True):
            st.markdown("### Why did the system recommend this?")

            explanations = result.get("explanation", [])

            if explanations:
                for explanation in explanations:
                    st.markdown(f"- {explanation}")
            else:
                st.write(
                    "No explanation was returned. "
                    "Human review is still required."
                )

            st.markdown(
                """
                <div class="privacy-note">
                    The recommendation supports the officer—it does
                    not approve, reject or automatically answer the
                    sender.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------
    # Probability panel
    # -----------------------------------------------------
    with result_column2:
        with st.container(border=True):
            st.markdown("### Model probability comparison")

            probabilities = result.get(
                "probabilities",
                {},
            )

            for category in CATEGORIES:
                probability = float(
                    probabilities.get(category, 0.0)
                )

                label_column, score_column = st.columns(
                    [2, 1]
                )

                with label_column:
                    st.write(category)

                with score_column:
                    st.write(f"**{probability:.1%}**")

                st.progress(
                    int(round(probability * 100))
                )

    with st.expander("View technical assessment details"):
        st.write(
            "**Raw model category:**",
            raw_category,
        )

        st.write(
            "**Final AI recommendation:**",
            recommended_category,
        )

        st.write(
            "**Safety rule triggered:**",
            safety_triggered,
        )

        safety_reasons = result.get(
            "safety_reasons",
            [],
        )

        if safety_reasons:
            st.write("**Safety indicators:**")

            for reason in safety_reasons:
                st.write(f"- {reason}")
        else:
            st.write(
                "**Safety indicators:** "
                "No explicit rule matched."
            )

        st.warning(
            "No rule match does not guarantee that a message is safe."
        )


    # =====================================================
    # 10. HUMAN DECISION
    # =====================================================
    st.divider()
    st.markdown("## Human review and final decision")

    st.write(
        "The officer must review the original message, the AI "
        "recommendation and the reasons before recording a decision."
    )

    message_id = create_message_id(assessed_message)
    default_category_index = CATEGORIES.index(
        recommended_category
    )

    with st.form(
        key=f"human_decision_{message_id}"
    ):
        form_column1, form_column2 = st.columns(2)

        with form_column1:
            final_category = st.selectbox(
                "Human-selected final category",
                options=CATEGORIES,
                index=default_category_index,
            )

        with form_column2:
            demonstration_officer = st.text_input(
                "Demonstration officer ID",
                value="DEMO-OFFICER-01",
                disabled=True,
            )

        officer_reason = st.text_area(
            "Reason for confirming or changing the recommendation",
            placeholder=(
                "Example: I confirmed Critical because the message "
                "describes a child in immediate danger."
            ),
            height=120,
        )

        review_confirmed = st.checkbox(
            "I confirm that I reviewed the original message, "
            "the recommendation and the explanation."
        )

        submit_decision = st.form_submit_button(
            "Record human decision",
            type="primary",
            use_container_width=True,
        )

    if submit_decision:
        if not officer_reason.strip():
            st.error(
                "A reason is required for accountability."
            )

        elif not review_confirmed:
            st.error(
                "Confirm that you completed the human review."
            )

        else:
            saved_message_id = save_human_decision(
                message=assessed_message,
                raw_model_category=raw_category,
                recommended_category=recommended_category,
                confidence=confidence,
                safety_triggered=safety_triggered,
                final_category=final_category,
                officer_reason=officer_reason.strip(),
            )

            st.success(
                "Human decision recorded successfully. "
                f"Anonymous case ID: {saved_message_id}"
            )

            if final_category != recommended_category:
                st.info(
                    "The human officer overrode the AI recommendation. "
                    "The reason was recorded for later review."
                )
            else:
                st.info(
                    "The human officer confirmed the recommendation. "
                    "The officer—not the AI—remains accountable."
                )


# =========================================================
# 11. FOOTER
# =========================================================
st.markdown(
    """
    <div class="footer-note">
        PriorityLink • CDU IT Code Fair 2026 student prototype<br>
        Synthetic data only • AI recommends • A human decides
    </div>
    """,
    unsafe_allow_html=True,
)