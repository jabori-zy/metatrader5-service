import asyncio
from fastapi import FastAPI
import logging
from uvicorn.logging import DefaultFormatter
from fastapi.middleware.cors import CORSMiddleware
from api.router import create_router
from service_state import initialize_service_status, run_service_startup_check


# logging
handler = logging.StreamHandler()
handler.setFormatter(DefaultFormatter("%(levelprefix)s %(message)s"))
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler]
)


def create_app(terminal, skip_pull_config: bool = False) -> FastAPI:
    logger = logging.getLogger("MetaTrader5-service.app")

    app = FastAPI(
        title="MetaTrader5 Service",
        description="HTTP service for MetaTrader5",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源，生产环境应限制
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    initialize_service_status(app)
    app.state.terminal = terminal
    app.state.skip_pull_config = skip_pull_config

    @app.on_event("startup")
    async def startup_event():
        logger.info("scheduling service startup check, skip_pull_config=%s", skip_pull_config)
        app.state.service_status_task = asyncio.create_task(run_service_startup_check(app))

    @app.on_event("shutdown")
    async def shutdown_event():
        task = getattr(app.state, "service_status_task", None)
        if task is not None and not task.done():
            logger.info("cancelling service startup check")
            task.cancel()

    router = create_router(terminal)
    app.include_router(router)

    return app
