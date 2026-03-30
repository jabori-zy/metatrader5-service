from fastapi import APIRouter, Request

from api.response import response_success
from service_state import get_service_status


def create_router():
    router = APIRouter(tags=["service"])

    @router.get("/service_status")
    async def service_status(request: Request):
        """
        Get the current service state.
        """
        return response_success(get_service_status(request.app))

    return router
