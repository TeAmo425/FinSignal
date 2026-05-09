import pandas as pd
import numpy as np
from typing import Any

def analyze_dataset(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    missing = df.isnull().sum()
    missing_dict = {col: int(missing[col]) for col in missing.index if missing[col] > 0}

    summary_stats = {}
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            summary_stats[col] = {
                "mean": float(col_data.mean()),
                "std": float(col_data.std()),
                "min": float(col_data.min()),
                "max": float(col_data.max()),
                "median": float(col_data.median()),
                "q25": float(col_data.quantile(0.25)),
                "q75": float(col_data.quantile(0.75)),
            }

    return {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": missing_dict,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "summary_stats": summary_stats,
        "chart_suggestions": suggest_charts(df, numeric_cols, categorical_cols, datetime_cols),
        "preview": df.head(10).fillna("").to_dict("records"),
    }

def suggest_charts(df, numeric_cols, categorical_cols, datetime_cols) -> list:
    suggestions = []
    for col in categorical_cols[:3]:
        suggestions.append({"type": "bar", "x": col, "title": f"Distribution of {col}"})
    for col in numeric_cols[:2]:
        suggestions.append({"type": "histogram", "x": col, "title": f"Histogram of {col}"})
    if datetime_cols and numeric_cols:
        suggestions.append({
            "type": "line",
            "x": datetime_cols[0],
            "y": numeric_cols[0],
            "title": "Time Series"
        })
    if len(numeric_cols) >= 2:
        suggestions.append({
            "type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1],
            "title": "Correlation"
        })
    return suggestions
