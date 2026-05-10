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
async def generate_forecast(symbol: str, req: ForecastRequest, current_user: User = Depends(get_current_user)):
    import asyncio
    from services.forecasting import _statistical_fallback
    sym = symbol.upper()
    stock_data = await get_stock_data(sym, period="2y")
    if "error" in stock_data:
        raise HTTPException(status_code=404, detail=stock_data["error"])
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, forecast_stock, stock_data["data"], req.horizon, sym),
            timeout=25.0,
        )
    except asyncio.TimeoutError:
        result = _statistical_fallback(stock_data["data"], req.horizon)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {
        "symbol": sym,
        "horizon": req.horizon,
        "historical": stock_data["data"][-90:],
        **result,
    }
