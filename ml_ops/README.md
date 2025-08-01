# **MLflow + Feast + PostgreSQL (Windows Setup)**

This repository contains a working example of integrating **Feast** (feature store) with **MLflow** (experiment tracking + model registry) using a **PostgreSQL backend**.
It is designed for **Windows** with a **flat directory structure** (no nested `feature_repo/feature_repo` folders).

---

## **📂 Project Structure**

```
ml_ops/
│
├── mlflow_data/                # MLflow backend + artifacts
│
└── feature_repo/               # Feast repository root
    │   feature_store.yaml      # Feast config
    │   driver_features.py      # Feast feature definitions
    │   gen_data.py             # Generates demo feature data
    │   train.py                # Trains model + logs to MLflow
    │
    ├── data/                   # Generated data
    │   driver_stats.parquet
```

---

## **1️⃣ Prerequisites**

* **Python 3.10+**
* **PostgreSQL** installed locally
  Download: [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
* **Virtual environment** recommended

---

## **2️⃣ Create PostgreSQL Databases**

In **pgAdmin** or `psql`:

```sql
CREATE DATABASE mlflow_db;
CREATE DATABASE feast_db;
```

---

## **3️⃣ Python Environment Setup**

```powershell
cd T:\dev\Learn\AI\learn_ai\ml_ops

python -m venv .venv
.venv\Scripts\activate

pip install mlflow "feast[postgres]" scikit-learn pandas sqlalchemy
```

---

## **4️⃣ Start MLflow Tracking Server**

```powershell
mkdir ml_ops\mlflow
cd ml_ops\mlflow

mlflow server `
    --backend-store-uri postgresql://postgres:edno@localhost:5432/mlflow_db `
    --default-artifact-root "T:/dev/Learn/AI/learn_ai/ml_ops/mlflow/artifacts" `
    --host 127.0.0.1 `
    --port 5000
```

> Replace `YOURPASSWORD` with your PostgreSQL password.
> Leave this running in its own terminal.

---

## **5️⃣ Configure Feast**

**`feature_store.yaml`** in `feature_repo/`:

```yaml
project: feature_repo

registry: data/registry.db

provider: local

offline_store:
  type: postgres
  host: localhost
  port: 5432
  database: feast_db
  db_schema: public
  user: postgres
  password: YOURPASSWORD

online_store:
  type: sqlite
  path: data/online_store.db
```

---

## **6️⃣ Generate Demo Data**

`feature_repo/gen_data.py`:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

end_date = datetime.now()
dates = [end_date - timedelta(days=i) for i in range(10)]

rows = []
for driver_id in range(1001, 1011):
    for d in dates:
        rows.append({
            "driver_id": driver_id,
            "event_timestamp": d,
            "conv_rate": np.random.rand(),
            "acc_rate": np.random.rand(),
            "avg_daily_trips": np.random.randint(10, 50)
        })

df = pd.DataFrame(rows)
os.makedirs("data", exist_ok=True)
df.to_parquet("data/driver_stats.parquet")
print("✅ Data saved to data/driver_stats.parquet")
```

Run:

```powershell
cd feature_repo
python gen_data.py
```

---

## **7️⃣ Apply & Materialize Features**

```powershell
cd feature_repo
feast apply
feast materialize-incremental 2025-08-01T00:00:00
```

---

## **8️⃣ Train a Model & Log to MLflow**

`feature_repo/train.py`:

```python
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature

# Paths
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "driver_stats.parquet")

# MLflow config
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("Feast-MLflow-Demo")

# Load data
df = pd.read_parquet(DATA_PATH)
X = df[["conv_rate", "acc_rate", "avg_daily_trips"]]
y = (df["conv_rate"] > 0.5).astype(int)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

# Model training
model = LogisticRegression()
with mlflow.start_run():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    # Log params/metrics
    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_metric("accuracy", acc)

    # Log model
    signature = infer_signature(X_train, preds)
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="DriverModel",
        signature=signature,
        input_example=X_train.head(3)
    )

    print(f"✅ Model logged. Accuracy={acc:.4f}")
```

Run:

```powershell
cd feature_repo
python train.py
```

---

## **9️⃣ View Results**

* **MLflow UI** → [http://127.0.0.1:5000](http://127.0.0.1:5000)

  * **Experiments tab** → See runs
  * **Models tab** → See `DriverModel` versions
* **Feast UI**:

```powershell
cd feature_repo
feast ui
```

---

## **🔟 Notes**

* Always run **Feast commands from inside `feature_repo/`** (where `feature_store.yaml` is located).
* Always activate `.venv` before running any commands:

```powershell
.venv\Scripts\activate
```

* PostgreSQL must be running for both MLflow and Feast.

