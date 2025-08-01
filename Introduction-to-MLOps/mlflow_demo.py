import os
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.models.signature import infer_signature

mlflow.set_tracking_uri("../mlflow")  # Set your MLflow tracking URI

EXPERIMENT_NAME = "Iris-Demo"
client = MlflowClient()

if not client.get_experiment_by_name(EXPERIMENT_NAME):
    # Create a new experiment if it does not exist
    client.create_experiment(EXPERIMENT_NAME)

mlflow.set_experiment(EXPERIMENT_NAME)

# load data and train classifier
iris = load_iris(as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)

clf = LogisticRegression(max_iter=200)

with mlflow.start_run() as run:
    clf.fit(X_train, y_train)
    
    # Predict and evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Log parameters, metrics, and model
    mlflow.log_param("model", "Logistic Regression")
    mlflow.log_param("solver", clf.solver)
    mlflow.log_metric("accuracy", accuracy)
    
    # infer the model signature from the training data
    # the signature captures the input and output schema of the model
    signature = infer_signature(X_train, clf.predict(X_train))
    mlflow.sklearn.log_model(clf, "model", signature=signature)
    
    # create input example (using first 5 rows of the training data)
    input_example = X_train.head(5)
    
    # log model with signature and input example
    mlflow.sklearn.log_model(
        sk_model=clf,
        artifact_path="model",
        registered_model_name="IrisSKModel",
        signature=signature,
        input_example=input_example
    )
    
    print(f"Model logged and sent to registry (run_id = {run.info.run_id})")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Model signature: {signature}")
    