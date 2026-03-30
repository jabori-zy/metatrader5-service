from fastapi import APIRouter, Body
from typing import Optional
from pydantic import BaseModel
from api.response import response_success, response_error

DEFAULT_TERMINAL_PATH = "C:/Program Files/MetaTrader 5/terminal64.exe"


class InitializeRequest(BaseModel):
    terminal_path: Optional[str] = None
    portable: Optional[bool] = None


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


def get_last_error(terminal) -> tuple[int, str]:
    last_error = terminal.last_error()
    if isinstance(last_error, tuple) and len(last_error) >= 2:
        return int(last_error[0]), str(last_error[1])
    return -1, str(last_error)


def is_initialized(terminal) -> bool:
    return terminal.terminal_info() is not None



def create_router(terminal):
    router = APIRouter(tags=["account"])

    @router.post("/initialize")
    async def initialize(payload: Optional[InitializeRequest] = Body(default=None)):
        """
        Initialize MetaTrader 5 runtime in portable mode.
        """
        terminal_path = DEFAULT_TERMINAL_PATH
        portable = True
        if payload and payload.terminal_path:
            terminal_path = payload.terminal_path
        if payload and payload.portable is not None:
            portable = payload.portable

        try:
            if not is_initialized(terminal):
                init_result = terminal.initialize(terminal_path=terminal_path, portable=portable)
                if not init_result:
                    last_error = get_last_error(terminal)
                    return response_error(last_error[0], last_error[1])

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

            login_result = terminal.login(
                login=payload.login,
                password=payload.password,
                server=payload.server,
            )
            if not login_result:
                last_error = get_last_error(terminal)
                return response_error(last_error[0], last_error[1])

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
            account_info = terminal.account_info()

            if not account_info:
                last_error = get_last_error(terminal)
                return response_error(last_error[0], last_error[1])
            return response_success(account_info._asdict())

        except Exception as e:
            return response_error(-1, f"Get account info failed: {str(e)}")
    return router
