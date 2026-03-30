import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI

SERVICE_STATUS_STARTING = "STARTING"
SERVICE_STATUS_PULLING_USER_CONFIG = "PULLING_USER_CONFIG"
SERVICE_STATUS_NEEDS_MANUAL_LOGIN = "NEEDS_MANUAL_LOGIN"
SERVICE_STATUS_READY = "READY"
SERVICE_STATUS_ERROR = "ERROR"

SERVICE_STATUSES = [
    SERVICE_STATUS_STARTING,
    SERVICE_STATUS_PULLING_USER_CONFIG,
    SERVICE_STATUS_NEEDS_MANUAL_LOGIN,
    SERVICE_STATUS_READY,
    SERVICE_STATUS_ERROR,
]

SERVICE_REASON_USER_CONFIG_NOT_FOUND = "USER_CONFIG_NOT_FOUND"
SERVICE_REASON_STARTUP_CHECK_FAILED = "SERVICE_STARTUP_CHECK_FAILED"


def _now_isoformat() -> str:
    return datetime.now().isoformat()


def build_service_status(
    status: str,
    reason: Optional[str],
    message: Optional[str],
    manual_login_required: bool,
) -> dict:
    return {
        "status": status,
        "reason": reason,
        "message": message,
        "manual_login_required": manual_login_required,
        "updated_at": _now_isoformat(),
        "all_statuses": SERVICE_STATUSES,
    }


def initialize_service_status(app: FastAPI) -> None:
    app.state.service_status = build_service_status(
        status=SERVICE_STATUS_STARTING,
        reason=None,
        message="Service is starting.",
        manual_login_required=False,
    )


def get_service_status(app: FastAPI) -> dict:
    service_status = getattr(app.state, "service_status", None)
    if service_status is None:
        initialize_service_status(app)
        service_status = app.state.service_status
    return service_status


def set_service_status(
    app: FastAPI,
    status: str,
    reason: Optional[str],
    message: Optional[str],
    manual_login_required: bool,
) -> dict:
    app.state.service_status = build_service_status(
        status=status,
        reason=reason,
        message=message,
        manual_login_required=manual_login_required,
    )
    return app.state.service_status


async def run_service_startup_check(app: FastAPI) -> None:
    try:
        set_service_status(
            app,
            status=SERVICE_STATUS_PULLING_USER_CONFIG,
            reason=None,
            message="Pulling user config.",
            manual_login_required=False,
        )
        await asyncio.sleep(0.1)
        set_service_status(
            app,
            status=SERVICE_STATUS_NEEDS_MANUAL_LOGIN,
            reason=SERVICE_REASON_USER_CONFIG_NOT_FOUND,
            message="User config not found in S3. Manual login is required.",
            manual_login_required=True,
        )
    except Exception as exc:
        set_service_status(
            app,
            status=SERVICE_STATUS_ERROR,
            reason=SERVICE_REASON_STARTUP_CHECK_FAILED,
            message=str(exc),
            manual_login_required=False,
        )
