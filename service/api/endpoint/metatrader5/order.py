from fastapi import APIRouter, Body
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from api.error import Mt5Error
from api.response import response_success, response_error
from mt5_terminal import (
    orders_total as mt5_orders_total,
    orders_get as mt5_orders_get,
    order_calc_margin as mt5_order_calc_margin,
    order_calc_profit as mt5_order_calc_profit,
    order_check as mt5_order_check,
    order_send as mt5_order_send,
    history_orders_total as mt5_history_orders_total,
    history_orders_get as mt5_history_orders_get,
    history_deals_total as mt5_history_deals_total,
    history_deals_get as mt5_history_deals_get,
)
from terminal_utils import get_last_error
from api.utils import check_init, parse_datetime


class CalcMarginRequest(BaseModel):
    action: int
    symbol: str
    volume: float
    price: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "action": 0,
                "symbol": "EURUSD",
                "volume": 0.1,
                "price": 1.1234,
            }
        }
    }


class CalcProfitRequest(BaseModel):
    action: int
    symbol: str
    volume: float
    price_open: float
    price_close: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "action": 0,
                "symbol": "EURUSD",
                "volume": 0.1,
                "price_open": 1.1000,
                "price_close": 1.1100,
            }
        }
    }


class TradeRequest(BaseModel):
    action: int
    symbol: Optional[str] = None
    volume: Optional[float] = None
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: Optional[int] = None
    type: Optional[int] = None
    type_filling: Optional[int] = None
    type_time: Optional[int] = None
    expiration: Optional[int] = None
    comment: Optional[str] = None
    position: Optional[int] = None
    position_by: Optional[int] = None
    order: Optional[int] = None
    magic: Optional[int] = None
    stoplimit: Optional[float] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 0,
                "price": 1.1234,
                "sl": 1.1100,
                "tp": 1.1400,
                "deviation": 10,
                "magic": 234000,
                "comment": "python script open",
                "type_filling": 2,
                "type_time": 0,
            }
        }
    }


def _to_list(result):
    if result is None:
        return None
    return [item._asdict() if hasattr(item, "_asdict") else item for item in result]


class OrdersGetRequest(BaseModel):
    symbol: Optional[str] = None
    group: Optional[str] = None
    ticket: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {"symbol": "EURUSD"}
        }
    }


class HistoryDateRequest(BaseModel):
    date_from: str
    date_to: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "date_from": "2024-01-01T00:00:00",
                "date_to": "2024-02-01T00:00:00",
            }
        }
    }


class HistoryGetRequest(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    group: Optional[str] = None
    ticket: Optional[int] = None
    position: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "date_from": "2024-01-01T00:00:00",
                "date_to": "2024-02-01T00:00:00",
            }
        }
    }


def _trade_request_to_dict(payload: TradeRequest) -> dict:
    return {k: v for k, v in payload.model_dump().items() if v is not None}


