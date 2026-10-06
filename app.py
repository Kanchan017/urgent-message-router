"""Streamlit interface for the PriorityLink prototype."""

import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from triage import triage_message


# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="PriorityLink",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# Application constants
# -----------------------------------------------------------------------------

CATEGORIES = ["Critical", "Urgent", "Routine", "Uncertain"]

PRIORITY_ORDER = {
    "Critical": 1,
    "Urgent": 2,
    "Uncertain": 3,
    "Routine": 4,
}

AUDIT_LOG_PATH = Path("results/human_decision_log.csv")
QUEUE_DATABASE_PATH = Path("results/prioritylink_queue.db")
MAXIMUM_MESSAGE_LENGTH = 5000

EXAMPLE_MESSAGES = {
    "Critical": (
        "A child has fallen into the water tank and is not responding."
    ),
    "Urgent": (
        "Our only toilet is blocked and overflowing onto the floor."
    ),
    "Routine": "Please update my postal address.",
    "Uncertain": (
        "Something happened near my house and I need someone to help."
    ),
}

CATEGORY_STYLES = {
    "Critical": {
        "css_class": "critical",
        "heading": "Immediate human review",
        "description": (
            "The message may describe an immediate threat to life, "
            "safety or property."
        ),
        "route": "Immediate review queue",
    },
    "Urgent": {
        "css_class": "urgent",
        "heading": "Priority human review",
        "description": (
            "The message requires prompt attention from an officer."
        ),
        "route": "Priority review queue",
    },
    "Routine": {
        "css_class": "routine",
        "heading": "Standard review",
        "description": (
            "The message can enter the normal human-review workflow."
        ),
        "route": "Standard review queue",
    },
    "Uncertain": {
        "css_class": "uncertain",
        "heading": "Clarification required",
        "description": (
            "The available information or model evidence is not strong "
            "enough for a reliable category."
        ),
        "route": "Clarification queue",
    },
}


