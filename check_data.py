import pandas as pd

# Location of the training dataset
DATA_PATH = "data/training_messages.csv"

# Read the CSV file into a pandas table
data = pd.read_csv(DATA_PATH)

# Columns that must contain information
required_columns = [
    "message_id",
    "message",
    "label",
    "reason",
    "topic",
    "writing_style",
    "difficulty",
    "scenario_group",
    "source",
    "split",
    "review_status",
]

print(f"Total messages: {len(data)}")

# Count missing values only in required columns.
# reviewer_1 and reviewer_2 are excluded because they are intentionally blank.
missing_required = data[required_columns].isna().sum().sum()
print(f"Missing required values: {missing_required}")

# Count messages that contain exactly the same text
duplicate_messages = data["message"].duplicated().sum()
print(f"Duplicate messages: {duplicate_messages}")

# Count the number of examples in each urgency category
print("\nClass distribution:")
print(data["label"].value_counts())

# Check whether all message IDs are unique
duplicate_ids = data["message_id"].duplicated().sum()
print(f"\nDuplicate message IDs: {duplicate_ids}")

# Show whether the dataset passed the basic checks
if (
    len(data) == 400
    and missing_required == 0
    and duplicate_messages == 0
    and duplicate_ids == 0
):
    print("\nDataset check: PASSED")
else:
    print("\nDataset check: REVIEW REQUIRED")