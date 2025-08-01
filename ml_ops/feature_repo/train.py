import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("Feast-MLflow-Postgres-Demo")

df = pd.read_parquet("data/driver_stats.parquet")

X = df[["conv_rate", "acc_rate", "avg_daily_trips"]]
y = (df["conv_rate"] > 0.5).astype(int)

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

model = LogisticRegression()
with mlflow.start_run():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    signature = infer_signature(X_train, preds)

    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_metric("accuracy", acc)

    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="DriverModel",
        signature=signature,
        input_example=X_train.head(3)
    )

    print(f"✅ Model logged. Accuracy={acc:.4f}")
    
print("Tracking URI in this run:", mlflow.get_tracking_uri())