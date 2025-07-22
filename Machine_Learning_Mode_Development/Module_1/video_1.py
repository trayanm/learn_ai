import pandas as pd
import joblib
import os
import time
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.exceptions import ConvergenceWarning

# Load UCI Adult dataset (10k rows for speed)
df = pd.read_csv(
    "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data",
    header=None,
    names=[
        "age", "workclass", "fnlwgt", "education", "education-num",
        "marital-status", "occupation", "relationship", "race", "sex",
        "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"
    ]
)

# Drop rows with missing values
df.replace(" ?", np.nan, inplace=True)
df.dropna(inplace=True)

X = df.drop("income", axis=1)
y = df["income"].apply(lambda x: x.strip() == ">50K")

# Identify column types
cat_cols = X.select_dtypes(include="object").columns.tolist()
num_cols = X.select_dtypes(exclude="object").columns.tolist()

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=42
)

# Preprocessing: One-hot for categoricals, scale for numerics
preprocessor = ColumnTransformer([
    ("onehot", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("scale", StandardScaler(), num_cols)
])

# Define models
models = {
    "LogisticRegression": LogisticRegression(max_iter=2000, solver="lbfgs", n_jobs=-1),
    "RandomForest": RandomForestClassifier(n_estimators=200, n_jobs=-1),
    "MLPClassifier": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=400)
}

results = {}

for name, model in models.items():
    pipeline = make_pipeline(preprocessor, model)

    # Fit
    start_time = time.perf_counter()
    pipeline.fit(X_train, y_train)
    fit_time = time.perf_counter() - start_time

    # Save model to disk
    filename = f"{name}.joblib"
    joblib.dump(pipeline, filename)
    model_size_kb = os.path.getsize(filename) / 1024

    # Inference timing (single-row prediction)
    start_time = time.perf_counter()
    for _ in range(1000):
        pipeline.predict(X_test.iloc[[0]])  # Correct: 2D input
    latency_ms = (time.perf_counter() - start_time) / 1000 * 1000


    # Accuracy
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    results[name] = {
        "Train Time (s)": round(fit_time, 3),
        "Latency (ms)": round(latency_ms, 3),
        "Model Size (KB)": round(model_size_kb, 1),
        "Accuracy": round(acc * 100, 2)
    }

# Display results in aligned output
print("\nModel Benchmark Results:\n")
print("{:<18} {:>15} {:>15} {:>18} {:>12}".format(
    "Model", "Train Time (s)", "Latency (ms)", "Model Size (KB)", "Accuracy (%)"
))
print("-" * 80)

for model_name, stats in results.items():
    print("{:<18} {:>15} {:>15} {:>18} {:>12}".format(
        model_name,
        stats["Train Time (s)"],
        stats["Latency (ms)"],
        stats["Model Size (KB)"],
        stats["Accuracy"]
    ))
