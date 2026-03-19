from fastapi import APIRouter
from .endpoint import account
from .endpoint import health
# , symbol, market, order, basic, position



def create_router(terminal):
    router = APIRouter()
    account_router  = account.create_router(terminal)
    health_router  = health.create_router(terminal)
    # # 创建交易品种路由
    # symbol_router  = symbol.create_router(terminal)
    # # 创建市场路由
    # market_router  = market.create_router(terminal)
    # # 创建订单路由
    # order_router  = order.create_router(terminal)
    # # 创建基础路由
    # basic_router  = basic.create_router(terminal)
    # # 创建持仓路由
    # position_router  = position.create_router(terminal)
    # 将账户路由添加到主路由
    router.include_router(account_router)
    router.include_router(health_router)
    # router.include_router(symbol_router)
    # router.include_router(market_router)
    # router.include_router(order_router)
    # router.include_router(basic_router)
    # router.include_router(position_router)
    return router



