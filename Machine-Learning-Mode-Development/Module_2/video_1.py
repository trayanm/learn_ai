import os
import joblib
import pandas as pd
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import StringTensorType, FloatTensorType

def load_data():
    data_path = 'adult_data.csv'
    if not os.path.exists(data_path):
        df = pd.read_csv(
            "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data",
            header=None,
            names=[
                "age", "workclass", "fnlwgt", "education", "education-num",
                "marital-status", "occupation", "relationship", "race", "sex",
                "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"
            ]
        )
        df.to_csv(data_path, index=False)
    else:
        df = pd.read_csv(data_path)  # Remove header=None since the saved file has headers
    return df

# main code
df = load_data()

df.dropna(inplace=True)
X = df.drop("income", axis=1)

# Construct initial_types using column names and types
initial_types = []
for col in X.columns:
    if X[col].dtype == object:
        initial_types.append((col, StringTensorType([None, 1])))
    else:
        initial_types.append((col, FloatTensorType([None, 1])))

# Load fitted pipeline | Use file names of models trained in Module 1
pipe = joblib.load("LogisticRegression.joblib")

# Convert pipeline to ONNX using column-aware initial_types
onnx_model = convert_sklearn(pipe, initial_types=initial_types)

# save the ONNX model
onnx_model_path = 'LogisticRegression.onnx'
with open(onnx_model_path, 'wb') as f:
    f.write(onnx_model.SerializeToString())
    
print(f"ONNX model saved to {onnx_model_path}")