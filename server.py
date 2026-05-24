"""
server.py — Obesity Risk Prediction API v3
Endpoints:
  POST /predict/core6    — Core_6feat  (6 fields,  Binary F1=0.608)
  POST /predict/behav15  — Behav_15feat (15 fields, Binary F1=0.680)
"""

import os
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Model paths ───────────────────────────────────────────────
MODEL_DIR = "models_binary"

models = {}
feature_cols = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    models["core6"]   = joblib.load(f"{MODEL_DIR}/model_core.pkl")
    models["behav15"] = joblib.load(f"{MODEL_DIR}/model_behav.pkl")
    feature_cols["core6"]   = joblib.load(f"{MODEL_DIR}/feature_cols_Core_6feat.pkl")
    feature_cols["behav15"] = joblib.load(f"{MODEL_DIR}/feature_cols_Behav_15feat.pkl")
    yield

# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="Obesity Risk Prediction API",
    version="3.0",
    description="Binary prediction: Normal (BMI<25) vs Overweight+Obese (BMI≥25). "
                "Model trained on CDC BRFSS 2022, n=329,126.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Request schemas ───────────────────────────────────────────
class Core6Request(BaseModel):
    sleep_hours:      float = Field(..., ge=1.0,  le=24.0, description="每日平均睡眠時數 (1–24)")
    smoking_status:   int   = Field(..., ge=1,    le=4,    description="1=每日 2=偶爾 3=已戒 4=從未")
    drank_any:        int   = Field(..., ge=0,    le=1,    description="近30天是否飲酒 0=否 1=是")
    drinks_per_week:  float = Field(..., ge=0.0,           description="每週飲酒杯數 (≥0)")
    exercised:        int   = Field(..., ge=0,    le=1,    description="近30天是否運動 0=否 1=是")
    general_health:   int   = Field(..., ge=1,    le=5,    description="自評健康 1=最好 5=最差")

    class Config:
        json_schema_extra = {
            "example": {
                "sleep_hours": 7.0,
                "smoking_status": 4,
                "drank_any": 1,
                "drinks_per_week": 3.5,
                "exercised": 1,
                "general_health": 2
            }
        }


class Behav15Request(BaseModel):
    # Life habits (5)
    sleep_hours:           float = Field(..., ge=1.0,  le=24.0)
    smoking_status:        int   = Field(..., ge=1,    le=4)
    drank_any:             int   = Field(..., ge=0,    le=1)
    drinks_per_week:       float = Field(..., ge=0.0)
    exercised:             int   = Field(..., ge=0,    le=1)
    # Health status (5)
    general_health:        int   = Field(..., ge=1,    le=5,   description="1=Excellent 5=Poor")
    mental_health_days:    int   = Field(..., ge=0,    le=30,  description="近30天心理不健康天數")
    physical_health_days:  int   = Field(..., ge=0,    le=30,  description="近30天身體不健康天數")
    diff_walking:          int   = Field(..., ge=0,    le=1,   description="行走困難 0=否 1=是")
    depression:            int   = Field(..., ge=0,    le=1,   description="曾診斷憂鬱症 0=否 1=是")
    # Demographics (5)
    sex:                   int   = Field(..., ge=0,    le=1,   description="0=Female 1=Male")
    age_group:             int   = Field(..., ge=1,    le=13,  description="1=18-24 … 13=80+")
    education:             int   = Field(..., ge=1,    le=6,   description="1=未受教育 … 6=大學以上")
    income:                int   = Field(..., ge=1,    le=8,   description="1=<$15k … 8=≥$200k")
    employment:            int   = Field(..., ge=1,    le=8,   description="1=全職 … 8=失業")

    class Config:
        json_schema_extra = {
            "example": {
                "sleep_hours": 6.5,
                "smoking_status": 4,
                "drank_any": 1,
                "drinks_per_week": 7.0,
                "exercised": 0,
                "general_health": 3,
                "mental_health_days": 5,
                "physical_health_days": 2,
                "diff_walking": 0,
                "depression": 0,
                "sex": 0,
                "age_group": 4,
                "education": 6,
                "income": 5,
                "employment": 1
            }
        }


# ── Shared predict helper ─────────────────────────────────────
def run_predict(model_key: str, data: dict) -> dict:
    model = models[model_key]
    cols  = feature_cols[model_key]
    df    = pd.DataFrame([data])[cols]
    pred  = int(model.predict(df)[0])
    proba = model.predict_proba(df)[0]
    return {
        "model":      model_key,
        "prediction": pred,
        "label":      "Normal" if pred == 0 else "Overweight+Obese",
        "probability": {
            "normal":           round(float(proba[0]), 4),
            "overweight_obese": round(float(proba[1]), 4),
        },
    }


# ── Endpoints ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "version": "3.0", "models": list(models.keys())}


@app.post("/predict/core6", tags=["Predict"])
def predict_core6(req: Core6Request):
    """
    輕量版預測（6 欄位）。Weighted F1 = 0.608。
    適合只有基本生活習慣資料的場景。
    """
    try:
        return run_predict("core6", req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/behav15", tags=["Predict"])
def predict_behav15(req: Behav15Request):
    """
    完整行為版預測（15 欄位）。Weighted F1 = 0.680。
    包含生活習慣、健康狀態、人口統計，準確度最高（不含慢性病史）。
    """
    try:
        return run_predict("behav15", req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
