from typing import Optional, Tuple

DEFAULT_TERMINAL_PATH = "C:/Program Files/MetaTrader 5/terminal64.exe"


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
