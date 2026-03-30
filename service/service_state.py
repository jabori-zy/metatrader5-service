import asyncio
from datetime import datetime
import logging
from typing import Optional
from fastapi import FastAPI
from user_config import (
    AwsCredentialsUnavailableError,
    UserConfigApplyError,
    UserConfigDownloadError,
    UserConfigNotFoundError,
    download_and_apply_user_config,
)

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
SERVICE_REASON_AWS_CREDENTIALS_NOT_AVAILABLE = "AWS_CREDENTIALS_NOT_AVAILABLE"
SERVICE_REASON_USER_CONFIG_DOWNLOAD_FAILED = "USER_CONFIG_DOWNLOAD_FAILED"
SERVICE_REASON_USER_CONFIG_APPLY_FAILED = "USER_CONFIG_APPLY_FAILED"
SERVICE_REASON_STARTUP_CHECK_FAILED = "SERVICE_STARTUP_CHECK_FAILED"

logger = logging.getLogger("MetaTrader5-service.service_state")


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
    logger.info("service status initialized: status=%s", SERVICE_STATUS_STARTING)


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
    previous_status = getattr(getattr(app, "state", None), "service_status", {}).get("status")
    app.state.service_status = build_service_status(
        status=status,
        reason=reason,
        message=message,
        manual_login_required=manual_login_required,
    )
    logger.info(
        "service status updated: from=%s to=%s reason=%s manual_login_required=%s",
        previous_status,
        status,
        reason,
        manual_login_required,
    )
    return app.state.service_status


async def run_service_startup_check(app: FastAPI) -> None:
    try:
        logger.info("service startup check started")
        set_service_status(
            app,
            status=SERVICE_STATUS_PULLING_USER_CONFIG,
            reason=None,
            message="Pulling user config from S3.",
            manual_login_required=False,
        )
        settings = await asyncio.to_thread(download_and_apply_user_config)
        logger.info(
            "user config downloaded and applied, bucket=%s key=%s target=%s",
            settings.s3_bucket_name,
            settings.object_key,
            settings.target_config_dir,
        )
        set_service_status(
            app,
            status=SERVICE_STATUS_READY,
            reason=None,
            message="User config downloaded and applied.",
            manual_login_required=False,
        )
    except UserConfigNotFoundError:
        logger.info("user config not found in S3; manual login is required")
        set_service_status(
            app,
            status=SERVICE_STATUS_NEEDS_MANUAL_LOGIN,
            reason=SERVICE_REASON_USER_CONFIG_NOT_FOUND,
            message="User config not found in S3. Manual login is required.",
            manual_login_required=True,
        )
    except AwsCredentialsUnavailableError as exc:
        logger.error("aws credentials are not available: %s", exc)
        set_service_status(
            app,
            status=SERVICE_STATUS_ERROR,
            reason=SERVICE_REASON_AWS_CREDENTIALS_NOT_AVAILABLE,
            message=str(exc),
            manual_login_required=False,
        )
    except UserConfigDownloadError as exc:
        logger.error("failed to download user config: %s", exc)
        set_service_status(
            app,
            status=SERVICE_STATUS_ERROR,
            reason=SERVICE_REASON_USER_CONFIG_DOWNLOAD_FAILED,
            message=str(exc),
            manual_login_required=False,
        )
    except UserConfigApplyError as exc:
        logger.error("failed to apply user config: %s", exc)
        set_service_status(
            app,
            status=SERVICE_STATUS_ERROR,
            reason=SERVICE_REASON_USER_CONFIG_APPLY_FAILED,
            message=str(exc),
            manual_login_required=False,
        )
    except Exception as exc:
        logger.exception("service startup check failed")
        set_service_status(
            app,
            status=SERVICE_STATUS_ERROR,
            reason=SERVICE_REASON_STARTUP_CHECK_FAILED,
            message=str(exc),
            manual_login_required=False,
        )
