from fastapi import APIRouter
from .endpoint.metatrader5 import terminal as terminal_mod, account, symbol, market, order, position
from .endpoint import health
from .endpoint import service_status


def create_router(terminal):
    router = APIRouter()
    router.include_router(terminal_mod.create_router(terminal))
    router.include_router(account.create_router(terminal))
    router.include_router(symbol.create_router(terminal))
    router.include_router(market.create_router(terminal))
    router.include_router(order.create_router(terminal))
    router.include_router(position.create_router(terminal))
    router.include_router(health.create_router(terminal))
    router.include_router(service_status.create_router(terminal))
    return router


