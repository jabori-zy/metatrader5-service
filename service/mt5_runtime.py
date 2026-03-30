import logging
import os
import subprocess
import time
from typing import Optional, Tuple

DEFAULT_TERMINAL_PATH = "C:/Program Files/MetaTrader 5/terminal64.exe"
INITIALIZE_TIMEOUT_SECONDS = 60

logger = logging.getLogger("MetaTrader5-service.mt5_runtime")


def get_last_error(terminal) -> Tuple[int, str]:
    last_error = terminal.last_error()
    if isinstance(last_error, tuple) and len(last_error) >= 2:
        return int(last_error[0]), str(last_error[1])
    return -1, str(last_error)


def is_initialized(terminal) -> bool:
    return terminal.terminal_info() is not None


def normalize_terminal_path(terminal_path: Optional[str]) -> str:
    if terminal_path is None:
        return DEFAULT_TERMINAL_PATH

    normalized = terminal_path.strip()
    if normalized == "" or normalized.lower() == "string":
        return DEFAULT_TERMINAL_PATH
    return normalized.replace("/", "\\")


def start_terminal_process(terminal_path: str, portable: bool) -> Tuple[bool, str]:
    if not os.path.exists(terminal_path):
        return False, "terminal executable not found: %s" % terminal_path

    command = [terminal_path]
    if portable:
        command.append("/portable")

    creationflags = 0
    detached_process = getattr(subprocess, "DETACHED_PROCESS", 0)
    create_new_process_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    creationflags |= detached_process | create_new_process_group

    try:
        process = subprocess.Popen(
            command,
            cwd=os.path.dirname(terminal_path) or None,
            creationflags=creationflags,
        )
        return True, "pid=%s" % process.pid
    except Exception as exc:
        return False, str(exc)


def wait_for_initialize(terminal, terminal_path: str, portable: bool, timeout_seconds: int) -> Tuple[bool, Tuple[int, str]]:
    deadline = time.time() + timeout_seconds
    last_error = (-1, "initialize timed out")
    while time.time() < deadline:
        init_result = terminal.initialize(terminal_path=terminal_path, portable=portable)
        if init_result:
            return True, (0, "")
        last_error = get_last_error(terminal)
        time.sleep(1)
    return False, last_error


def initialize_terminal(
    terminal,
    terminal_path: Optional[str] = None,
    portable: bool = True,
    launch_if_needed: bool = True,
) -> Tuple[bool, Tuple[int, str], str, bool]:
    normalized_terminal_path = normalize_terminal_path(terminal_path)

    if is_initialized(terminal):
        return True, (0, ""), normalized_terminal_path, portable

    init_result = terminal.initialize(terminal_path=normalized_terminal_path, portable=portable)
    if init_result:
        return True, (0, ""), normalized_terminal_path, portable

    initial_error = get_last_error(terminal)
    logger.info(
        "initialize requested, terminal_path=%s portable=%s initial_error=%s launch_if_needed=%s",
        normalized_terminal_path,
        portable,
        initial_error,
        launch_if_needed,
    )

    if launch_if_needed:
        launch_ok, launch_message = start_terminal_process(normalized_terminal_path, portable)
        if not launch_ok:
            return False, (-1, "Start terminal failed: %s" % launch_message), normalized_terminal_path, portable
        logger.info(
            "terminal start requested, terminal_path=%s portable=%s result=%s",
            normalized_terminal_path,
            portable,
            launch_message,
        )

    initialized, initialize_error = wait_for_initialize(
        terminal,
        normalized_terminal_path,
        portable,
        INITIALIZE_TIMEOUT_SECONDS,
    )
    if not initialized:
        return (
            False,
            (
                initialize_error[0],
                "Timed out waiting for terminal initialization after %ss: %s"
                % (INITIALIZE_TIMEOUT_SECONDS, initialize_error[1]),
            ),
            normalized_terminal_path,
            portable,
        )

    return True, (0, ""), normalized_terminal_path, portable


def login_terminal(terminal, login: int, password: str, server: str) -> Tuple[bool, Tuple[int, str]]:
    login_result = terminal.login(
        login=login,
        password=password,
        server=server,
    )
    if not login_result:
        return False, get_last_error(terminal)
    return True, (0, "")


def get_account_info_data(terminal) -> Tuple[bool, object, Tuple[int, str]]:
    account_info = terminal.account_info()
    if not account_info:
        return False, None, get_last_error(terminal)
    return True, account_info._asdict(), (0, "")
