from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.db.supabase import get_supabase_admin
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar todos los muelles disponibles",
)
def listar_muelles(
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Retorna la lista de muelles registrados en la base de datos.
    Cualquier usuario autenticado puede consultarlos para llenar formularios.
    """
    sb = get_supabase_admin()
    
    try:
        # Ordenamos alfabéticamente por código
        muelles_res = sb.table("muelles").select("*").order("codigo").execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar la lista de muelles: {str(e)}"
        )
        
    return muelles_res.data
