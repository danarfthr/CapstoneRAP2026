from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
INPUT = BASE_DIR / "youtube_comments.csv"

df = pd.read_csv(INPUT)

print("Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isna().sum())

print("\nData types:")
print(df.dtypes)

# Treat empty strings / whitespace as missing
df = df.replace(r"^\s*$", np.nan, regex=True)

print("\nMissing values after treating blank strings as NaN:")
print(df.isna().sum())