from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import onnxruntime as ort
import joblib, os, re

app = FastAPI(title="Income Prediction API")

# --- load model -----------------------------------------------------------
USE_ONNX = os.getenv("USE_ONNX", "1") == "1"
if USE_ONNX:
    sess = ort.InferenceSession("logreg.onnx", providers=["CPUExecutionProvider"])
    ONNX_INPUTS = [i.name for i in sess.get_inputs()]
else:
    pipe = joblib.load("LogisticRegression.joblib")

# --- helper to match ONNX names ------------------------------------------
def sanitise(col: str) -> str:
    """
    Apply the exact rules skl2onnx uses:
    - replace any char other than [A-Za-z0-9_] with '_'
    - collapse multiple '_' into one
    - strip leading/trailing '_'
    """
    col = re.sub(r"[^0-9A-Za-z_]", "_", col)
    col = re.sub(r"__+", "_", col)
    return col.strip("_")

SANITISED_LOOKUP = {c: sanitise(c) for c in [
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race", "sex",
    "capital-gain", "capital-loss", "hours-per-week", "native-country"
]}

class Record(BaseModel):
    data: dict               # original column names

# --- endpoint -------------------------------------------------------------
@app.post("/predict")
def predict(rec: Record):
    # Build the dict ONNX expects
    input_dict = {}
    for raw_key, val in rec.data.items():
        onnx_key = SANITISED_LOOKUP.get(raw_key)
        if onnx_key is None:
            raise ValueError(f"Unexpected key: {raw_key}")
        # make 2-D array; choose dtype by value type
        arr = np.array([[val]], dtype=np.float32 if isinstance(val, (int, float)) else np.str_)
        input_dict[onnx_key] = arr

    # validate keys → quick guardrail
    missing = set(ONNX_INPUTS) - input_dict.keys()
    if missing:
        raise ValueError(f"Missing keys for ONNX: {missing}")

    # run inference
    if USE_ONNX:
        proba = float(sess.run(None, input_dict)[1][0][1])   # class 1 prob
    else:
        import pandas as pd
        row = pd.DataFrame([rec.data])
        proba = float(pipe.predict_proba(row)[0][1])
    return {"p_gt_50k": proba}
