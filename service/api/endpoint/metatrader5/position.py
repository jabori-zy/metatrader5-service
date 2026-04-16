from fastapi import APIRouter, Body
from typing import Optional
from pydantic import BaseModel
from api.error import Mt5Error
from api.response import response_success, response_error
from mt5_terminal import (
    positions_total as mt5_positions_total,
    positions_get as mt5_positions_get,
)
from terminal_utils import get_last_error
from api.utils import check_init


class PositionsGetRequest(BaseModel):
    symbol: Optional[str] = None
    group: Optional[str] = None
    ticket: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {"symbol": "EURUSD"}
        }
    }


def create_router(terminal):
    router = APIRouter(tags=["position"], prefix="/metatrader5")

    @router.get("/positions_total")
    async def positions_total():
        """Get the total number of open positions."""
        err = check_init(terminal)
        if err:
            return err
        try:
            return response_success({"total": mt5_positions_total(terminal)})
        except Exception as e:
            return response_error(Exception(f"Get positions total failed: {e}"), status_code=500)

    @router.post("/positions_get")
    async def positions_get(payload: PositionsGetRequest = Body(...)):
        """
        Get open positions, optionally filtered by symbol, group or ticket.
        Only one filter parameter is applied at a time (symbol > group > ticket).
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_positions_get(terminal, symbol=payload.symbol, group=payload.group, ticket=payload.ticket)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(
                [item._asdict() if hasattr(item, "_asdict") else item for item in result]
            )
        except Exception as e:
            return response_error(Exception(f"Get positions failed: {e}"), status_code=500)

    return router
