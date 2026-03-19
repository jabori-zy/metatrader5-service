from datetime import datetime
from typing import Any


def response_success(data: Any) -> dict:
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }


def response_error(mt5_error_code: int, message: str) -> dict:
    return {
        "success": False,
        "error_code": mt5_error_code,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }