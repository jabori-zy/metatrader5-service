from datetime import datetime

from api.response import response_error
from terminal_utils import is_initialized


def check_init(terminal):
    if not is_initialized(terminal):
        return response_error(ValueError("terminal is not initialized; call /initialize first"), status_code=409)
    return None


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)

