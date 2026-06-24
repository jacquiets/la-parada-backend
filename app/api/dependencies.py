from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from app.db.supabase import get_supabase_admin

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica el token JWT enviado en el header Authorization: Bearer <token>.
    Utiliza Supabase Auth para validarlo y obtener el perfil completo del usuario.
    """
    token = credentials.credentials
    sb = get_supabase_admin()
    
    try:
        res = sb.auth.get_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}"
        )
        
    if not res.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciales de autenticación inválidas"
        )
    
    # Obtener el perfil del usuario sin el join de roles
    try:
        perfil_res = (
            sb.table("usuarios")
            .select("*")
            .eq("auth_user_id", res.user.id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar el perfil de usuario: {str(e)}"
        )
    
    if not perfil_res.data:
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED, 
             detail="Perfil de usuario no encontrado en la base de datos"
         )
    
    user_data = perfil_res.data[0]
    
    # Buscar el rol por separado
    user_data["rol_nombre"] = None
    try:
        if user_data.get("rol_id"):
            rol_res = sb.table("roles").select("nombre").eq("id", user_data["rol_id"]).execute()
            if rol_res.data:
                user_data["rol_nombre"] = rol_res.data[0]["nombre"]
    except Exception:
        pass
    
    # Validar que el usuario esté activo
    if user_data.get("estado") != "Aprobado" and user_data.get("estado") != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o pendiente de aprobación."
        )
        
    return user_data


class RoleChecker:
    """
    Dependencia de FastAPI para validar que el usuario tenga uno de los roles permitidos.
    Uso:
    @router.get("/ruta", dependencies=[Depends(RoleChecker(["Administrador", "Comerciante"]))])
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(get_current_user)):
        rol_usuario = user.get("rol_nombre")
        
        if rol_usuario not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operación denegada. Se requiere rol: {', '.join(self.allowed_roles)}"
            )
        return user
