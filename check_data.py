import pandas as pd

data_path = "data/train_messages.csv"
data = pd.read_csv(data_path)

print("Total messages:", len(data))

print("Total missing values:", data.isna().sum().sum())

print("Duplicate messages:", data["message"].duplicated().sum())

print("\nClass distribution:")
print(data["urgency"].value_counts())

print("\nFirst five records:")
print(data.head())