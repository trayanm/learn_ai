import os
import time
import joblib
import pandas as pd
from sklearn.model_selection import (
    StratifiedKFold,
    KFold,
    TimeSeriesSplit,
    cross_val_score,
)
from sklearn.metrics import roc_auc_score

# ------------------------------------------------------------
# 1. Download & prepare UCI Adult data
# ------------------------------------------------------------
URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
COLS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]

print("⏬  Fetching Adult data …")
df = pd.read_csv(
    URL, names=COLS, header=None, na_values=" ?", skipinitialspace=True
).dropna()

# Create target and feature matrix
y = df["income"].str.contains(">50K").astype(int)
X = df.drop(columns="income")

print(
    f"✅  Dataset ready — {len(X):,} rows, "
    f"class balance: {y.mean():.2%} high-income\n"
)

# ------------------------------------------------------------
# 2. Load the pre-trained models (assumed to be pipelines)
# ------------------------------------------------------------
FILES = {
    "LogReg": "LogisticRegression.joblib",
    "RandForest": "RandomForest.joblib",
    "MLP": "MLPClassifier.joblib",
}

models = {}
for name, path in FILES.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cannot find '{path}' in working directory.")
    models[name] = joblib.load(path)
    print(f"🔹  Loaded {name} pipeline from {path}")
print("")

# ------------------------------------------------------------
# 3. Validation strategies
# ------------------------------------------------------------
splits = {
    "StratifiedK5": StratifiedKFold(n_splits=5, shuffle=True, random_state=0),
    "KFold5": KFold(n_splits=5, shuffle=True, random_state=0),
    "TimeSeries3": TimeSeriesSplit(n_splits=3, test_size=2000),
}


def blocked_progressive(X_df, y_ser, pipe, block=2000):
    """Rolling-window validation until AUC stabilises (<0.001 delta)."""
    scores, start = [], 0
    total = len(X_df)
    while start + 2 * block <= total:
        end_train = start + block
        end_test = end_train + block
        X_tr, y_tr = X_df.iloc[start:end_train], y_ser.iloc[start:end_train]
        X_te, y_te = X_df.iloc[end_train:end_test], y_ser.iloc[end_train:end_test]
        pipe.fit(X_tr, y_tr)
        scores.append(roc_auc_score(y_te, pipe.predict_proba(X_te)[:, 1]))
        if len(scores) > 2 and abs(scores[-1] - scores[-2]) < 0.001:
            break
        start += block
    return sum(scores) / len(scores)


# ------------------------------------------------------------
# 4. Run benchmarks
# ------------------------------------------------------------
rows = []

for m_name, pipe in models.items():
    # Standard CV options
    for s_name, splitter in splits.items():
        t0 = time.perf_counter()
        auc = cross_val_score(
            pipe, X, y, cv=splitter, scoring="roc_auc", n_jobs=1
        ).mean()
        duration = time.perf_counter() - t0
        rows.append((m_name, s_name, round(auc, 4), round(duration, 2)))

    # Blocked Progressive
    t0 = time.perf_counter()
    auc = blocked_progressive(X, y, pipe)
    duration = time.perf_counter() - t0
    rows.append((m_name, "BlockedProg", round(auc, 4), round(duration, 2)))

# ------------------------------------------------------------
# 5. Display results: AUC + Seconds
# ------------------------------------------------------------
df_results = pd.DataFrame(rows, columns=["Model", "Strategy", "AUC", "Seconds"])
df_pivot = df_results.pivot(index="Model", columns="Strategy")

# Clean up multi-index columns
df_pivot.columns = ["_".join(col).strip() for col in df_pivot.columns.values]
df_pivot = df_pivot.reset_index()

# Print
with pd.option_context("display.width", None):
    print("\n📊  AUC and Runtime (sec) by Model and Strategy\n")
    print(df_pivot)
