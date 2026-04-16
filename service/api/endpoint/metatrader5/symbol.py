from fastapi import APIRouter, Body
from typing import Optional
from pydantic import BaseModel
from api.error import Mt5Error
from api.response import response_success, response_error

from mt5_terminal import (
    symbols_total as mt5_symbols_total,
    symbols_get as mt5_symbols_get,
    symbol_info as mt5_symbol_info,
    symbol_info_tick as mt5_symbol_info_tick,
    symbol_select as mt5_symbol_select,
    market_book_add as mt5_market_book_add,
    market_book_get as mt5_market_book_get,
    market_book_release as mt5_market_book_release,
)
from terminal_utils import get_last_error
from api.utils import check_init


class SymbolRequest(BaseModel):
    symbol: str

    model_config = {
        "json_schema_extra": {
            "example": {"symbol": "EURUSD"}
        }
    }


class SymbolSelectRequest(BaseModel):
    symbol: str
    enable: Optional[bool] = None

    model_config = {
        "json_schema_extra": {
            "example": {"symbol": "EURUSD", "enable": True}
        }
    }


def create_router(terminal):
    router = APIRouter(tags=["symbol"], prefix="/metatrader5")

    @router.get("/symbols_total")
    async def symbols_total():
        """Get the total number of available symbols."""
        err = check_init(terminal)
        if err:
            return err
        try:
            return response_success({"total": mt5_symbols_total(terminal)})
        except Exception as e:
            return response_error(Exception(f"Get symbols total failed: {e}"), status_code=500)

    @router.get("/symbols_get")
    async def symbols_get(group: Optional[str] = None):
        """Get the list of all symbols, optionally filtered by group."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_symbols_get(terminal, group=group)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success([s._asdict() if hasattr(s, "_asdict") else s for s in result])
        except Exception as e:
            return response_error(Exception(f"Get symbols failed: {e}"), status_code=500)

    @router.get("/symbol_info")
    async def symbol_info(symbol: str):
        """Get information about a specific symbol."""
        err = check_init(terminal)
        if err:
            return err
        try:
            info = mt5_symbol_info(terminal, symbol)
            if info is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(info)
        except Exception as e:
            return response_error(Exception(f"Get symbol info failed: {e}"), status_code=500)

    @router.get("/symbol_info_tick")
    async def symbol_info_tick(symbol: str):
        """Get the latest tick for a specific symbol."""
        err = check_init(terminal)
        if err:
            return err
        try:
            tick = mt5_symbol_info_tick(terminal, symbol)
            if tick is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(tick)
        except Exception as e:
            return response_error(Exception(f"Get symbol tick failed: {e}"), status_code=500)

    @router.post("/symbol_select")
    async def symbol_select(payload: SymbolSelectRequest = Body(...)):
        """Add or remove a symbol from the MarketWatch window."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_symbol_select(terminal, payload.symbol, payload.enable)
            return response_success({"selected": result})
        except Exception as e:
            return response_error(Exception(f"Symbol select failed: {e}"), status_code=500)

    @router.post("/market_book_add")
    async def market_book_add(payload: SymbolRequest = Body(...)):
        """Subscribe to the market depth (DOM) for a symbol."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_market_book_add(terminal, payload.symbol)
            if not result:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success({"subscribed": True, "symbol": payload.symbol})
        except Exception as e:
            return response_error(Exception(f"Market book add failed: {e}"), status_code=500)

    @router.get("/market_book_get")
    async def market_book_get(symbol: str):
        """Get the current market depth (DOM) for a symbol."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_market_book_get(terminal, symbol)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(
                [item._asdict() if hasattr(item, "_asdict") else item for item in result]
            )
        except Exception as e:
            return response_error(Exception(f"Market book get failed: {e}"), status_code=500)

    @router.post("/market_book_release")
    async def market_book_release(payload: SymbolRequest = Body(...)):
        """Unsubscribe from the market depth (DOM) for a symbol."""
        err = check_init(terminal)
        if err:
            return err
        try:
            result = mt5_market_book_release(terminal, payload.symbol)
            if not result:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success({"released": True, "symbol": payload.symbol})
        except Exception as e:
            return response_error(Exception(f"Market book release failed: {e}"), status_code=500)

    return router
