from fastapi import APIRouter, Body, Request
from typing import Optional
from pydantic import BaseModel
from api.response import response_success, response_error
from mt5_runtime import (
    DEFAULT_TERMINAL_PATH,
    get_account_info_data,
    initialize_terminal,
    is_initialized,
    login_terminal,
    normalize_terminal_path,
)
from service_state import SERVICE_STATUS_READY, get_service_status


class InitializeRequest(BaseModel):
    terminal_path: Optional[str] = None
    portable: Optional[bool] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "terminal_path": "C:/Program Files/MetaTrader 5/terminal64.exe",
                "portable": True,
            }
        }
    }


class LoginRequest(BaseModel):
    login: int
    password: str
    server: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "login": 51236,
                "password": "HhazJ520....",
                "server": "EBCFinancialGroupKY-Demo",
            }
        }
    }

def create_router(terminal):
    router = APIRouter(tags=["account"])

    @router.post("/initialize")
    async def initialize(request: Request, payload: Optional[InitializeRequest] = Body(default=None)):
        """
        Initialize MetaTrader 5 runtime.
        """
        terminal_path = DEFAULT_TERMINAL_PATH
        portable = True
        if payload:
            terminal_path = normalize_terminal_path(payload.terminal_path)
        if payload and payload.portable is not None:
            portable = payload.portable

        try:
            service_status = get_service_status(request.app)
            if service_status["status"] != SERVICE_STATUS_READY:
                return response_error(
                    -1,
                    "Service is not ready for MT5 initialization.",
                    {"service_status": service_status},
                )

            initialized, initialize_error, terminal_path, portable = initialize_terminal(
                terminal,
                terminal_path=terminal_path,
                portable=portable,
                launch_if_needed=True,
            )
            if not initialized:
                return response_error(initialize_error[0], initialize_error[1])

            return response_success({
                "initialized": True,
                "portable": portable,
                "terminal_path": terminal_path,
            })
        except Exception as e:
            return response_error(-1, f"Initialize terminal failed: {str(e)}")

    @router.post("/login")
    async def login(payload: LoginRequest):
        """
        Login to a specific MT5 account after initialization.
        """
        try:
            if not is_initialized(terminal):
                return response_error(-1, "terminal is not initialized; call /initialize first")

            login_ok, login_error = login_terminal(
                terminal,
                login=payload.login,
                password=payload.password,
                server=payload.server,
            )
            if not login_ok:
                return response_error(login_error[0], login_error[1])

            return response_success({
                "logged_in": True,
                "login": payload.login,
                "server": payload.server,
            })
        except Exception as e:
            return response_error(-1, f"Login failed: {str(e)}")

    @router.get("/account_info")
    async def get_account_info():
        """
        get account info
        
        get the detailed information of the current MT5 account, including balance, equity, margin, free margin, etc.
        """
        try:
            account_info_ok, account_info, account_info_error = get_account_info_data(terminal)
            if not account_info_ok:
                return response_error(account_info_error[0], account_info_error[1])
            return response_success(account_info)

        except Exception as e:
            return response_error(-1, f"Get account info failed: {str(e)}")
    return router