def create_router(terminal):
    router = APIRouter(tags=["order"], prefix="/metatrader5")

    # ── Active orders ──────────────────────────────────────────────────────────

    @router.get("/orders_total")
    async def orders_total():
        """Get the total number of active pending orders."""
        err = check_init(terminal)
        if err:
            return err
        try:
            return response_success({"total": mt5_orders_total(terminal)})
        except Exception as e:
            return response_error(Exception(f"Get orders total failed: {e}"), status_code=500)

    @router.post("/orders_get")
    async def orders_get(payload: OrdersGetRequest = Body(...)):
        """
        Get active pending orders, optionally filtered by symbol, group or ticket.
        Only one filter parameter is applied at a time (symbol > group > ticket).
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_orders_get(terminal, symbol=payload.symbol, group=payload.group, ticket=payload.ticket)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_to_list(result))
        except Exception as e:
            return response_error(Exception(f"Get orders failed: {e}"), status_code=500)

    # ── Order calculation ──────────────────────────────────────────────────────

    @router.post("/order_calc_margin")
    async def order_calc_margin(payload: CalcMarginRequest = Body(...)):
        """Calculate the margin required for a potential order."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_order_calc_margin(terminal, payload.action, payload.symbol, payload.volume, payload.price)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success({"margin": result})
        except Exception as e:
            return response_error(Exception(f"Calc margin failed: {e}"), status_code=500)

    @router.post("/order_calc_profit")
    async def order_calc_profit(payload: CalcProfitRequest = Body(...)):
        """Calculate the profit for a potential order."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_order_calc_profit(
                terminal, payload.action, payload.symbol, payload.volume,
                payload.price_open, payload.price_close
            )
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success({"profit": result})
        except Exception as e:
            return response_error(Exception(f"Calc profit failed: {e}"), status_code=500)

    @router.post("/order_check")
    async def order_check(payload: TradeRequest = Body(...)):
        """Check whether a trade request is valid before sending."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_order_check(terminal, _trade_request_to_dict(payload))
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(result)
        except Exception as e:
            return response_error(Exception(f"Order check failed: {e}"), status_code=500)

    @router.post("/order_send")
    async def order_send(payload: TradeRequest = Body(...)):
        """Send a trade request to the server."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_order_send(terminal, _trade_request_to_dict(payload))
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(result)
        except Exception as e:
            return response_error(Exception(f"Order send failed: {e}"), status_code=500)

    # ── History orders ─────────────────────────────────────────────────────────

    @router.post("/history_orders_total")
    async def history_orders_total(payload: HistoryDateRequest = Body(...)):
        """
        Get the total number of orders in trading history for a date range.

        - **date_from**: ISO 8601 datetime string
        - **date_to**: ISO 8601 datetime string
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            dt_from = parse_datetime(payload.date_from)
            dt_to = parse_datetime(payload.date_to)
            return response_success({"total": mt5_history_orders_total(terminal, dt_from, dt_to)})
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"Get history orders total failed: {e}"), status_code=500)

    @router.post("/history_orders_get")
    async def history_orders_get(payload: HistoryGetRequest = Body(...)):
        """
        Get orders from trading history.

        Filter by ticket or position (no dates needed), or by date range with optional group.
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            dt_from = parse_datetime(payload.date_from) if payload.date_from else None
            dt_to = parse_datetime(payload.date_to) if payload.date_to else None
            result = mt5_history_orders_get(
                terminal,
                date_from=dt_from,
                date_to=dt_to,
                group=payload.group,
                ticket=payload.ticket,
                position=payload.position,
            )
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_to_list(result))
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"Get history orders failed: {e}"), status_code=500)

    # ── History deals ──────────────────────────────────────────────────────────

    @router.post("/history_deals_total")
    async def history_deals_total(payload: HistoryDateRequest = Body(...)):
        """
        Get the total number of deals in trading history for a date range.

        - **date_from**: ISO 8601 datetime string
        - **date_to**: ISO 8601 datetime string
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            dt_from = parse_datetime(payload.date_from)
            dt_to = parse_datetime(payload.date_to)
            return response_success({"total": mt5_history_deals_total(terminal, dt_from, dt_to)})
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"Get history deals total failed: {e}"), status_code=500)

    @router.post("/history_deals_get")
    async def history_deals_get(payload: HistoryGetRequest = Body(...)):
        """
        Get deals from trading history.

        Filter by ticket or position (no dates needed), or by date range with optional group.
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            dt_from = parse_datetime(payload.date_from) if payload.date_from else None
            dt_to = parse_datetime(payload.date_to) if payload.date_to else None
            result = mt5_history_deals_get(
                terminal,
                date_from=dt_from,
                date_to=dt_to,
                group=payload.group,
                ticket=payload.ticket,
                position=payload.position,
            )
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_to_list(result))
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"Get history deals failed: {e}"), status_code=500)

    return router
