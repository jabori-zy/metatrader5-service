from datetime import datetime
from typing import Any, Optional

from fastapi.responses import JSONResponse

from api.error import Mt5Error


def response_success(data: Any) -> dict:
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }


def response_error(error, extra: Optional[dict] = None, status_code: Optional[int] = None) -> JSONResponse:
    response = {
        "success": False,
        "message": str(error),
        "timestamp": datetime.now().isoformat(),
    }
    if isinstance(error, Mt5Error):
        response["mt5_error_code"] = error.error_code
        if status_code is None:
            status_code = 424 # Failed Dependency, since the error is related to MT5 operations
    if status_code is None:
        status_code = 400
    if extra:
        response.update(extra)
    return JSONResponse(status_code=status_code, content=response)
