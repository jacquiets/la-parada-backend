from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserProfile
from app.db.supabase import get_supabase_admin

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def register(body: RegisterRequest):
    """
    Crea una nueva cuenta en Supabase Auth e inserta el perfil en la tabla `usuarios`.

    El estado del usuario se establece como **activo** de inmediato para que pueda
    iniciar sesión sin validación adicional.
    """
    sb = get_supabase_admin()

    # 1. Crear usuario en Supabase Auth
    try:
        auth_res = sb.auth.admin.create_user(
            {
                "email": body.email,
                "password": body.password,
                "email_confirm": True,  # Confirmar email automáticamente (sin email verification)
            }
        )
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg or "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este correo electrónico ya está registrado.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear la cuenta: {error_msg}",
        )

    auth_user = auth_res.user
    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear el usuario en el sistema de autenticación.",
        )

    # 2. Buscar el rol_id por nombre en la tabla roles
    try:
        rol_res = (
            sb.table("roles")
            .select("id, nombre")
            .eq("nombre", body.rol_nombre)
            .execute()
        )
    except Exception as e:
        sb.auth.admin.delete_user(auth_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando la tabla de roles: {str(e)}"
        )

    if not rol_res.data:
        # Revertir: eliminar el usuario de Auth si el rol no existe
        sb.auth.admin.delete_user(auth_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol '{body.rol_nombre}' no existe en la base de datos de Supabase.",
        )

    rol = rol_res.data[0]

    # 3. Insertar perfil en la tabla usuarios con estado = "activo"
    usuario_data = {
        "auth_user_id": auth_user.id,
        "nombres": body.nombres,
        "apellidos": body.apellidos,
        "telefono": body.telefono,
        "rol_id": rol["id"],
        "estado": "activo",
    }

    try:
        insert_res = sb.table("usuarios").insert(usuario_data).execute()
    except Exception as e:
        sb.auth.admin.delete_user(auth_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error insertando en tabla usuarios: {str(e)}"
        )

    if not insert_res.data:
        # Revertir: eliminar el usuario de Auth si falla la inserción de perfil
        sb.auth.admin.delete_user(auth_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar el perfil del usuario.",
        )

    usuario = insert_res.data[0]

    # 4. Obtener access_token haciendo sign_in inmediatamente después del registro
    sign_in_res = sb.auth.sign_in_with_password(
        {"email": body.email, "password": body.password}
    )

    if sign_in_res.session is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Usuario creado pero no se pudo iniciar sesión automáticamente.",
        )

    return AuthResponse(
        access_token=sign_in_res.session.access_token,
        user=UserProfile(
            id=usuario["id"],
            auth_user_id=usuario["auth_user_id"],
            nombres=usuario["nombres"],
            apellidos=usuario["apellidos"],
            telefono=usuario.get("telefono"),
            rol_id=usuario["rol_id"],
            rol_nombre=rol["nombre"],
            estado=usuario["estado"],
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
)
def login(body: LoginRequest):
    """
    Autentica al usuario con email y contraseña usando Supabase Auth
    y retorna el access_token junto con el perfil del usuario.
    """
    sb = get_supabase_admin()

    # 1. Autenticar en Supabase Auth
    try:
        sign_in_res = sb.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
        )

    if sign_in_res.session is None or sign_in_res.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
        )

    auth_user = sign_in_res.user

    # 2. Obtener perfil del usuario desde la tabla usuarios + rol
    perfil_res = (
        sb.table("usuarios")
        .select("*, roles(nombre)")
        .eq("auth_user_id", auth_user.id)
        .single()
        .execute()
    )

    if not perfil_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el perfil del usuario.",
        )

    usuario = perfil_res.data
    rol_nombre = usuario.get("roles", {}).get("nombre") if usuario.get("roles") else None

    return AuthResponse(
        access_token=sign_in_res.session.access_token,
        user=UserProfile(
            id=usuario["id"],
            auth_user_id=usuario["auth_user_id"],
            nombres=usuario["nombres"],
            apellidos=usuario["apellidos"],
            telefono=usuario.get("telefono"),
            rol_id=usuario["rol_id"],
            rol_nombre=rol_nombre,
            estado=usuario["estado"],
        ),
    )
