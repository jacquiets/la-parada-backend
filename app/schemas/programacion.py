from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime


class ProgramacionCreate(BaseModel):
    muelle_id: str
    fecha_ingreso: date
    hora_ingreso: time
    tipo_carga: str
    volumen_carga: float


class ProgramacionResponse(BaseModel):
    id: str
    usuario_id: str
    muelle_id: str
    fecha_ingreso: date
    hora_ingreso: time
    tipo_carga: str
    volumen_carga: float
    estado: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class UsuarioInfo(BaseModel):
    nombres: str
    apellidos: str


class MuelleInfo(BaseModel):
    codigo: str


class ProgramacionListResponse(ProgramacionResponse):
    usuarios: Optional[UsuarioInfo] = None
    muelles: Optional[MuelleInfo] = None
