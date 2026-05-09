from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import os
import uuid
import logging
from database import get_db
from models.dataset import Dataset
from models.user import User
from services.data_analysis import analyze_dataset
from services.ai_service import generate_dataset_insights
from core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.get("")
def list_datasets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    datasets = db.query(Dataset).all()
    return [{"id": d.id, "name": d.name, "rows": d.rows, "columns": d.columns,
             "status": d.status, "created": str(d.created_at)[:10],
             "updated": str(d.updated_at)[:10] if d.updated_at else str(d.created_at)[:10]} for d in datasets]

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files supported")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError:
        logger.error("Failed to save uploaded file", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save file")

    try:
        df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
    except Exception:
        os.remove(file_path)
        logger.error("Failed to parse uploaded file", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to parse file")

    dataset = Dataset(name=file.filename, file_path=file_path,
                      rows=len(df), columns=len(df.columns), status="analyzed")
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    analysis = analyze_dataset(df)
    return {"id": dataset.id, "name": dataset.name, "rows": dataset.rows,
            "columns": dataset.columns, "analysis": analysis}

@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"id": ds.id, "name": ds.name, "rows": ds.rows, "columns": ds.columns, "status": ds.status}

@router.get("/{dataset_id}/preview")
def preview_dataset(dataset_id: int, db: Session = Depends(get_db),
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
    return {"columns": list(df.columns), "rows": df.head(100).fillna("").to_dict("records")}

@router.post("/{dataset_id}/analyze")
def analyze(dataset_id: int, db: Session = Depends(get_db),
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
    ds.updated_at = datetime.now()
    db.commit()
    analysis = analyze_dataset(df)
    insights = generate_dataset_insights(analysis)
    return {**analysis, "ai_insights": insights}

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if ds.file_path and os.path.exists(ds.file_path):
        try:
            os.remove(ds.file_path)
        except OSError:
            pass
    db.delete(ds)
    db.commit()
    return {"message": "Dataset deleted"}
