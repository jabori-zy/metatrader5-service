from fastapi import APIRouter, Body
from typing import Optional
import logging
import os
import subprocess
import time
from pydantic import BaseModel
from api.response import response_success, response_error

DEFAULT_TERMINAL_PATH = "C:/Program Files/MetaTrader 5/terminal64.exe"
DEFAULT_TERMINAL_PATH_LINUX = "/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
INITIALIZE_TIMEOUT_SECONDS = 60
LAUNCH_MT5_SCRIPT = "/scripts/runtime/launch-mt5.sh"


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


def is_terminal_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-fa", "terminal64.exe"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def windows_to_linux_terminal_path(terminal_path: str) -> str:
    normalized = terminal_path.replace("\\", "/")
    if normalized == DEFAULT_TERMINAL_PATH:
        return DEFAULT_TERMINAL_PATH_LINUX
    return normalized


def launch_mt5(terminal_path: str, portable: bool) -> tuple[bool, str]:
    env = os.environ.copy()
    env["MT5_TERMINAL_PATH"] = windows_to_linux_terminal_path(terminal_path)
    env["MT5_PORTABLE"] = "true" if portable else "false"
    result = subprocess.run(
        ["bash", LAUNCH_MT5_SCRIPT],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        error_message = result.stderr.strip() or result.stdout.strip() or "launch-mt5.sh failed"
        return False, error_message
    return True, result.stdout.strip()


def wait_for_terminal_process(timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_terminal_running():
            return True
        time.sleep(1)
    return False



def create_router(terminal):
    router = APIRouter(tags=["account"])
    logger = logging.getLogger("MetaTrader5-service.account")

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
                logger.info(
                    "initialize requested, terminal_path=%s portable=%s running=%s",
                    terminal_path,
                    portable,
                    is_terminal_running(),
                )
                launch_ok, launch_message = launch_mt5(terminal_path, portable)
                if not launch_ok:
                    return response_error(-1, f"Launch terminal failed: {launch_message}")

                if not wait_for_terminal_process(INITIALIZE_TIMEOUT_SECONDS):
                    return response_error(
                        -1,
                        f"Timed out waiting for terminal64.exe after {INITIALIZE_TIMEOUT_SECONDS}s",
                    )

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
