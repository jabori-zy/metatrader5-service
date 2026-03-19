from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from typing import Dict
from api.response import response_success, response_error



def create_router(terminal):
    router = APIRouter(tags=["account"])

    @router.get("/account_info")
    async def get_account_info():
        """
        get account info
        
        get the detailed information of the current MT5 account, including balance, equity, margin, free margin, etc.
        """
        try:
            account_info = terminal.account_info()
            
            if not account_info:
                last_error = terminal.last_error()
                return response_error(last_error[0], last_error[1])
            return response_success(account_info._asdict())
            
        except Exception as e:
            return response_error(-1, f"Get account info failed: {str(e)}")
    return router