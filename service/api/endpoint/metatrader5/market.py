from fastapi import APIRouter
from api.error import Mt5Error
from api.response import response_success, response_error
from mt5_terminal import (
    copy_rates_from as mt5_copy_rates_from,
    copy_rates_from_pos as mt5_copy_rates_from_pos,
    copy_rates_range as mt5_copy_rates_range,
    copy_ticks_from as mt5_copy_ticks_from,
    copy_ticks_range as mt5_copy_ticks_range,
)
from terminal_utils import get_last_error, get_time_frame
from api.utils import check_init, parse_datetime


def _rates_to_list(result):
    if result is None:
        return None
    # numpy structured array or list of namedtuples
    try:
        return result.tolist()
    except AttributeError:
        return list(result)


_TIMEFRAME_ERROR = (
    "Invalid timeframe: '{}'. Valid values: "
    "M1, M2, M3, M4, M5, M6, M10, M12, M15, M20, M30, "
    "H1, H2, H3, H4, H6, H8, H12, D1, W1, MN1"
)


def create_router(terminal):
    router = APIRouter(tags=["market"], prefix="/metatrader5")

    @router.get("/copy_rates_from")
    async def copy_rates_from(symbol: str, timeframe: str, date_from: str, count: int):
        """
        Get OHLCV bars starting from a given date.

        - **timeframe**: e.g. M1, M5, H1, D1
        - **date_from**: ISO 8601 datetime string (e.g. 2024-01-01T00:00:00)
        - **count**: number of bars to retrieve
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            tf = get_time_frame(timeframe)
            if tf is None:
                return response_error(ValueError(_TIMEFRAME_ERROR.format(timeframe)), status_code=422)
            dt = parse_datetime(date_from)
            result = mt5_copy_rates_from(terminal, symbol, tf, dt, count)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_rates_to_list(result))
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"copy_rates_from failed: {e}"), status_code=500)

    @router.get("/copy_rates_from_pos")
    async def copy_rates_from_pos(symbol: str, timeframe: str, start_pos: int, count: int):
        """
        Get OHLCV bars starting from a bar index (0 = current bar).

        - **timeframe**: e.g. M1, M5, H1, D1
        - **start_pos**: start position (0-based index from current bar)
        - **count**: number of bars to retrieve
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            tf = get_time_frame(timeframe)
            if tf is None:
                return response_error(ValueError(_TIMEFRAME_ERROR.format(timeframe)), status_code=422)
            result = mt5_copy_rates_from_pos(terminal, symbol, tf, start_pos, count)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_rates_to_list(result))
        except Exception as e:
            return response_error(Exception(f"copy_rates_from_pos failed: {e}"), status_code=500)

    @router.get("/copy_rates_range")
    async def copy_rates_range(symbol: str, timeframe: str, date_from: str, date_to: str):
        """
        Get OHLCV bars within a date range.

        - **timeframe**: e.g. M1, M5, H1, D1
        - **date_from**: ISO 8601 datetime string
        - **date_to**: ISO 8601 datetime string
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            tf = get_time_frame(timeframe)
            if tf is None:
                return response_error(ValueError(_TIMEFRAME_ERROR.format(timeframe)), status_code=422)
            dt_from = parse_datetime(date_from)
            dt_to = parse_datetime(date_to)
            result = mt5_copy_rates_range(terminal, symbol, tf, dt_from, dt_to)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_rates_to_list(result))
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"copy_rates_range failed: {e}"), status_code=500)

    @router.get("/copy_ticks_from")
    async def copy_ticks_from(symbol: str, date_from: str, count: int, flags: int):
        """
        Get ticks starting from a given date.

        - **date_from**: ISO 8601 datetime string
        - **count**: number of ticks to retrieve
        - **flags**: MT5 COPY_TICKS_* flags as integer (e.g. 1=ALL, 2=INFO, 4=TRADE)
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            dt = parse_datetime(date_from)
            result = mt5_copy_ticks_from(terminal, symbol, dt, count, flags)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_rates_to_list(result))
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"copy_ticks_from failed: {e}"), status_code=500)

    @router.get("/copy_ticks_range")
    async def copy_ticks_range(symbol: str, date_from: str, date_to: str, flags: int):
        """
        Get ticks within a date range.

        - **date_from**: ISO 8601 datetime string
        - **date_to**: ISO 8601 datetime string
        - **flags**: MT5 COPY_TICKS_* flags as integer
        """
        err = check_init(terminal)
        if err:
            return err
        try:
            dt_from = parse_datetime(date_from)
            dt_to = parse_datetime(date_to)
            result = mt5_copy_ticks_range(terminal, symbol, dt_from, dt_to, flags)
            if result is None:
                mt5_err = get_last_error(terminal)
                return response_error(Mt5Error(mt5_err[0], mt5_err[1]))
            return response_success(_rates_to_list(result))
        except ValueError as e:
            return response_error(e, status_code=422)
        except Exception as e:
            return response_error(Exception(f"copy_ticks_range failed: {e}"), status_code=500)

    return router
