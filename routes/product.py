import json
import gspread
import base64
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, text, func, insert, update
from typing import Optional
from utils.validate_jwt import jwt_dependecy
from config.db import con, session, CREDENTIALS_JSON, BUCKET_NAME, AWS_REGION
from config.s3_aws import get_s3_client
from sqlmodel.product import Product
from sqlmodel.uploads import Uploads
from sqlmodel.objectfiles import ObjectFiles
from sqlmodel.ware_product import Ware_Product
from sqlmodel.user_perm_mdl import User_perm_mdl
from functions.product import get_all_publishers, generate_filename
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
from gspread.exceptions import GSpreadException
from basemodel.product import product_maintenance, product_basic_model
from sqlalchemy.exc import SQLAlchemyError
from routes.authorization import get_user_permissions_by_module
from fastapi import Response
from routes.catalogs import Get_Time
from botocore.exceptions import (
    NoCredentialsError,
    PartialCredentialsError,
    ParamValidationError,
    ClientError
)

product_route = APIRouter(
    prefix = '/product',
    tags=['Product']
)

##Activar credenciales google
# Parse the JSON string into a dictionary
credentials_dict = json.loads(CREDENTIALS_JSON)

# creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
creds = Credentials.from_service_account_info(credentials_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])


def get_isbn_isExists(isbn):
    return f"pr.isbn like '%{isbn.upper()}%' and " if bool(isbn) else " "


@product_route.get("/", status_code=200)
async def get_all_products(jwt_dependency: jwt_dependecy):
    return []
    # if jwt_dependency:
    #     return {
    #         "content": []
    #     }
    # else:
    #     raise HTTPException(status_code=401, detail='Authentication failed')


@product_route.get("/stock_by_product_attribute", status_code=200)
async def get_stock_by_product_attribute(jwt_dependency: jwt_dependecy,
                                Isbn: Optional[str] = "",
                                Title: Optional[str] = "",
                                Autor: Optional[str] = "",
                                Publisher: Optional[str] = "",
                                ):
    # if not(jwt_dependency):
    if not(True):
        raise HTTPException(
            status_code=498,
            detail='Invalid Access Token',
        )
    else:
        status = False
        result = []
        try:
            if bool(Isbn) or bool(Title) or bool(Autor) or bool(Publisher):
                query = f"""wp.idProduct as idProduct, 
                pr.isbn, pr.title, pr.autor, pr.publisher, 
                wr.code, wp.pvNew, wp.isEnabled as enabled, 
                wp.qtyNew as stock from ware_product wp 
                inner join product pr on wp.idProduct = pr.id 
                inner join ware wr on wp.idWare = wr.id 
                where {get_isbn_isExists(Isbn)} pr.title like '%{Title.upper()}%' 
                and pr.autor like '%{Autor.upper()}%' 
                and pr.publisher like '%{Publisher.upper()}%' 
                and wr.enabled = 1
                group by wp.idProduct , pr.isbn, pr.title, pr.publisher, wr.code, wp.pvNew, wp.isEnabled, wp.qtyNew 
                order by wp.idProduct asc"""
                stock = session.execute(select(text(query)))
                data = stock.fetchall()
                # result = []
                for item in data:
                    _index = next((index for (index, d) in enumerate(result) if d["id"] == item[0]), None)
                    if _index is None:
                        result.append({
                            "id": item[0],
                            "isbn": item[1],
                            "title": item[2],
                            "autor": item[3],
                            "publisher": item[4],
                            "isEnabled": {item[5]: item[7] != b'\x00'},
                            "stock": {item[5]: int(item[8])},
                            "pvp": {item[5]: item[6]}
                        })
                    else:
                        # result[_index]["isEnabled"] = result[_index]["isEnabled"] or (item[7] != b'\x00')
                        result[_index]["isEnabled"][item[5]] = item[7] != b'\x00'
                        result[_index]["stock"][item[5]] = int(item[8])
                        result[_index]["pvp"][item[5]] = item[6]
        
                status = True
                # return JSONResponse(
                # status_code=200,
                # content={"result": result}
                # )
            else:
                raise HTTPException(status_code=404, detail='Nothing to show you')
        except:
            session.rollback()
            # raise HTTPException(status_code=404, detail='Nothing to show you')
            # raise
        finally:
            session.close()
            if not status:
                raise HTTPException(status_code=404, detail='Nothing to show you')
            elif status:
                return JSONResponse(
                status_code=200,
                content={"result": result}
                )
        
