from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from services.stock_service import get_stock_data
from services.forecasting import forecast_stock
from models.user import User
from core.dependencies import get_current_user

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

class ForecastRequest(BaseModel):
    horizon: int = Field(30, gt=0, le=90)
    confidence_interval: float = Field(0.95, ge=0.5, le=0.99)

@router.post("/{symbol}")
def generate_forecast(symbol: str, req: ForecastRequest, current_user: User = Depends(get_current_user)):
    sym = symbol.upper()
    stock_data = get_stock_data(sym, period="2y")
    if "error" in stock_data:
        raise HTTPException(status_code=404, detail=stock_data["error"])
    result = forecast_stock(stock_data["data"], horizon=req.horizon, symbol=sym)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {
        "symbol": sym,
        "horizon": req.horizon,
        "historical": stock_data["data"][-90:],
        **result,
    }
