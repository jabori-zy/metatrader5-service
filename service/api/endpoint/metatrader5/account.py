from fastapi import APIRouter
from api.error import Mt5Error
from api.response import response_success, response_error
from mt5_terminal import account_info as mt5_account_info
from terminal_utils import get_last_error, is_initialized


def create_router(terminal):
    router = APIRouter(tags=["account"], prefix="/metatrader5")

    @router.get("/account_info")
    async def get_account_info():
        """
        Get the detailed information of the current MT5 account,
        including balance, equity, margin, free margin, etc.
        """
        try:
            if not is_initialized(terminal):
                return response_error(ValueError("terminal is not initialized; call /initialize first"), status_code=409)
            info = mt5_account_info(terminal)
            if info is None:
                err = get_last_error(terminal)
                return response_error(Mt5Error(err[0], err[1]))
            return response_success(info)
        except Exception as e:
            return response_error(Exception(f"Get account info failed: {e}"), status_code=500)

    return router
