from typing import Optional, Tuple

DEFAULT_TERMINAL_PATH = "C:/Program Files/MetaTrader 5/terminal64.exe"
import MetaTrader5

def get_last_error(terminal) -> Tuple[int, str]:
    last_error = terminal.last_error()
    if isinstance(last_error, tuple) and len(last_error) >= 2:
        return int(last_error[0]), str(last_error[1])
    return -1, str(last_error)


def is_initialized(terminal) -> bool:
    return terminal.terminal_info() is not None


def check_terminal_path_format(terminal_path: Optional[str]) -> str:
    if terminal_path is None:
        return DEFAULT_TERMINAL_PATH

    normalized = terminal_path.strip()
    if normalized == "":
        return DEFAULT_TERMINAL_PATH

    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in ("'", '"'):
        raise ValueError("terminal_path format is invalid.: %s. The correct path is like 'C:/Program Files/MetaTrader 5/terminal64.exe" % normalized)

    return normalized


def get_time_frame(time_frame: str) -> Optional[int]:
    """
    get time frame
    Args:
        time_frame: time frame string
    Returns:
        int: MetaTrader5 time frame integer
    """
    time_frame_dict = {
        "M1": MetaTrader5.TIMEFRAME_M1,
        "M5": MetaTrader5.TIMEFRAME_M5,
        "M15": MetaTrader5.TIMEFRAME_M15,
        "M30": MetaTrader5.TIMEFRAME_M30,
        "H1": MetaTrader5.TIMEFRAME_H1,
        "H2": MetaTrader5.TIMEFRAME_H2,
        "H4": MetaTrader5.TIMEFRAME_H4,
        "H6": MetaTrader5.TIMEFRAME_H6,
        "H8": MetaTrader5.TIMEFRAME_H8,
        "H12": MetaTrader5.TIMEFRAME_H12,
        "D1": MetaTrader5.TIMEFRAME_D1,
        "W1": MetaTrader5.TIMEFRAME_W1,
        "MN1": MetaTrader5.TIMEFRAME_MN1
    }
    return time_frame_dict.get(time_frame)