@product_route.post("/request_maintenance", status_code=200)
async def request_product_maintenance(jwt_dependency: jwt_dependecy, product_maintenance: product_maintenance):
    data = [
        product_maintenance.code,
        product_maintenance.isbn ,
        product_maintenance.title,
        product_maintenance.autor,
        product_maintenance.publisher,
        '', #proveedor
        '', #lenguaje
        '', #paginas
        '', #cubierta
        '', #ancho
        '', #alto
        product_maintenance.pv,
        product_maintenance.pvp,
        '', #"edicion"
        '', #"año mes edicion"
        product_maintenance.warehouse,
        product_maintenance.rqType,
        product_maintenance.asker,
        product_maintenance.date,
        ]
    try:
        client = gspread.authorize(creds)
        sheet_id = '1ArWWeiC9JsiLJw021O3EzS9i1XLMAbg0Z8S9b-5rmtY'
        sheet = client.open_by_key(sheet_id)
        row_counts = sheet.sheet1.row_count
        sheet.sheet1.append_row(data)
        return {"state": True}
    except GoogleAuthError as auth_error:
        print(f"Authentication error: {auth_error}")
        return {"state": False}
    except GSpreadException as gs_error:
        print(f"Gspread error: {gs_error}")
        return {"state": True}
    except Exception as e:
        print(f"get_last_row:get: An error ocurred: {e}")
        return {"state": True}

@product_route.delete("/", status_code=200)
async def delete_product(jwt_dependency: jwt_dependecy, idProduct: str = None, curDate: str = None, nameModule: str = None):
    #cuando jwt_dependency es false, es por que el token ya vencio
    if jwt_dependency[0]:
        try:
            #verificamos que no exista stock
            stock_exits = session.query(func.sum(Ware_Product.c.qtyNew)).filter(Ware_Product.c.idProduct == idProduct).scalar()
            if stock_exits == 0:
                response = session.query(User_perm_mdl).filter(User_perm_mdl.c.mdlCode == nameModule, 
                                                    User_perm_mdl.c.permCode == 'DPR',
                                                    User_perm_mdl.c.user == jwt_dependency[1]).first()
                if response is not None:
                    try:
                        if((idProduct is not None and curDate is not None) and (idProduct != '' and curDate != '')):
                            rows_affected = session.query(Product).filter(Product.c.id == idProduct).update({
                                "isDelete": b'\x01',
                                "editDate": curDate})
                            
                            session.commit()
                            session.close()
                            return {
                                'status': 'ok'
                            }
                        else:
                            return JSONResponse(
                                status_code=400,
                                content={"message": 'Bad Request', "status": "Check productId or moduleCode or editDate", "code": 400}
                            )
                    except Exception as e:
                        print(f"delete_product: {e}")
                        session.close()
                        return False
                else:
                    session.close()
                    return JSONResponse(
                        status_code=401,
                        content={"message": 'Unauthorized', "status": "No tiene permisos para esta operación", "code": 401}
                    )
            else:
                session.close()
                return JSONResponse(
                    status_code=401,
                    content={"message": 'Unauthorized', "status": "El producto contiene stock, primero regularice", "code": 401}
                )
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            print(f"SQLAlchemy error occurred: {e}")
    else:
        return JSONResponse(
            status_code=401,
            content={"message": 'Token expired', "status": "error", "code": 401}
        )
    

@product_route.get("/getlastimage", description="Obtiene imagen de producto desde bucket s3 con el codigo interno del producto seguido de la extension del formato")
async def obtener_imagen(jwt_dependency: jwt_dependecy, body: product_basic_model = Depends(), s3 = Depends(get_s3_client)):
    status_code = 422
    returned_value = {
        "message": "error",
        "data": None, 
        "action": None,
        "url": None
    }
    
    try:
        if not(body.DocEntry):
            returned_value.update({"message": "Ingrese un ID de Producto Valido!"})
        else:
            stmt = (select(Product.c.FileName)
                    .filter(Product.c.id == int(body.DocEntry)))
            obj = session.execute(stmt).mappings().first()
            
            if obj["FileName"]:
                # CASO 1: EXISTE EN DB PERO NO EN REMOTO ó EXISTE EN DB Y ARCHIVO REMOTO DIFERENTE
                if not(body.FileName) or (obj["FileName"] != body.FileName): #RPTA: TRAE LA URL DESDE S3

                    # inicia verificacion de existencia
                    try:
                        s3.head_object(Bucket=BUCKET_NAME, Key=obj["FileName"])
                    except ClientError:
                        raise HTTPException(status_code=404, detail="Archivo no existe en S3")
                    # culmina verificacion de existencia

                    ##ARMA EL BODY
                    status_code = 200
                    returned_value.update(
                                            {
                                            "data": {"FileName": obj["FileName"]},
                                            "message": "FileName encontrado",
                                            "action": "update",
                                            "url": f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{obj['FileName']}"
                                            }   
                                        )
                
                elif (obj["FileName"] == body.FileName):
                    status_code = 200
                    returned_value.update(
                                            {
                                            "data": {"FileName": obj["FileName"]},
                                            "message": "FileName encontrado!",
                                            "action": "noaction",
                                            "url": None
                                            }   
                                        )
                    
                else:
                    status_code = 422
                    returned_value.update(
                                            {
                                            "data": None,
                                            "message": None,
                                            "action": None,
                                            "url": None
                                            }   
                                        )
                
            else:
                status_code = 200
                returned_value.update(
                                        {"data": None,
                                        "message": "FileName no existe!",
                                        "action": "delete",
                                        "url": None
                                        }
                                       )

    except Exception as e:
        session.rollback()
        session.close()
        raise HTTPException(status_code=404, detail="Error al descargar de S3")
    
    finally:
        session.close()
        return JSONResponse(
            status_code= status_code,
            content= returned_value
        )
    

