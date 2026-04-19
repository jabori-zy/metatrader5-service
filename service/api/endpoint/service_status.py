import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.error import Mt5Error
from api.response import response_error, response_success
from mt5_terminal import account_info, initialize, terminal_info
from terminal_utils import DEFAULT_TERMINAL_PATH, check_terminal_path_format, get_last_error
from service_state import (
    SERVICE_STATUS_READY,
    SERVICE_STATUS_WAITING_MANUAL_LOGIN,
    get_service_status,
    set_service_status,
)


class ConfirmManualLoginRequest(BaseModel):
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
    router = APIRouter(tags=["service"])
    logger = logging.getLogger("MetaTrader5-service.service")

    @router.get("/service_status")
    async def service_status(request: Request):
        """
        Get the current service state.
        """
        return response_success(get_service_status(request.app))

    @router.post("/confirm_manual_login")
    async def confirm_manual_login(request: Request, payload: ConfirmManualLoginRequest):
        """
        Confirm that manual login completed and validate terminal readiness.
        """
        service_status = get_service_status(request.app)
        current_status = service_status["status"]

        if current_status == SERVICE_STATUS_READY:
            return response_success({
                "confirmed": True,
                "service_status": service_status,
            })

        if current_status != SERVICE_STATUS_WAITING_MANUAL_LOGIN:
            return response_error(
                ValueError("Service is not waiting for manual login confirmation."),
                extra={"service_status": service_status},
                status_code=409,
            )

        logger.info("confirm_manual_login requested for login=%s server=%s", payload.login, payload.server)

        try:
            terminal_path = check_terminal_path_format(DEFAULT_TERMINAL_PATH)
        except ValueError as exc:
            return response_error(
                exc,
                extra={"service_status": get_service_status(request.app)},
                status_code=422,
            )

        portable = True
        initialized = initialize(
            terminal,
            terminal_path=terminal_path,
            portable=portable,
            login=payload.login,
            password=payload.password,
            server=payload.server,
        )
        if not initialized:
            last_error = get_last_error(terminal)
            return response_error(
                Mt5Error(last_error[0], last_error[1]),
            )

        info = account_info(terminal)
        if info is None:
            account_info_error = get_last_error(terminal)
            return response_error(
                Mt5Error(account_info_error[0], account_info_error[1]),
            )

        t_info = terminal_info(terminal)
        if t_info is None:
            t_info_error = get_last_error(terminal)
            return response_error(
                Mt5Error(t_info_error[0], t_info_error[1]),
            )
        if not t_info.get("trade_allowed", False):
            return response_error(
                ValueError("Algo Trading is not enabled."),
                status_code=403,
            )

        updated_service_status = set_service_status(
            request.app,
            status=SERVICE_STATUS_READY,
            reason=None,
            message="Manual login confirmed and account is ready.",
            manual_login_required=False,
        )
        logger.info(
            "manual login confirmed, terminal_path=%s portable=%s login=%s server=%s",
            terminal_path,
            portable,
            payload.login,
            payload.server,
        )
        return response_success({
            "confirmed": True,
            "service_status": updated_service_status,
        })

    return router
