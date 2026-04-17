from datetime import datetime

import pytz

from api.response import response_error
from terminal_utils import is_initialized


UTC_TIMEZONE = pytz.timezone("Etc/UTC")


def check_init(terminal):
    if not is_initialized(terminal):
        return response_error(ValueError("terminal is not initialized; call /initialize first"), status_code=409)
    return None


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return UTC_TIMEZONE.localize(parsed)
    return parsed.astimezone(UTC_TIMEZONE)
