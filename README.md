# PriorityLink

PriorityLink is a student prototype for the CDU IT Code Fair 2026 challenge **Getting urgent messages to a human, fast**. It assesses fictional incoming messages, recommends a priority, places them in a human-review queue, and records the officer's final decision.

The system supports four categories:

- **Critical** — possible immediate threat to life, safety, or property
- **Urgent** — requires prompt human attention
- **Uncertain** — lacks enough information or reliable model evidence
- **Routine** — can enter the normal review workflow

PriorityLink is a decision-support tool. It does not make the final decision and is not an emergency service.

## Main features

- TF-IDF and logistic-regression text classification
- Explainable safety rules for explicit danger indicators
- Confidence display and an uncertainty pathway
- Priority-ordered human-review queue
- Human confirmation or correction of every recommendation
- Persistent local queue and status tracking using SQLite
- Anonymous CSV audit log for completed human decisions
- Streamlit interface with fictional demonstration messages

## How the system works

1. The incoming text is validated and cleaned.
2. The machine-learning model predicts a category and probabilities.
3. Safety rules check for explicit indicators such as breathing failure, weapons, fire, drowning, overdose, self-harm, gas, electrical hazards, and structural collapse.
4. The model result, confidence, and safety result are combined into a recommendation.
5. The message enters the queue, ordered Critical, Urgent, Uncertain, then Routine.
6. A human officer reviews the evidence and records the final category and reason.

## Project structure

```text
Urgent_Message_router_starter/
├── app.py
├── triage.py
├── safety_rules.py
├── train_model.py
├── requirements.txt
├── data/
├── models/
│   └── urgency_model_v2.joblib
└── results/
    ├── prioritylink_queue.db       # generated locally
    └── human_decision_log.csv      # generated locally
```

The exact contents of `data/` include the training and validation CSV files used by the project.

## Requirements

- Windows 10 or 11
- Python 3.10 or later
- Internet access for the initial package installation

## Installation

Open PowerShell or the VS Code terminal in the project folder:

```powershell
cd C:\dev\Urgent_Message_router_starter
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Model preparation

The repository contains:

```text
models/urgency_model_v2.joblib
```

If the model file is missing, or if the training data has changed, retrain it:

```powershell
.\.venv\Scripts\python.exe train_model.py
```

## Run the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit will display a local address, normally:

```text
http://localhost:8501
```

## Basic demonstration

Use the example buttons or enter fictional messages. A useful demonstration sequence is:

1. Routine: `Please update my postal address.`
2. Urgent: `Our only toilet is blocked and overflowing onto the floor.`
3. Critical: `A child has fallen into the water tank and is not responding.`
4. Uncertain: `Something happened near my house and I need someone to help.`

Show that the Critical case moves above lower-priority cases. Select **Open next priority message**, inspect the model output and safety information, then record a human decision.

## Persistent records

PriorityLink creates the following local runtime files automatically:

- `results/prioritylink_queue.db` stores the fictional message, recommendation, queue status, and final category so the queue survives refreshes and restarts.
- `results/human_decision_log.csv` stores an anonymous message identifier, model result, confidence, safety flag, final human category, and review reason. It does not store the full message text.

These files should not be committed to GitHub or distributed with real message data. The `.gitignore` file contains:

```gitignore
results/prioritylink_queue.db
results/human_decision_log.csv
```

## Dataset statement

This prototype was trained using synthetic messages created with AI assistance for educational testing. The data was checked for formatting, missing values, duplicates, and label consistency. It does not contain real emergency messages or personal information.

Synthetic data made it possible to build a privacy-preserving prototype, but it does not fully represent real language, locations, cultural variation, spelling, or emergency conditions. The reported evaluation therefore describes performance on the project dataset only and must not be presented as evidence of production readiness.

## Safety and human oversight

- The statistical model can produce false positives and false negatives.
- Pattern-based safety rules have limited wording coverage.
- Confidence is model evidence, not proof that a message is safe.
- Every recommendation requires human review.
- The interface demonstrated with fictional messages.
- A production system would require real-world validation, secure authentication, access controls, encryption, monitoring, and organisational approval.

## Current limitations

- Small synthetic dataset
- English-language text only
- No sender authentication or automatic emergency-service connection
- Safety rules cannot cover every possible phrase
- Local SQLite storage is intended for a single-computer prototype
- No production deployment or clinical, legal, or emergency-service validation

## Code verification

Run a basic syntax check:

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py triage.py safety_rules.py train_model.py
```

Then start the app and test at least one example from every category.

## Responsible use

PriorityLink demonstrates how machine learning, explainable rules, confidence handling, queue prioritisation, and human oversight can work together. It must not be used to replace emergency services or independent human judgement.
