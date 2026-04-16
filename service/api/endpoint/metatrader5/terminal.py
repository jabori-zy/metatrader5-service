from fastapi import APIRouter, Body, Request
from typing import Optional
from pydantic import BaseModel
from api.error import Mt5Error
from api.response import response_success, response_error
from mt5_terminal import (
    initialize as terminal_initialize,
    login as terminal_login,
    terminal_info as mt5_terminal_info,
    shutdown as mt5_shutdown,
    version as mt5_version,
)
from terminal_utils import check_terminal_path_format, get_last_error, is_initialized
from service_state import SERVICE_STATUS_READY, get_service_status


class InitializeRequest(BaseModel):
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None
    terminal_path: Optional[str] = None
    portable: Optional[bool] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "login": 51236,
                "password": "HhazJ520....",
                "server": "EBCFinancialGroupKY-Demo",
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
    router = APIRouter(tags=["terminal"], prefix="/metatrader5")

    @router.post("/initialize")
    async def initialize(request: Request, payload: InitializeRequest = Body(...)):
        """
        Initialize MetaTrader 5 runtime and login immediately.
        """
        terminal_path = payload.terminal_path
        portable = True
        if payload.portable is not None:
            portable = payload.portable

        try:
            service_status = get_service_status(request.app)
            if service_status["status"] != SERVICE_STATUS_READY:
                return response_error(
                    ValueError("Service is not ready for MT5 initialization."),
                    extra={"service_status": service_status},
                    status_code=503,
                )

            try:
                terminal_path = check_terminal_path_format(terminal_path)
            except ValueError as exc:
                return response_error(exc, status_code=422)

            initialized = terminal_initialize(
                terminal,
                terminal_path=terminal_path,
                portable=portable,
                login=payload.login,
                password=payload.password,
                server=payload.server,
            )
            if not initialized:
                last_error = get_last_error(terminal)
                return response_error(Mt5Error(last_error[0], last_error[1]))

            return response_success({
                "initialized": True,
                "login": payload.login,
                "server": payload.server,
                "portable": portable,
                "terminal_path": terminal_path,
            })
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"Initialize terminal failed: {e}"), status_code=500)

    @router.post("/login")
    async def login(payload: LoginRequest):
        """
        Login to a specific MT5 account after initialization.
        """
        try:
            if not is_initialized(terminal):
                return response_error(ValueError("terminal is not initialized; call /initialize first"), status_code=409)

            login_result = terminal_login(
                terminal,
                login=payload.login,
                password=payload.password,
                server=payload.server,
            )
            # loging failed
            if not login_result:
                login_error = get_last_error(terminal)
                return response_error(Mt5Error(login_error[0], login_error[1]))

            return response_success({
                "logged_in": True,
                "login": payload.login,
                "server": payload.server,
            })
        except Exception as e:
            return response_error(Exception(f"Login failed: {e}"), status_code=500)

    @router.get("/terminal_info")
    async def get_terminal_info():
        """
        Get MetaTrader 5 terminal information.
        """
        try:
            if not is_initialized(terminal):
                return response_error(ValueError("terminal is not initialized; call /initialize first"), status_code=409)
            info = mt5_terminal_info(terminal)
            if info is None:
                err = get_last_error(terminal)
                return response_error(Mt5Error(err[0], err[1]))
            return response_success(info)
        except Exception as e:
            return response_error(Exception(f"Get terminal info failed: {e}"), status_code=500)

    @router.post("/shutdown")
    async def shutdown():
        """
        Shutdown the MetaTrader 5 terminal connection.
        """
        try:
            if not is_initialized(terminal):
                return response_error(ValueError("terminal is not initialized"), status_code=409)
            mt5_shutdown(terminal)
            return response_success({"shutdown": True})
        except Exception as e:
            return response_error(Exception(f"Shutdown failed: {e}"), status_code=500)

    @router.get("/version")
    async def get_version():
        """
        Get MetaTrader 5 terminal version info.
        """
        try:
            if not is_initialized(terminal):
                return response_error(ValueError("terminal is not initialized; call /initialize first"), status_code=409)
            ver = mt5_version(terminal)
            if ver is None:
                err = get_last_error(terminal)
                return response_error(Mt5Error(err[0], err[1]))
            return response_success({"version": ver})
        except Exception as e:
            return response_error(Exception(f"Get version failed: {e}"), status_code=500)

    return router
