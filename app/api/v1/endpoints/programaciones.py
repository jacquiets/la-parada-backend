from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date, time

from app.schemas.programacion import ProgramacionCreate, ProgramacionResponse, ProgramacionListResponse
from app.db.supabase import get_supabase_admin
from app.api.dependencies import get_current_user, RoleChecker

router = APIRouter()


@router.post(
    "",
    response_model=ProgramacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear programación de ingreso",
    dependencies=[Depends(RoleChecker(["Comerciante"]))],
)
def crear_programacion(
    body: ProgramacionCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Crea una nueva programación de ingreso.
    Requiere rol 'Comerciante' y estado 'Aprobado'.
    """
    sb = get_supabase_admin()

    # 1. Validar Muelle
    try:
        muelle_res = sb.table("muelles").select("*").eq("id", body.muelle_id).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando el muelle: {str(e)}"
        )

    if not muelle_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El muelle especificado no existe."
        )

    muelle = muelle_res.data[0]

    if muelle.get("estado") != "Disponible":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El muelle no está disponible. Estado actual: {muelle.get('estado')}"
        )

    # 2. Validar capacidad del slot (misma fecha y hora)
    try:
        str_fecha = body.fecha_ingreso.isoformat()
        str_hora = body.hora_ingreso.isoformat()
        
        programaciones_res = (
            sb.table("programaciones")
            .select("id")
            .eq("muelle_id", body.muelle_id)
            .eq("fecha_ingreso", str_fecha)
            .eq("hora_ingreso", str_hora)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando programaciones existentes: {str(e)}"
        )

    programaciones_actuales = len(programaciones_res.data)
    capacidad = muelle.get("capacidad_camiones", 0)

    if programaciones_actuales >= capacidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El muelle ya alcanzó su capacidad máxima ({capacidad}) para la fecha y hora seleccionadas."
        )

    # 3. Crear Programación
    programacion_data = {
        "usuario_id": current_user["id"],
        "muelle_id": body.muelle_id,
        "fecha_ingreso": str_fecha,
        "hora_ingreso": str_hora,
        "tipo_carga": body.tipo_carga,
        "volumen_carga": body.volumen_carga,
        "estado": "Programado"
    }

    try:
        insert_res = sb.table("programaciones").insert(programacion_data).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la programación: {str(e)}"
        )

    if not insert_res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo registrar la programación."
        )

    return insert_res.data[0]


@router.get(
    "",
    response_model=List[ProgramacionListResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar programaciones",
)
def listar_programaciones(
    usuario_id: Optional[str] = Query(None, description="Filtro de usuario (solo Admins)"),
    muelle_id: Optional[str] = Query(None, description="Filtro de muelle"),
    fecha_ingreso: Optional[date] = Query(None, description="Filtro de fecha"),
    estado: Optional[str] = Query(None, description="Filtro de estado"),
    current_user: dict = Depends(get_current_user),
):
    """
    Lista las programaciones.
    Los comerciantes solo ven las suyas. Los administradores ven todas y pueden filtrar.
    """
    sb = get_supabase_admin()
    
    query = sb.table("programaciones").select("*, usuarios(nombres, apellidos), muelles(codigo)")

    rol_usuario = current_user.get("rol_nombre")

    if rol_usuario == "Comerciante":
        # Comerciante solo ve lo suyo
        query = query.eq("usuario_id", current_user["id"])
        
        # Filtros opcionales para el comerciante
        if muelle_id:
            query = query.eq("muelle_id", muelle_id)
        if fecha_ingreso:
            query = query.eq("fecha_ingreso", fecha_ingreso.isoformat())
        if estado:
            query = query.eq("estado", estado)
            
    elif rol_usuario == "Administrador":
        # Administrador puede ver todo y usar todos los filtros
        if usuario_id:
            query = query.eq("usuario_id", usuario_id)
        if muelle_id:
            query = query.eq("muelle_id", muelle_id)
        if fecha_ingreso:
            query = query.eq("fecha_ingreso", fecha_ingreso.isoformat())
        if estado:
            query = query.eq("estado", estado)
    else:
        # Por seguridad, si hay otro rol no contemplado, no devolvemos nada o arrojamos error
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su rol no tiene permisos para consultar programaciones."
        )

    try:
        # Ordenamos de más reciente a más antiguo por fecha y hora
        query = query.order("fecha_ingreso", desc=True).order("hora_ingreso", desc=True)
        result = query.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando las programaciones: {str(e)}"
        )

    return result.data