@product_route.get("/uploads/presign", description="Optine url prefirmada para carga ", status_code=200)
async def obtener_url_prefirmada_para_actualizacion(payload: jwt_dependecy, body: product_basic_model = Depends(), s3 = Depends(get_s3_client)):
    status_code = 422
    returned_value = {
        "message": "Indeterminado",
        "data": {}, 
        "url": None
    }

    try:

        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='IVT')

        if isinstance(permisos, list) and 'IVT_UIM' not in permisos: #APRUEBA PERMISO IVT_UIM: permiso para actualizar imagen
            raise RuntimeError("No cuenta con permisos para actualizar imagenes")


        # 0| CONSULTA NOMBRE ACTUAL DE ARCHIVO
        Result = session.execute(select(Product.c.FileName).filter(Product.c.id == body.DocEntry)).mappings().first()


        # 1| GENERACION DE NOMBRE DE ARCHIVO CON EXTENSION SEGUN EL CONTENT TYPE
        FileName = generate_filename(numero=body.DocEntry, extension=body.ContentType, valor_inicial=Result['FileName'] if 'FileName' in Result else None)

        if FileName: #verifica que existe nombre filename

            content_type=f'image/{body.ContentType}'

            url = s3.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": BUCKET_NAME,
                        "Key": FileName,
                        "ContentType": content_type,
                    },
                    ExpiresIn=30  # 30 segundos
                )

            if not isinstance(url, str) or not url.startswith("http"):
                raise RuntimeError("Invalid presigned URL generated")
            
            returned_value.update({
                "url": url,
                "data": {
                    "prev_filename": None,
                    "new_filename": None,
                    "UploadEntry": None,
                    "ContentType": None
                }
            })
            
            #registra en tabla uploads
            if url:
                date = await Get_Time() #<-- obtiene hora
                # LastDate= date["lima_bd_format"]
                stmt = (insert(Uploads).
                        values(
                            FileName= FileName,
                            ContentType= body.ContentType,
                            Status= 'P',
                            UserSign= payload.get("username"),
                            LastDate= date["lima_bd_format"]
                        )
                )

                affected = session.execute(stmt)

                if affected.rowcount > 0:  #filas afectadas mayor a 0 ✅, EMPIEZA CON REGISTRO DE LINEAS HIJAS
                    Uuid = affected.inserted_primary_key[0]
                    session.commit()

                    returned_value.update({
                        "message": "ok",
                        "data": {
                            "prev_filename": Result['FileName'],
                            "new_filename": FileName,
                            "UploadEntry": Uuid,
                            "ContentType": content_type
                        }
                    })
                    status_code = 200
        
    except (
        NoCredentialsError,
        PartialCredentialsError,
        ParamValidationError,
        ClientError
    ) as e:
        returned_value.update({"message": f"Failed to generate presigned URL: {e}"})
        status_code = 422
        session.close()
        session.rollback()
        
    except Exception as e:
        session.rollback()
        session.close()
        returned_value.update({
            "message": f"{e}"
        })
        status_code = 422

    
    finally:
        session.close()
        return JSONResponse(
            status_code= status_code,
            content= returned_value
        )

