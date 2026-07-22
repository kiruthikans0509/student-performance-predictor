from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
import joblib

# ---------- Pydantic Models ----------

class StudentInput(BaseModel):
    hours_studied: int = Field(..., ge=1, le=9)
    previous_scores: int = Field(..., ge=40, le=99)
    extracurricular: str = Field(..., pattern="^(Yes|No)$")
    sleep_hours: int = Field(..., ge=4, le=9)
    sample_papers: int = Field(..., ge=0, le=9)


class StudentUpdate(BaseModel):
    hours_studied: int | None = Field(None, ge=1, le=9)
    previous_scores: int | None = Field(None, ge=40, le=99)
    extracurricular: str | None = Field(None, pattern="^(Yes|No)$")
    sleep_hours: int | None = Field(None, ge=4, le=9)
    sample_papers: int | None = Field(None, ge=0, le=9)


class StudentOutput(BaseModel):
    grade: str
    pass_fail: str
    performance_level: str


class PredictionRecord(BaseModel):
    id: int
    input: StudentInput
    output: StudentOutput


# ---------- Load model + encoders ----------

model = joblib.load("student_predict.pkl")
le_grade = joblib.load("le_grade.pkl")
le_pass = joblib.load("le_pass.pkl")
le_perf = joblib.load("le_perf.pkl")

# ---------- In-memory storage ----------

predictions_db: dict[int, PredictionRecord] = {}
next_id = 1

# ---------- App ----------

app = FastAPI(title="Student Performance Predictor")


def run_prediction(student: StudentInput) -> StudentOutput:
    extra = 1 if student.extracurricular == "Yes" else 0
    input_data = [[
        student.hours_studied,
        student.previous_scores,
        extra,
        student.sleep_hours,
        student.sample_papers
    ]]
    prediction = model.predict(input_data)[0]
    grade = le_grade.inverse_transform([prediction[0]])[0]
    pass_fail = le_pass.inverse_transform([prediction[1]])[0]
    performance = le_perf.inverse_transform([prediction[2]])[0]
    return StudentOutput(grade=grade, pass_fail=pass_fail, performance_level=performance)


# ---------- POST: create a new prediction ----------

@app.post("/predict", response_model=PredictionRecord)
def predict(student: StudentInput):
    global next_id
    output = run_prediction(student)
    record = PredictionRecord(id=next_id, input=student, output=output)
    predictions_db[next_id] = record
    next_id += 1
    return record


# ---------- GET: list all predictions ----------

@app.get("/predictions", response_model=list[PredictionRecord])
def list_predictions():
    return list(predictions_db.values())


# ---------- GET: fetch one prediction by ID ----------

@app.get("/predictions/{prediction_id}", response_model=PredictionRecord)
def get_prediction(prediction_id: int):
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return predictions_db[prediction_id]


# ---------- PUT: replace an entire prediction's input, re-run model ----------

@app.put("/predictions/{prediction_id}", response_model=PredictionRecord)
def replace_prediction(prediction_id: int, student: StudentInput):
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    output = run_prediction(student)
    record = PredictionRecord(id=prediction_id, input=student, output=output)
    predictions_db[prediction_id] = record
    return record


# ---------- PATCH: update part of a prediction's input, re-run model ----------

@app.patch("/predictions/{prediction_id}", response_model=PredictionRecord)
def update_prediction(prediction_id: int, update: StudentUpdate):
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")

    existing = predictions_db[prediction_id]
    updated_data = existing.input.model_copy(update=update.model_dump(exclude_unset=True))

    output = run_prediction(updated_data)
    record = PredictionRecord(id=prediction_id, input=updated_data, output=output)
    predictions_db[prediction_id] = record
    return record


# ---------- DELETE: remove a prediction ----------

@app.delete("/predictions/{prediction_id}")
def delete_prediction(prediction_id: int):
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    del predictions_db[prediction_id]
    return {"message": f"Prediction {prediction_id} deleted"}