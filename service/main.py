import uvicorn
import argparse
import logging
from fastapi import FastAPI
import MetaTrader5
from app import create_app






def start_server(env: str, port: int, terminal_path: str, login:int, password:str, server:str):
    if env == "dev":
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    logger = logging.getLogger("MetaTrader5-service")
    logger.info("Starting MetaTrader5-service, env: %s, port: %s", env, port)
    logger.info("API docs: http://localhost:%s/docs", port)
    

    try:
        init_terminal(login, password, server, terminal_path)
        app = create_app(MetaTrader5, login, password, server, terminal_path)
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            reload=False,
            log_level="info",
        )
    except Exception as e:
        logging.error("terminal initialized failed, error: %s", e)
        raise RuntimeError(f"terminal initialized failed, error: {e}") from e


def init_terminal(login:int, password:str, server:str, terminal_path:str):
    logging.info("Start to init terminal, terminal_path: %s", terminal_path)
    init_result = MetaTrader5.initialize(login=login, password=password, server=server, terminal_path=terminal_path)

    if not init_result:
        logging.error("terminal initialized failed, error: %s", MetaTrader5.last_error())
        raise ConnectionError(f"terminal initialized failed, error: {MetaTrader5.last_error()}")

    terminal_info = MetaTrader5.terminal_info()  # type: ignore
    logging.info("terminal initialized successfully. connected: %s, trade_enabled: %s", terminal_info.connected, terminal_info.trade_allowed)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--env", type=str, default="dev", help="environment")
    parser.add_argument("--port", type=int, default=8000, help="port")
    parser.add_argument("--terminal-path", type=str, default="C:/Program Files/MetaTrader 5/terminal64.exe", help="terminal path")
    parser.add_argument("--login", type=int, help="login")
    parser.add_argument("--password", type=str, help="password")
    parser.add_argument("--server", type=str, help="server")
    args = parser.parse_args()
    start_server(args.env, args.port, args.terminal_path, args.login, args.password, args.server)


if __name__ == "__main__":
    main()
