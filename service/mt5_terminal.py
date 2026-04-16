import logging
from typing import Optional

INITIALIZE_TIMEOUT_MILLISECONDS = 5000

logger = logging.getLogger("MetaTrader5-service.mt5_termimal")


def initialize(
    terminal,
    terminal_path: str,
    portable: bool = True,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
) -> bool:
    has_credentials = login is not None or password is not None or server is not None
    if has_credentials and (login is None or password is None or server is None):
        raise ValueError("login, password and server must be provided together")

    if login is None and password is None and server is None:
        init_result = terminal.initialize(
            terminal_path,
            portable=portable,
            timeout=INITIALIZE_TIMEOUT_MILLISECONDS,
        )
    else:
        init_result = terminal.initialize(
            terminal_path,
            login=login,
            password=password,
            server=server,
            portable=portable,
            timeout=INITIALIZE_TIMEOUT_MILLISECONDS,
        )
    return init_result

def login(terminal, login: int, password: str, server: str) -> bool:
    login_result = terminal.login(
        login=login,
        password=password,
        server=server,
    )
    return login_result


def _convert_struct_result(value):
    if value is None:
        return None
    if hasattr(value, "_asdict"):
        return value._asdict()
    return value


def account_info(terminal) -> Optional[dict]:
    return _convert_struct_result(terminal.account_info())


def terminal_info(terminal) -> Optional[dict]:
    return _convert_struct_result(terminal.terminal_info())


def symbols_total(terminal) -> int:
    return terminal.symbols_total()


def symbols_get(terminal, group: Optional[str] = None):
    if group is None:
        return terminal.symbols_get()
    return terminal.symbols_get(group=group)


def symbol_info(terminal, symbol: str) -> Optional[dict]:
    return _convert_struct_result(terminal.symbol_info(symbol))


def symbol_info_tick(terminal, symbol: str):
    return _convert_struct_result(terminal.symbol_info_tick(symbol))


def symbol_select(terminal, symbol: str, enable=None):
    if enable is None:
        return terminal.symbol_select(symbol)
    return terminal.symbol_select(symbol, enable)


def market_book_add(terminal, symbol: str) -> bool:
    return terminal.market_book_add(symbol)


def market_book_get(terminal, symbol: str):
    return terminal.market_book_get(symbol)


def market_book_release(terminal, symbol: str) -> bool:
    return terminal.market_book_release(symbol)


def copy_rates_from(terminal, symbol: str, timeframe, date_from, count):
    return terminal.copy_rates_from(symbol, timeframe, date_from, count)


def copy_rates_from_pos(terminal, symbol: str, timeframe, start_pos: int, count: int):
    return terminal.copy_rates_from_pos(symbol, timeframe, start_pos, count)


def copy_rates_range(terminal, symbol: str, timeframe, date_from, date_to):
    return terminal.copy_rates_range(symbol, timeframe, date_from, date_to)


def copy_ticks_from(terminal, symbol: str, date_from, count: int, flags: int):
    return terminal.copy_ticks_from(symbol, date_from, count, flags)


def copy_ticks_range(terminal, symbol: str, date_from, date_to, flags: int):
    return terminal.copy_ticks_range(symbol, date_from, date_to, flags)


def orders_total(terminal) -> int:
    return terminal.orders_total()


def orders_get(
    terminal,
    symbol: Optional[str] = None,
    group: Optional[str] = None,
    ticket: Optional[int] = None,
):
    if symbol is not None:
        return terminal.orders_get(symbol=symbol)
    if group is not None:
        return terminal.orders_get(group=group)
    if ticket is not None:
        return terminal.orders_get(ticket=ticket)
    return terminal.orders_get()


def order_calc_margin(terminal, action, symbol: str, volume: float, price: float):
    return terminal.order_calc_margin(action, symbol, volume, price)


def order_calc_profit(terminal, action, symbol: str, volume: float, price_open: float, price_close: float):
    return terminal.order_calc_profit(action, symbol, volume, price_open, price_close)


def order_check(terminal, request):
    return _convert_struct_result(terminal.order_check(request))


def order_send(terminal, request):
    return _convert_struct_result(terminal.order_send(request))


def positions_total(terminal) -> int:
    return terminal.positions_total()


def positions_get(
    terminal,
    symbol: Optional[str] = None,
    group: Optional[str] = None,
    ticket: Optional[int] = None,
):
    if symbol is not None:
        return terminal.positions_get(symbol=symbol)
    if group is not None:
        return terminal.positions_get(group=group)
    if ticket is not None:
        return terminal.positions_get(ticket=ticket)
    return terminal.positions_get()


def history_orders_total(terminal, date_from, date_to) -> int:
    return terminal.history_orders_total(date_from, date_to)


def history_orders_get(
    terminal,
    date_from=None,
    date_to=None,
    group: Optional[str] = None,
    ticket: Optional[int] = None,
    position: Optional[int] = None,
):
    if ticket is not None:
        return terminal.history_orders_get(ticket=ticket)
    if position is not None:
        return terminal.history_orders_get(position=position)
    if date_from is None or date_to is None:
        raise ValueError("date_from and date_to must be provided together")
    if group is None:
        return terminal.history_orders_get(date_from, date_to)
    return terminal.history_orders_get(date_from, date_to, group=group)


def history_deals_total(terminal, date_from, date_to) -> int:
    return terminal.history_deals_total(date_from, date_to)


def history_deals_get(
    terminal,
    date_from=None,
    date_to=None,
    group: Optional[str] = None,
    ticket: Optional[int] = None,
    position: Optional[int] = None,
):
    if ticket is not None:
        return terminal.history_deals_get(ticket=ticket)
    if position is not None:
        return terminal.history_deals_get(position=position)
    if date_from is None or date_to is None:
        raise ValueError("date_from and date_to must be provided together")
    if group is None:
        return terminal.history_deals_get(date_from, date_to)
    return terminal.history_deals_get(date_from, date_to, group=group)


def shutdown(terminal):
    return terminal.shutdown()


def version(terminal):
    return terminal.version()


def last_error(terminal):
    return terminal.last_error()
