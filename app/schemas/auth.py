from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    nombres: str
    apellidos: str
    email: EmailStr
    password: str
    rol_nombre: str  # "comerciante" | "estibador"
    telefono: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: str
    auth_user_id: str
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    rol_id: str
    rol_nombre: Optional[str] = None
    estado: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