@product_route.post("/uploads/confirm", description="confirma carga de archivos desde el frondend para objeto de tipo producto", status_code=200)
async def confirmar_archivo_de_producto(payload: jwt_dependecy, body: product_basic_model, s3 = Depends(get_s3_client)):
    status_code = 422
    returned_value = {
        "message": "Indeterminado",
        "data": {}, 
        "url": None
    }

    try:
        #0| CAMBIA DE ESTADO PENDING TO CLOSE
        date = await Get_Time() #<-- obtiene hora
        
        stmt = (update(Uploads)
                .where(Uploads.c.Uuid == body.UploadEntry)
                .values(
                Status=body.ConfirmStatus or None,
                LastDate=date["lima_bd_format"],
                )
            )
        # Ejecutar la instrucción de actualización
        result = session.execute(stmt)
        
        if result.rowcount == 0 or body.ConfirmStatus not in ('C', 'P'): #no afecta ninguna fila o es failed
            session.rollback()
            returned_value.update({"message": "Error actualizando tabla upload o error durante carga a bucket de imagenes"})
            raise RuntimeError("Error actualizando tabla upload o error durante carga a bucket de imagenes")
        
        session.commit()

        #2| AGREGA FILA EN MANEJO DE VERSIONES DE DOCUMENTOS DE OBJECTO
        #2.1| DESACTIVA VERSIONES ANTERIORES
        stmt_deactivate = (
            update(ObjectFiles)
            .where(
                ObjectFiles.c.EntityType  == 'ITEM',
                ObjectFiles.c.EntityEntry == body.DocEntry,
                ObjectFiles.c.FileRole    == body.FileRole,
                ObjectFiles.c.IsActive    == 'Y'
            )
            .values(
                IsActive='N',
                LastDate=date["lima_bd_format"]
            )
        )
        session.execute(stmt_deactivate)
        session.commit()

        #2.2| ACTIVA VERSION RECIENTE
        stmt = (insert(ObjectFiles).
                values(
                    EntityType= 'ITEM', #ITEM, USER, STORE, BP | ESTE VALOR ESTA HARDCODEADO POR QUE ESTA EN LA RUTA PRODUCT| PRONTO HACER RUTA GENERICA 🎃
                    EntityEntry= body.DocEntry,
                    UploadEntry= body.UploadEntry,
                    FileRole= body.FileRole, #IM: IMAGEN, FT: FICHA TECNICA, LG: LOGO, AV:AVATAR, MN: MANUAL, CT: CERTIFICADO
                    IsActive= 'Y',
                    LastDate= date["lima_bd_format"]
                )
        )

        # Ejecutar la instrucción de actualización
        result_1 = session.execute(stmt)

        if result_1.rowcount == 0: #no afecta ninguna fila o es failed
            session.rollback()
            returned_value.update({"message": "Error actualizando tabla de control de versiones ojectfile, no se agrego filas"})
            raise RuntimeError("Error actualizando tabla de control de versiones ojectfile, no se agrego filas")

        session.commit()

        #3| ACTUALIZA EL NOMBRE DEL ARCHIVO EN TABLA MAESTRA
        new_fileName=session.execute(select(Uploads.c.FileName).filter(Uploads.c.Uuid == body.UploadEntry)).mappings().first()
        
        stmt_update = (
            update(Product)
            .where(
                Product.c.id  == body.DocEntry,
            )
            .values(
                FileName= 'error' if not new_fileName else new_fileName["FileName"],
                editDate=date["lima_bd_format"]
            )
        )
        result = session.execute(stmt_update)
        
        if result.rowcount == 0: #no afecta ninguna fila o es failed
            session.rollback()
            returned_value.update({"message": "Error durante actualizacion de dato FileName en tabla maestra ITEM"})
            raise RuntimeError("Error durante actualizacion de dato FileName en tabla maestra ITEM")
        
        session.commit()
        status_code = 200
        returned_value.update({"message": "ok!"})

        #3| ELIMINA VERSION ANTIGUA DE BUCKET SI EXISTE
        if body.prevFileName: #en caso existe archivo antiguo, elimina
            s3.delete_object(
                Bucket=BUCKET_NAME,
                Key=body.prevFileName
            )

    except (
        NoCredentialsError,
        PartialCredentialsError,
        ParamValidationError,
        ClientError
    ) as e:
        returned_value.update({"message": f"Error intentando eliminar la version anterior: {e}"})
        status_code = 422
        session.close()
        session.rollback()

    except Exception as e:
        session.rollback()
        session.close()
        returned_value.update({
            "message": f"An error ocurred: {e}"
        })
        status_code = 422

    
    finally:
        session.close()
        return JSONResponse(
            status_code= status_code,
            content= returned_value
        )

        
