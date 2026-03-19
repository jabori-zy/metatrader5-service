from fastapi import FastAPI
import logging
from uvicorn.logging import DefaultFormatter
from fastapi.middleware.cors import CORSMiddleware
from api.router import create_router


# logging
handler = logging.StreamHandler()
handler.setFormatter(DefaultFormatter("%(levelprefix)s %(message)s"))
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler]
)




def create_app(terminal, login, password, server, terminal_path ) -> FastAPI:

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

    router = create_router(terminal)
    app.include_router(router)

    return app