# -----------------------------------------------------------------------------
# Simple operational styling
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
        :root {
            --page: #0b1220;
            --surface: #111a2b;
            --surface-2: #162237;
            --border: #2b3a55;
            --text: #f3f6fb;
            --muted: #9eacc2;
            --blue: #4f8cff;
            --blue-hover: #3d75dd;
            --critical: #e05252;
            --urgent: #d99a36;
            --routine: #3ea66b;
            --uncertain: #5b8def;
        }

        .stApp {
            background: var(--page);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: var(--page);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 4.25rem;
            padding-bottom: 3rem;
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            letter-spacing: -0.02em;
        }

        h1 {
            margin-bottom: 0.2rem !important;
        }

        p, label {
            color: #d8e0ec;
        }

        .app-intro {
            color: #b5c1d3;
            font-size: 1rem;
            margin: 0 0 0.35rem 0;
        }

        .section-note {
            color: var(--muted);
            font-size: 0.82rem;
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 7px;
            padding: 0.85rem 0.95rem;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
        }

        div[data-baseweb="textarea"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 7px !important;
        }

        div[data-baseweb="textarea"]:focus-within {
            border-color: var(--blue) !important;
            box-shadow: 0 0 0 1px var(--blue);
        }

        div[data-baseweb="textarea"] textarea {
            background: transparent !important;
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }

        div[data-baseweb="textarea"] textarea::placeholder {
            color: #6f8099 !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: var(--surface) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="input"] input {
            color: var(--text) !important;
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 6px !important;
            min-height: 2.65rem;
            font-weight: 650;
        }

        div.stButton > button[kind="secondary"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            color: #dce5f2 !important;
        }

        div.stButton > button[kind="secondary"] p {
            color: #dce5f2 !important;
        }

        div.stButton > button[kind="secondary"]:hover {
            background: var(--surface-2) !important;
            border-color: #58709a !important;
        }

        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button {
            background: var(--blue) !important;
            border: 1px solid var(--blue) !important;
            color: #ffffff !important;
        }

        div.stButton > button[kind="primary"] p,
        div[data-testid="stFormSubmitButton"] > button p {
            color: #ffffff !important;
        }

        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            background: var(--blue-hover) !important;
            border-color: var(--blue-hover) !important;
        }

        div[data-testid="stForm"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
        }

        [data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 7px;
        }

        .priority-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 5px solid;
            border-radius: 7px;
            padding: 1.1rem 1.2rem;
            margin: 0.65rem 0 1rem 0;
        }

        .priority-card.critical {
            border-left-color: var(--critical);
        }

        .priority-card.urgent {
            border-left-color: var(--urgent);
        }

        .priority-card.routine {
            border-left-color: var(--routine);
        }

        .priority-card.uncertain {
            border-left-color: var(--uncertain);
        }

        .priority-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.1em;
            margin-bottom: 0.3rem;
        }

        .priority-card.critical .priority-label {
            color: #f17b7b;
        }

        .priority-card.urgent .priority-label {
            color: #edb85e;
        }

        .priority-card.routine .priority-label {
            color: #72c995;
        }

        .priority-card.uncertain .priority-label {
            color: #8eb1f4;
        }

        .priority-heading {
            color: var(--text);
            font-size: 1.25rem;
            font-weight: 720;
            margin-bottom: 0.3rem;
        }

        .priority-description {
            color: #c4cfde;
            line-height: 1.5;
            margin-bottom: 0.55rem;
        }

        .priority-meta {
            color: var(--muted);
            font-size: 0.8rem;
        }

        hr {
            border-color: var(--border) !important;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-top: 4rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# State and audit helpers
# -----------------------------------------------------------------------------


def connect_to_queue_database():
    """Open the local database used for persistent queue records."""

    QUEUE_DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        QUEUE_DATABASE_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialise_queue_database():
    """Create the persistent queue table when it does not exist."""

    with connect_to_queue_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_cases (
                case_id TEXT PRIMARY KEY,
                sequence INTEGER NOT NULL UNIQUE,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL NOT NULL,
                safety_triggered INTEGER NOT NULL,
                status TEXT NOT NULL,
                final_category TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            )
            """
        )


def load_review_queue():
    """Load all saved queue cases from the local database."""

    with connect_to_queue_database() as connection:
        rows = connection.execute(
            """
            SELECT
                case_id,
                sequence,
                message,
                category,
                confidence,
                safety_triggered,
                status,
                final_category,
                result_json
            FROM review_cases
            ORDER BY sequence
            """
        ).fetchall()

    return [
        {
            "case_id": row["case_id"],
            "sequence": int(row["sequence"]),
            "message": row["message"],
            "category": row["category"],
            "confidence": float(row["confidence"]),
            "safety_triggered": bool(
                row["safety_triggered"]
            ),
            "status": row["status"],
            "final_category": row["final_category"],
            "result": json.loads(row["result_json"]),
        }
        for row in rows
    ]


def save_queue_item(queue_item):
    """Write one newly assessed case to the persistent queue."""

    with connect_to_queue_database() as connection:
        connection.execute(
            """
            INSERT INTO review_cases (
                case_id,
                sequence,
                message,
                category,
                confidence,
                safety_triggered,
                status,
                final_category,
                result_json,
                created_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                queue_item["case_id"],
                queue_item["sequence"],
                queue_item["message"],
                queue_item["category"],
                queue_item["confidence"],
                int(queue_item["safety_triggered"]),
                queue_item["status"],
                queue_item["final_category"],
                json.dumps(
                    queue_item["result"],
                    ensure_ascii=False,
                    default=str,
                ),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def save_review_status(case_id, final_category):
    """Persist the final human-review status for one case."""

    with connect_to_queue_database() as connection:
        connection.execute(
            """
            UPDATE review_cases
            SET status = ?, final_category = ?
            WHERE case_id = ?
            """,
            (
                "Reviewed",
                final_category,
                case_id,
            ),
        )


def initialise_state():
    """Load persistent queue records into Streamlit state."""

    initialise_queue_database()
    saved_queue = load_review_queue()

    st.session_state.setdefault("message_input", "")
    st.session_state["review_queue"] = saved_queue
    st.session_state["queue_counter"] = max(
        (
            item["sequence"]
            for item in saved_queue
        ),
        default=0,
    )


def create_message_id(message):
    """Create an anonymous identifier without storing message text."""

    return hashlib.sha256(
        message.encode("utf-8")
    ).hexdigest()[:12]


def protect_csv_cell(value):
    """Prevent spreadsheet programs from executing a text value."""

    text = str(value).strip()

    if text.startswith(("=", "+", "-", "@")):
        return "'" + text

    return text


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
        "raw_model_category": protect_csv_cell(
            raw_model_category
        ),
        "ai_recommendation": protect_csv_cell(
            recommended_category
        ),
        "model_confidence": round(float(confidence), 4),
        "safety_rule_triggered": bool(safety_triggered),
        "human_final_category": protect_csv_cell(
            final_category
        ),
        "human_changed_recommendation": (
            final_category != recommended_category
        ),
        "human_reason": protect_csv_cell(officer_reason),
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


def clear_current_case():
    """Clear the current case while preserving the review queue."""

    st.session_state["message_input"] = ""
    st.session_state.pop("triage_result", None)
    st.session_state.pop("assessed_message", None)
    st.session_state.pop("active_case_id", None)


def load_example(example_message):
    """Load one fictional example into the message field."""

    st.session_state["message_input"] = example_message
    st.session_state.pop("triage_result", None)
    st.session_state.pop("assessed_message", None)
    st.session_state.pop("active_case_id", None)


def add_to_review_queue(result):
    """Add an assessed message to the persistent review queue."""

    st.session_state["queue_counter"] += 1
    sequence = st.session_state["queue_counter"]
    case_id = f"CASE-{sequence:03d}"

    queue_item = {
        "case_id": case_id,
        "sequence": sequence,
        "message": result["message"],
        "category": str(result["recommended_category"]),
        "confidence": float(result["model_confidence"]),
        "safety_triggered": bool(
            result["safety_rule_triggered"]
        ),
        "status": "Awaiting review",
        "final_category": "",
        "result": result,
    }

    save_queue_item(queue_item)
    st.session_state["review_queue"].append(queue_item)
    return case_id


def queue_sort_key(item):
    """Sort waiting cases by priority and then arrival order."""

    reviewed_rank = (
        1 if item["status"] == "Reviewed" else 0
    )

    return (
        reviewed_rank,
        PRIORITY_ORDER.get(item["category"], 99),
        item["sequence"],
    )


def waiting_cases():
    """Return waiting messages in operational priority order."""

    cases = [
        item
        for item in st.session_state["review_queue"]
        if item["status"] == "Awaiting review"
    ]

    return sorted(cases, key=queue_sort_key)


def find_case(case_id):
    """Find a case in the currently loaded queue."""

    for item in st.session_state["review_queue"]:
        if item["case_id"] == case_id:
            return item

    return None


def mark_case_reviewed(case_id, final_category):
    """Update the status of a human-reviewed case."""

    case = find_case(case_id)

    if case is not None:
        save_review_status(case_id, final_category)
        case["status"] = "Reviewed"
        case["final_category"] = final_category


def open_next_waiting_case():
    """Open the highest-priority case waiting for review."""

    cases = waiting_cases()

    if not cases:
        return

    next_case = cases[0]

    st.session_state["message_input"] = next_case["message"]
    st.session_state["triage_result"] = next_case["result"]
    st.session_state["assessed_message"] = next_case["message"]
    st.session_state["active_case_id"] = next_case["case_id"]


def queue_position(case_id):
    """Return a waiting case's current queue position."""

    for position, item in enumerate(
        waiting_cases(),
        start=1,
    ):
        if item["case_id"] == case_id:
            return position

    return None


def message_preview(message, maximum_length=68):
    """Create a short single-line queue preview."""

    preview = " ".join(str(message).split())

    if len(preview) <= maximum_length:
        return preview

    return preview[: maximum_length - 1].rstrip() + "…"


initialise_state()


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------

st.title("PriorityLink")

st.markdown(
    """
    <p class="app-intro">
        Assess incoming messages, prioritise the human-review queue,
        and record the officer's final decision.
    </p>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Student prototype using fictional messages only. "
    "It is not an emergency service, and the human officer remains "
    "responsible for every final decision."
)

flash_message = st.session_state.pop("flash_message", None)

if flash_message:
    st.success(flash_message)

st.divider()


# -----------------------------------------------------------------------------
# Message intake and live queue
# -----------------------------------------------------------------------------

input_column, queue_column = st.columns(
    [0.9, 1.1],
    gap="large",
)

with input_column:
    st.subheader("New message")
    st.caption("Enter a fictional message or load a test example.")

    example_column1, example_column2 = st.columns(2)

    with example_column1:
        st.button(
            "Critical example",
            on_click=load_example,
            args=(EXAMPLE_MESSAGES["Critical"],),
            use_container_width=True,
        )

        st.button(
            "Routine example",
            on_click=load_example,
            args=(EXAMPLE_MESSAGES["Routine"],),
            use_container_width=True,
        )

    with example_column2:
        st.button(
            "Urgent example",
            on_click=load_example,
            args=(EXAMPLE_MESSAGES["Urgent"],),
            use_container_width=True,
        )

        st.button(
            "Uncertain example",
            on_click=load_example,
            args=(EXAMPLE_MESSAGES["Uncertain"],),
            use_container_width=True,
        )

    message = st.text_area(
        "Fictional incoming message",
        key="message_input",
        height=150,
        max_chars=MAXIMUM_MESSAGE_LENGTH,
        placeholder="Describe the fictional situation here.",
    )

    st.caption(
        f"{len(message):,} / {MAXIMUM_MESSAGE_LENGTH:,} characters · "
        "Saved locally for queue and status tracking."
    )

    assess_message = st.button(
        "Assess and add to queue",
        type="primary",
        use_container_width=True,
    )

    if assess_message:
        if not message.strip():
            st.error("Enter a fictional message before assessment.")

        else:
            try:
                with st.spinner("Assessing message..."):
                    assessment = triage_message(message)

                case_id = add_to_review_queue(assessment)

                st.session_state["triage_result"] = assessment
                st.session_state["assessed_message"] = assessment[
                    "message"
                ]
                st.session_state["active_case_id"] = case_id

            except (
                ValueError,
                TypeError,
                FileNotFoundError,
            ) as error:
                st.error(
                    f"The assessment could not be completed: {error}"
                )

            except Exception:
                st.error(
                    "The assessment could not be completed. Check the "
                    "model files and try again."
                )

    if "triage_result" in st.session_state:
        st.button(
            "Start another message",
            on_click=clear_current_case,
            use_container_width=True,
        )


with queue_column:
    st.subheader("Human-review queue")
    st.caption(
        "Waiting messages are ordered Critical, Urgent, Uncertain, "
        "then Routine."
    )

    waiting = waiting_cases()
    reviewed = [
        item
        for item in st.session_state["review_queue"]
        if item["status"] == "Reviewed"
    ]

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Critical waiting",
            sum(
                item["category"] == "Critical"
                for item in waiting
            ),
        )

    with metric2:
        st.metric(
            "Urgent waiting",
            sum(
                item["category"] == "Urgent"
                for item in waiting
            ),
        )

    with metric3:
        st.metric("Total waiting", len(waiting))

    if not st.session_state["review_queue"]:
        st.info(
            "The queue is empty. Assess a message to create the "
            "first case."
        )

    else:
        ordered_cases = waiting + sorted(
            reviewed,
            key=lambda item: item["sequence"],
            reverse=True,
        )

        queue_rows = []
        waiting_position = 0

        for item in ordered_cases:
            if item["status"] == "Awaiting review":
                waiting_position += 1
                displayed_position = waiting_position
            else:
                displayed_position = "Done"

            queue_rows.append(
                {
                    "Position": displayed_position,
                    "Case": item["case_id"],
                    "Priority": item["category"],
                    "Message": message_preview(item["message"]),
                    "Status": item["status"],
                }
            )

        st.dataframe(
            queue_rows,
            hide_index=True,
            use_container_width=True,
            height=min(330, 38 * len(queue_rows) + 38),
        )

        if waiting:
            st.button(
                "Open next priority message",
                type="primary",
                on_click=open_next_waiting_case,
                use_container_width=True,
            )

# -----------------------------------------------------------------------------
# Current assessment and officer decision
# -----------------------------------------------------------------------------

if "triage_result" in st.session_state:
    result = st.session_state["triage_result"]
    assessed_message = st.session_state["assessed_message"]
    current_input = " ".join(
        st.session_state["message_input"].split()
    )

    if current_input != assessed_message:
        st.info(
            "The message text has changed. Select "
            "'Assess and add to queue' to create a new assessment."
        )

    else:
        recommended_category = str(
            result["recommended_category"]
        )
        raw_category = str(result["model_category"])
        confidence = float(result["model_confidence"])
        safety_triggered = bool(
            result["safety_rule_triggered"]
        )
        style = CATEGORY_STYLES.get(
            recommended_category,
            CATEGORY_STYLES["Uncertain"],
        )

        active_case_id = st.session_state.get(
            "active_case_id"
        )
        active_case = find_case(active_case_id)
        position = queue_position(active_case_id)

        if active_case and active_case["status"] == "Reviewed":
            queue_status = "Review complete"
        elif position is not None:
            queue_status = f"Queue position {position}"
        else:
            queue_status = "Awaiting human review"

        st.divider()
        st.subheader("Current case")

        recommendation_html = f"""
        <div class="priority-card {style['css_class']}">
            <div class="priority-label">
                {recommended_category.upper()}
            </div>
            <div class="priority-heading">
                {style['heading']}
            </div>
            <div class="priority-description">
                {style['description']}
            </div>
            <div class="priority-meta">
                {active_case_id} · {queue_status} · {style['route']}
            </div>
        </div>
        """

        st.markdown(
            recommendation_html,
            unsafe_allow_html=True,
        )

        result_metric1, result_metric2, result_metric3 = (
            st.columns(3)
        )

        with result_metric1:
            st.metric("Raw model output", raw_category)

        with result_metric2:
            st.metric(
                "Model confidence",
                f"{confidence:.1%}",
            )

        with result_metric3:
            st.metric(
                "Safety rule",
                (
                    "Triggered"
                    if safety_triggered
                    else "Not triggered"
                ),
            )

        st.caption(
            "Confidence describes the statistical model only; it "
            "does not prove that a message is safe or correct."
        )

        if safety_triggered:
            st.error(
                "An explicit danger indicator triggered immediate "
                "human review."
            )

        elif result.get("low_confidence", confidence < 0.50):
            st.warning(
                "The model evidence is weak. The message has been "
                "sent for human clarification."
            )

        with st.expander("Assessment details"):
            source = result.get(
                "recommendation_source",
                "machine_learning_model",
            )

            source_names = {
                "critical_safety_rule": "Critical safety rule",
                "safety_rule": "Critical safety rule",
                "low_confidence_fallback": (
                    "Low-confidence fallback"
                ),
                "machine_learning_model": (
                    "Machine-learning model"
                ),
            }

            st.write(
                "**Recommendation source:**",
                source_names.get(
                    source,
                    source.replace("_", " ").title(),
                ),
            )

            explanations = result.get("explanation", [])

            for explanation in explanations:
                st.write(f"- {explanation}")

            safety_reasons = result.get(
                "safety_reasons",
                [],
            )

            if safety_reasons:
                st.write("**Matched safety indicators:**")

                for reason in safety_reasons:
                    st.write(f"- {reason}")

            probabilities = result.get("probabilities", {})

            if probabilities:
                probability_rows = [
                    {
                        "Category": category,
                        "Probability": (
                            f"{float(probabilities.get(category, 0)):.1%}"
                        ),
                    }
                    for category in CATEGORIES
                ]

                st.write("**Model probability breakdown:**")
                st.dataframe(
                    probability_rows,
                    hide_index=True,
                    use_container_width=True,
                )

        st.subheader("Officer decision")

        if active_case and active_case["status"] == "Reviewed":
            st.success(
                "This case was reviewed and recorded as "
                f"{active_case['final_category']}."
            )

        else:
            default_category_index = CATEGORIES.index(
                recommended_category
            )

            with st.form(
                key=f"human_decision_{active_case_id}"
            ):
                final_category = st.selectbox(
                    "Final category",
                    options=CATEGORIES,
                    index=default_category_index,
                )

                officer_reason = st.text_area(
                    "Reason for the decision",
                    placeholder=(
                        "Briefly explain why the recommendation was "
                        "confirmed or changed."
                    ),
                    height=100,
                    max_chars=500,
                )

                review_confirmed = st.checkbox(
                    "I reviewed the message, recommendation and "
                    "explanation."
                )

                submit_decision = st.form_submit_button(
                    "Record human decision",
                    type="primary",
                    use_container_width=True,
                )

            if submit_decision:
                if not officer_reason.strip():
                    st.error(
                        "Enter a short reason for accountability."
                    )

                elif not review_confirmed:
                    st.error(
                        "Confirm that the human review was completed."
                    )

                else:
                    saved_message_id = save_human_decision(
                        message=assessed_message,
                        raw_model_category=raw_category,
                        recommended_category=(
                            recommended_category
                        ),
                        confidence=confidence,
                        safety_triggered=safety_triggered,
                        final_category=final_category,
                        officer_reason=officer_reason.strip(),
                    )

                    mark_case_reviewed(
                        active_case_id,
                        final_category,
                    )

                    st.session_state["flash_message"] = (
                        "Human decision recorded. "
                        f"Anonymous audit ID: {saved_message_id}"
                    )

                    st.rerun()
