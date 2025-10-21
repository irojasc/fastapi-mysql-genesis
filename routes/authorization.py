from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert, delete, text, and_
from sqlalchemy.exc import SQLAlchemyError
from utils.validate_jwt import jwt_dependecy
from sqlmodel.modules import Modules
from sqlmodel.permissions import Permissions
from sqlmodel.user_perm_mdl import User_perm_mdl
from basemodel.authorization import auth_data
from config.db import con, session
from sqlmodel.ubigeo import Ubigeo

authorization_route = APIRouter(
    prefix = '/authorization',
    tags=['Authorization']
)


@authorization_route.get("/")
async def get_data_Auth_UI(jwt_dependency: jwt_dependecy, user:str=None):
    not_matched_result = []
    try:
        #nueva consulta
        results = session.query(Modules.c.mdlCode, Modules.c.mdlName, Permissions.c.permCode, Permissions.c.permName, User_perm_mdl.c.user). \
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
        session.rollback()
        not_matched_result = str(e)

    finally:
        return not_matched_result

@authorization_route.get("/user")
async def get_user_permissions_by_module(jwt_dependency: jwt_dependecy = None, user:str=None, module:str=None):
    returned_value = []
    try:
        if module is not None:
            response = session.query(User_perm_mdl.c.permCode).filter(User_perm_mdl.c.user == user, User_perm_mdl.c.mdlCode == module).all()
        else:
            response = session.query(User_perm_mdl.c.permCode).filter(User_perm_mdl.c.user == user).all()
        session.close()
        returned_value = list(map(lambda x: x[0], response))
    except Exception as e:
        session.rollback()
        returned_value = []
    finally:
        return returned_value

@authorization_route.patch("/user")
async def update_user_permissions(jwt_dependency: jwt_dependecy, auth_data_changed:auth_data):
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
            session.query(User_perm_mdl).filter_by(**perm).delete()  # Usamos ** para desempaquetar el diccionario
     
        if perm_for_create:
            # # Crear los permisos segun cada filtro unico
            stmt = text(f"INSERT INTO user_perm_mdl VALUES (:mdlCode, :permCode, :user)")
            response = session.execute(stmt, perm_for_create)
        
        session.commit()
        # if(response.rowcount > 0):

    except Exception as e:
        session.rollback()
        msg['detail'] = str(e)
        msg['state'] = False

    finally:
        # Cerrar la sesión
        session.close()
        return JSONResponse(
            status_code=200,
            content= msg
            )
        
    

