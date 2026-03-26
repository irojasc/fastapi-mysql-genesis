from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, asc, insert, func
from sqlalchemy.exc import SQLAlchemyError
from utils.validate_jwt import jwt_dependecy
from sqlmodel.user import User
# from config.db import con, session
from functions.inventory import changeBin2Bool
from basemodel.user import new_user
from utils.hash_handler import hash_password
from config.db import get_db
from sqlalchemy.orm import Session

user_route = APIRouter(
    prefix = '/user',
    tags=['User']
)

@user_route.get("/")
# def get_users(access_token: Annotated[str | None, Cookie()] = None):
def get_users(jwt_dependency: jwt_dependecy, session: Session = Depends(get_db)):
    try:
        data_usrs = session.query(
            User.c.id, 
            User.c.idDoc, 
            User.c.userName, 
            User.c.user, 
            User.c.enabled
        ).order_by(asc(User.c.id)).all()

        # 3. Usamos acceso por nombre de atributo (x.id, x.docNum)
        result = [{
            "id": x.id, 
            "docNum": x.idDoc, 
            "userName": x.userName, 
            "user": x.user, 
            "enabled": changeBin2Bool(x.enabled)
        } for x in data_usrs]


        return {"result": result}

    except Exception as e:
        # Es mejor no exponer el error interno (str(e)) en producción por seguridad
        print(f"Error en get_users: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Ocurrió un error inesperado al obtener los usuarios"
        )

        
@user_route.post("/", status_code=201)
async def get_last_row(jwt_dependency: jwt_dependecy, new_user: new_user, session: Session = Depends(get_db)):
    try:
        # max_id = session.query(func.max(User.c.id)).first()
        #🎃 1|CUIDADO # SI VARIAS PERSONAS CREAN PUEDE HABER DUPLICIDAD DE ID, LO MEJOR ES CONGELAR MIENTRAS SE CONSULTA
        #🎃 2|CUIDADO # TAMBIEN SE TIENE QUE CAMBIAR LA FECHA Y HORA DE EDICION O CREACION CON EL DEL SERVIDOR
        max_id = session.query(func.max(User.c.id)).scalar()
        next_id = (max_id or 0) + 1

        stmt = (
                insert(User).
                values(
                    # id = int(max_id[0]) + 1,
                    id = next_id,
                    idDoc= new_user.docNumber or '',
                    user= new_user.user or '',
                    pw= hash_password(new_user.pwd) if new_user.pwd else '',
                    editDate= new_user.editDate or '',
                    creationDate= new_user.creationDate or '',
                    userName= new_user.userName or '',
                    enabled= b'\x01' #esta activo desde la creacion
                    )
                )
        
        # 3. Ejecutar y persistir
        session.execute(stmt)
        session.commit()
        
        return {"status": "success", "message": "Usuario creado", 'id': next_id}
    
    except SQLAlchemyError as e:
        session.rollback()
        # Logueamos el error real en consola para debugging
        print(f"SQLAlchemy Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error en la base de datos al crear el usuario"
        )
    
    except Exception as e:
        session.rollback()
        print(f"Unexpected Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno del servidor"
        )