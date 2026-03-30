import uvicorn
import argparse
import logging
import MetaTrader5
from app import create_app


def start_server(env: str, port: int, skip_pull_config: bool):
    if env == "dev":
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger("MetaTrader5-service")
    logger.info(
        "Starting MetaTrader5-service, env: %s, port: %s, skip_pull_config: %s",
        env,
        port,
        skip_pull_config,
    )
    logger.info("API docs: http://localhost:%s/docs", port)

    app = create_app(MetaTrader5, skip_pull_config=skip_pull_config)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--env", type=str, default="dev", help="environment")
    parser.add_argument("--port", type=int, default=8000, help="port")
    parser.add_argument(
        "--skip-pull-config",
        action="store_true",
        help="skip user config restore on startup and mark service ready for manual debugging",
    )
    args = parser.parse_args()
    start_server(args.env, args.port, args.skip_pull_config)


if __name__ == "__main__":
    main()
