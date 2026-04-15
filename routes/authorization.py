from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert, delete, text, and_
# from sqlalchemy.exc import SQLAlchemyError
from utils.validate_jwt import jwt_dependecy
from sqlmodel.modules import Modules
from sqlmodel.permissions import Permissions
from sqlmodel.user_perm_mdl import User_perm_mdl
from basemodel.authorization import auth_data
from config.db import get_db
from sqlmodel.ubigeo import Ubigeo
from sqlalchemy.orm import Session

authorization_route = APIRouter(
    prefix = '/authorization',
    tags=['Authorization']
)


@authorization_route.get("/")
async def get_data_Auth_UI(jwt_dependency: jwt_dependecy, 
                           user:str=None,
                           sessionx:Session=Depends(get_db)
                           ):
    not_matched_result = []
    try:
        #nueva consulta
        results = sessionx.query(Modules.c.mdlCode, Modules.c.mdlName, Permissions.c.permCode, Permissions.c.permName, User_perm_mdl.c.user). \
            join(Modules, Permissions.c.mdlCode == Modules.c.mdlCode). \
            join(User_perm_mdl, and_(User_perm_mdl.c.permCode == Permissions.c.permCode, User_perm_mdl.c.user == user), isouter=True). \
            all()
        
        modules = {}

        for mdl_code, mdl_name, perm_code, perm_name, user in results:
            if mdl_code not in modules:
                modules[mdl_code] = {
                    "code": mdl_code,
                    "name": mdl_name,
                    "perm": []
                }
            modules[mdl_code]["perm"].append({
                "code": perm_code,
                "name": perm_name,
                "enabled": user is not None  # True si hay texto, False si es None
            })

        not_matched_result = list(modules.values())

    except Exception as e:
        sessionx.rollback()
        not_matched_result = str(e)

    return not_matched_result

@authorization_route.get("/user")
async def get_user_permissions_by_module(
    jwt_dependency: jwt_dependecy = None, 
    user:str=None, 
    module:str=None,
    sessionx: Session = Depends(get_db)
    ):
    returned_value = []
    try:
        # if module is not None:
        #     response = sessionx.query(User_perm_mdl.c.permCode).filter(User_perm_mdl.c.user == user, User_perm_mdl.c.mdlCode == module).all()
        # else:
        #     response = sessionx.query(User_perm_mdl.c.permCode).filter(User_perm_mdl.c.user == user).all()
        # sessionx.close()
        # returned_value = list(map(lambda x: x[0], response))

        # Construimos la consulta base
        query = sessionx.query(User_perm_mdl.c.permCode).filter(User_perm_mdl.c.user == user)
        
        # Filtramos por módulo si es proporcionado
        if module:
            query = query.filter(User_perm_mdl.c.mdlCode == module)
            
        response = query.all()
        
        # Transformamos la respuesta (aplanamos la lista de tuplas)
        return [row[0] for row in response]

    except Exception as e:
        # Si algo falla, registramos el error y aseguramos que la sesión esté limpia
        print(f"Error en permisos: {e}")
        sessionx.rollback()
        return []
    

@authorization_route.patch("/user")
async def update_user_permissions(
    jwt_dependency: jwt_dependecy, 
    auth_data_changed:auth_data,
    sessionx:Session=Depends(get_db)
    ):
    msg = {
        'detail': 'Cambios aplicados.',
        'state': True
        }
        
    try:
        perm_for_delete = list(map(lambda y: {'mdlCode': y[0], 'permCode': y[1], 'user': auth_data_changed.user_affected}, list(filter(lambda x: not(bool(x[2])), auth_data_changed.auth_data))))

        perm_for_create = list(map(lambda w: {'mdlCode': w[0], 'permCode': w[1], 'user': auth_data_changed.user_affected}, list(filter(lambda x: bool(x[2]), auth_data_changed.auth_data))))

        # Eliminar filas según cada filtro único
        for perm in perm_for_delete:
            # Construimos la consulta con los filtros únicos
            sessionx.query(User_perm_mdl).filter_by(**perm).delete()  # Usamos ** para desempaquetar el diccionario
     
        if perm_for_create:
            # # Crear los permisos segun cada filtro unico
            stmt = text(f"INSERT INTO user_perm_mdl VALUES (:mdlCode, :permCode, :user)")
            response = sessionx.execute(stmt, perm_for_create)
        
        sessionx.commit()

    except Exception as e:
        sessionx.rollback()
        msg['detail'] = str(e)
        msg['state'] = False

    # Cerrar la sesión
    return JSONResponse(
        status_code=200,
        content= msg
        )
        
    

