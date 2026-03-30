import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.response import response_error, response_success
from mt5_runtime import DEFAULT_TERMINAL_PATH, get_account_info_data, initialize_terminal, login_terminal
from service_state import (
    SERVICE_STATUS_MANUAL_LOGIN_FAILED,
    SERVICE_STATUS_NEEDS_MANUAL_LOGIN,
    SERVICE_STATUS_READY,
    SERVICE_REASON_USER_CONFIG_UPLOAD_FAILED,
    get_service_status,
    set_service_status,
)
from user_config import UserConfigUploadError, upload_current_user_config


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
                "already_ready": True,
                "service_status": service_status,
            })

        if current_status == SERVICE_STATUS_MANUAL_LOGIN_FAILED:
            return response_error(
                -1,
                "Manual login terminal launch failed.",
                {"service_status": service_status},
            )

        if current_status != SERVICE_STATUS_NEEDS_MANUAL_LOGIN:
            return response_error(
                -1,
                "Service is not waiting for manual login confirmation.",
                {"service_status": service_status},
            )

        logger.info("confirm_manual_login requested for login=%s server=%s", payload.login, payload.server)

        initialized, initialize_error, terminal_path, portable = initialize_terminal(
            terminal,
            terminal_path=DEFAULT_TERMINAL_PATH,
            portable=True,
            launch_if_needed=False,
        )
        if not initialized:
            return response_error(
                initialize_error[0],
                initialize_error[1],
                {"service_status": get_service_status(request.app)},
            )

        login_ok, login_error = login_terminal(
            terminal,
            login=payload.login,
            password=payload.password,
            server=payload.server,
        )
        if not login_ok:
            return response_error(
                login_error[0],
                login_error[1],
                {"service_status": get_service_status(request.app)},
            )

        account_info_ok, account_info, account_info_error = get_account_info_data(terminal)
        if not account_info_ok:
            return response_error(
                account_info_error[0],
                account_info_error[1],
                {"service_status": get_service_status(request.app)},
            )

        try:
            upload_settings = upload_current_user_config()
        except UserConfigUploadError as exc:
            updated_service_status = set_service_status(
                request.app,
                status=SERVICE_STATUS_READY,
                reason=SERVICE_REASON_USER_CONFIG_UPLOAD_FAILED,
                message="Manual login confirmed, but failed to upload Config.zip to S3.",
                manual_login_required=False,
            )
            logger.error("failed to upload Config.zip after manual login: %s", exc)
            return response_error(
                -1,
                str(exc),
                {"service_status": updated_service_status},
            )

        updated_service_status = set_service_status(
            request.app,
            status=SERVICE_STATUS_READY,
            reason=None,
            message="Manual login confirmed and Config.zip uploaded to S3.",
            manual_login_required=False,
        )
        logger.info(
            "manual login confirmed, terminal_path=%s portable=%s login=%s server=%s uploaded_key=%s",
            terminal_path,
            portable,
            payload.login,
            payload.server,
            upload_settings.object_key,
        )
        return response_success({
            "confirmed": True,
            "initialized": True,
            "logged_in": True,
            "account_info": account_info,
            "service_status": updated_service_status,
        })

    return router
