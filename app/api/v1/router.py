from fastapi import APIRouter

api_router = APIRouter()

# Example of including sub-routers:
# from app.api.v1.endpoints import users
# api_router.include_router(users.router, prefix="/users", tags=["users"])
