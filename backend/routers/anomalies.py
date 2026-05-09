from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
import os
import logging
from services.stock_service import get_stock_data
from services.anomaly_detection import detect_stock_anomalies
from database import get_db
from models.dataset import Dataset
from models.user import User
from core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])

@router.post("/{symbol}")
def detect_stock_anomalies_endpoint(symbol: str, current_user: User = Depends(get_current_user)):
    stock_data = get_stock_data(symbol.upper(), period="1y")
    if "error" in stock_data:
        raise HTTPException(status_code=404, detail=stock_data["error"])
    result = detect_stock_anomalies(stock_data["data"])
    prices = [{"date": d["date"], "close": d["close"]} for d in stock_data["data"][-90:]]
    return {"symbol": symbol.upper(), "prices": prices, **result}

@router.post("/dataset/{dataset_id}")
def detect_dataset_anomalies(dataset_id: int, db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds or not os.path.exists(ds.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")
    ext = os.path.splitext(ds.file_path)[1].lower()
    try:
        df = pd.read_csv(ds.file_path) if ext == ".csv" else pd.read_excel(ds.file_path)
    except Exception:
        logger.error("Failed to read dataset file", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read file")
    anomalies = []
    for col in df.select_dtypes(include=[np.number]).columns:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
        for _, row in outliers.iterrows():
            val = row[col]
            if not pd.isna(val):
                anomalies.append({"column": col, "value": float(val), "type": "Statistical Outlier"})
    return {"dataset_id": dataset_id, "total": len(anomalies), "anomalies": anomalies[:50]}
