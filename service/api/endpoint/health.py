from fastapi import APIRouter, Response

from api.response import response_success, response_error


def create_router(terminal):
    router = APIRouter(tags=["health"])

    @router.get("/")
    async def ping():
        """
        Liveness probe - test if the server is running.
        """
        return response_success("ok")

    @router.get("/favicon.ico")
    async def favicon():
        """
        Handle browser favicon request, avoid 404 error.
        """
        return Response(status_code=204)

    return router
