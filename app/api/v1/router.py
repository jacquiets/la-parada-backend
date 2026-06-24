from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Agrega más routers aquí según crezca la aplicación:
# from app.api.v1.endpoints import usuarios, programaciones
# api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])

