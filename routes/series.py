from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, asc, func, insert, and_, desc, text, update, case, delete, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlmodel.docseries import DocSeries
from sqlmodel.doctype import DocType
from sqlmodel.ware import Ware
from basemodel.series import series_request, series_create_request
from functions.sales import generar_ticket, build_body_ticket, generar_ticket_close
from utils.validate_jwt import jwt_dependecy
from routes.authorization import get_user_permissions_by_module
from routes.catalogs import Get_Time
from config.db import con, session
from datetime import datetime as dt, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

series_route = APIRouter(
    prefix = '/series',
    tags=['Series']
)

@series_route.get("/get_series_data_by_ware/", status_code=200)
async def Get_Series_Data_By_Ware(series_body: series_request = Depends(), payload: jwt_dependecy = None):
    returned_value = {}
    try:

        def transform_series_list(series_list):
            # Mapas de conversión
            doc_type_map = {
                "NV": "Nota de Venta",
                "BOL": "Boleta",
                "FAC": "Factura"
            }

            status_map = {
                "Reserved": "Reservado",
                "Active": "Activo",
                "Blocked": "Bloqueado"
            }

            transformed = []

            for item in series_list:
                new_item = item.copy()  # evitar modificar el original

                # Convertir DocTypeCode
                dt = new_item.get("DocTypeCode")
                new_item["DocTypeCode"] = doc_type_map.get(dt, dt)

                # Convertir Status
                st = new_item.get("Status")
                new_item["Status"] = status_map.get(st, st)

                transformed.append(new_item)

            return transformed
            
        #Validacion MODULO NATIVO: SLS
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')
        
        if isinstance(permisos, list) and 'SLS_SLD' in permisos: #VERIFICA PERMISO VER SERIES
       
            stmt = (select( DocSeries
                        )
                    .filter(
                        DocSeries.c.WareCode == series_body.WareID,
                        DocSeries.c.SeriesType == series_body.SerieType #Regular, Deferred
                    )
                    .order_by(desc(DocSeries.c.SeriesCode))
                    )

            returned_list = [dict(r) for r in session.execute(stmt).mappings().all()]

            returned_list = transform_series_list(returned_list)
            
            returned_value.update({"status": True, 
                                   "message": "ok",
                                   "data": returned_list,
                                    }
                                   )

        else:
            returned_value.update({
                                    "status": False, 
                                    "message": "No cuenta con permisos para revisar información", 
                                    "data": {},
                                    }
                                )

    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()
        returned_value = []

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()
        returned_value = []

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
        returned_value = []

    finally:
        session.close()
        return returned_value

@series_route.get("/get_series_by_code/", status_code=200)
async def Get_Series_By_Code(series_body: series_request = Depends(), payload: jwt_dependecy = None):
    
    status_code = 200
    returned_value = {}
    try:
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')

        if series_body.SeriesCode is None and isinstance(permisos, list) and 'SLS_CSR' in permisos: #Modo crear
            #consulta tipos de documento
            stmt = (select( 
                            DocType.c.DocTypeCode.label("code"),
                            DocType.c.DocTypeName.label("name")
                           )
                    )
            doctype_list = [dict(r) for r in session.execute(stmt).mappings().all()]
            
            #consulta tipos de documento
            stmt = (select( 
                            Ware.c.id.label("code"),
                            Ware.c.code.label("name")
                           )
                    .filter(Ware.c.enabled == 1, Ware.c.isPos == 1) #tiene que esta habilitado y ser pos
                    )
            wares_list = [dict(r) for r in session.execute(stmt).mappings().all()]
            

            init = {
                "codigo": None,
                "tipoDoc": {
                    "current": None,
                    "options": doctype_list
                },
                "almacen": {
                    "current": None,
                    "options": wares_list
                },
                "tipoSerie": {
                    "current": None,
                    "options": [{"code": "Regular", "name": "Regular"}, {"code": "Deferred", "name": "Rezagado"}]
                },
                "prefijo": None,
                "estado": "RESERVADO" # POR DEFECTO
            }
            
            returned_value.update({
                                    "status": True,
                                    "message": f"Ok!", 
                                    "data": init,
                                    }
                                )
            status_code = 200
        elif series_body.SeriesCode is None and isinstance(permisos, list) and 'SLS_CSR' not in permisos: #Modo crear sin permiso
            returned_value.update({
                                    "status": False, 
                                    "message": f"No tiene permisos para crear series", 
                                    "data": {},
                                    }
                                )
            status_code = 422

        elif series_body.SeriesCode is not None and isinstance(permisos, list) and 'SLS_ESR' in permisos: #Modo editar
            
            #consulta datos serie
            stmt = (select(DocSeries).filter(DocSeries.c.SeriesCode == series_body.SeriesCode))

            serie = session.execute(stmt).mappings().first()

            if serie: #existe la serie


                #consulta tipos de documento
                stmt = (select( 
                                DocType.c.DocTypeCode.label("code"),
                                DocType.c.DocTypeName.label("name")
                            )
                        )
                doctype_list = [dict(r) for r in session.execute(stmt).mappings().all()]
                
                #consulta almacenes
                stmt = (select( 
                                Ware.c.id.label("code"),
                                Ware.c.code.label("name")
                            )
                        .filter(Ware.c.enabled == 1, Ware.c.isPos == 1) #tiene que esta habilitado y ser pos
                        )
                wares_list = [dict(r) for r in session.execute(stmt).mappings().all()]
                

                init = {
                    "codigo": serie["SeriesCode"],
                    "tipoDoc": {
                        "current": serie["DocTypeCode"],
                        "options": doctype_list
                    },
                    "almacen": {
                        "current": serie["WareCode"],
                        "options": wares_list
                    },
                    "tipoSerie": {
                        "current": serie["SeriesType"],
                        "options": [{"code": "Regular", "name": "Regular"}, {"code": "Deferred", "name": "Rezagado"}]
                    },
                    "prefijo": serie["Prefix"],
                    "estado": "ACTIVO" if serie["Status"] == 'Active' else "RESERVADO" # POR DEFECTO
                }
            
                returned_value.update({
                                        "status": True,
                                        "message": f"Ok!", 
                                        "data": init,
                                        }
                                    )
                status_code = 200

            else:
                returned_value.update({
                                        "status": False, 
                                        "message": f"La serie no existe, revisar!", 
                                        "data": {},
                                        }
                                    )
                status_code = 422


        
        elif series_body.SeriesCode is not None and isinstance(permisos, list) and 'SLS_ESR' not in permisos: #Modo editar sin permiso
            returned_value.update({
                                    "status": False, 
                                    "message": f"No tiene permisos para editar series", 
                                    "data": {},
                                    }
                                )
            status_code = 422

        else:
            returned_value.update({
                                    "status": False, 
                                    "message": f"Error: Posible inexistencia de serie", 
                                    "data": {},
                                    }
                                )
            status_code = 422

    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()
        returned_value = []

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()
        returned_value = []

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
        returned_value = []

    finally:
        session.close()
        return JSONResponse(
            status_code=status_code,
            content= returned_value
            )

@series_route.post("/create_new_serie/", status_code=201)
async def Create_Serie(series_body: series_create_request, payload: jwt_dependecy = None):
    status_code = 201
    returned_value = {}
    try:
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')

        if isinstance(permisos, list) and 'SLS_CSR' in permisos: #Modo crear
            
            async def create_serie(body_x: series_create_request = None, user=None):
                doc_type_map = {
                "NV": "Nota de Venta",
                "BOL": "Boleta",
                "FAC": "Factura"
                }

                status_map = {
                "Reserved": "Reservado",
                "Active": "Activo",
                "Blocked": "Bloqueado"
                }
                
                create_date = await Get_Time()
                
                stmt = (insert(DocSeries)
                        .values(
                            SeriesCode=body_x.codigo,
                            DocTypeCode=body_x.tipoDoc,
                            Prefix=body_x.prefijo,
                            LastNumber=0,
                            WareCode=body_x.almacen,
                            SeriesType=body_x.tipoSerie,
                            Status=body_x.estado,
                            CreateDate=create_date["lima_bd_format"],
                            UpdateUser=user
                            )
                        )
                
                affected = session.execute(stmt)

                if affected.rowcount > 0:  #filas afectadas mayor a 0 ✅, EMPIEZA CON REGISTRO DE LINEAS HIJAS
                    session.commit() #AQUI TERMINA TODO CON UN COMMIT 🎭🎭🎭
                    
                    stmt = (select(DocSeries).filter(DocSeries.c.SeriesCode == body_x.codigo))
                    
                    serie = dict(session.execute(stmt).mappings().first())

                    session.close()

                    for key, value in serie.items():
                        if isinstance(value, dt):
                            serie[key] = value.isoformat()  # o value.strftime('%Y-%m-%d %H:%M:%S')

                        elif key == 'DocTypeCode':
                            dt_x = serie[key]
                            serie[key] = doc_type_map.get(dt_x, dt_x)
                        
                        elif key == 'Status':
                            dt_y = serie[key]
                            serie[key] = status_map.get(dt_y, dt_y)

                    return 201, serie
                
                else:
                    return 422, {}

            
            #si es active, no debe existir reservado para que se salte esta serie
            stmt = (select(DocSeries)
                    .filter(and_(or_(DocSeries.c.Status == 'Reserved', DocSeries.c.Status == 'Active'), #estado
                            DocSeries.c.WareCode == series_body.almacen, #[almacen]
                            DocSeries.c.SeriesType ==  series_body.tipoSerie, #tipo serie [regular, rezagado]
                            DocSeries.c.DocTypeCode == series_body.tipoDoc) #tipo documento
                        )
                    )
            serie = session.execute(stmt).mappings().all()

            if series_body.estado == 'Active':

                if serie: #existe un reservado o activo, no puede crear
                    returned_value.update({
                                            "status": False,
                                            "message": "Ya existen series en uso para el almacen y tipo de documento!", 
                                            "data": {},
                                            }
                                        )
                    status_code = 422

                else:
                    status_code, data = await create_serie(body_x=series_body, user=payload.get("username"))
                    returned_value.update({
                                            "status": True,
                                            "message": "Ok!",
                                            "data": data,
                                            }
                                        )
                    

            elif series_body.estado == 'Reserved':

                if serie and any(item.get("Status") == "Reserved" for item in serie): #verifica si existe algun reserved, no puede crear
                    returned_value.update({
                                            "status": False,
                                            "message": "Ya existe una serie en reserva para el almacen y tipo de documento!", 
                                            "data": {},
                                            }
                                        )
                    status_code = 422

                else:
                    status_code, data = await create_serie(body_x=series_body, user=payload.get("username"))
                    returned_value.update({
                                            "status": True,
                                            "message": "Ok!",
                                            "data": data,
                                            }
                                        )
        else:
            returned_value.update({
                                    "status": False, 
                                    "message": f"Error: Posible inexistencia de serie", 
                                    "data": {},
                                    }
                                )
            status_code = 422

    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()
        returned_value = []

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()
        returned_value = []

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
        returned_value = []

    finally:
        session.close()
        return JSONResponse(
            status_code=status_code,
            content= returned_value
            )

@series_route.patch("/edit_serie_by_code/", status_code=200)
async def Edit_Serie_By_Code(series_body: series_create_request, payload: jwt_dependecy = None):
    status_code = 200
    returned_value = {}
    try:
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')

        if isinstance(permisos, list) and 'SLS_ESR' in permisos: #Modo editar
            
            async def edit_serie(body_x: series_create_request = None, user=None):
                doc_type_map = {
                    "NV": "Nota de Venta",
                    "BOL": "Boleta",
                    "FAC": "Factura"
                }

                status_map = {
                    "Reserved": "Reservado",
                    "Active": "Activo",
                    "Blocked": "Bloqueado"
                }
                
                create_date = await Get_Time()
                
                stmt = (update(DocSeries)
                        .where(DocSeries.c.SeriesCode == body_x.codigo)
                        .values(
                            Prefix=body_x.prefijo,
                            Status=body_x.estado,
                            UpdateDate=create_date["lima_bd_format"],
                            UpdateUser=user
                            #SeriesCode=body_x.codigo,
                            #DocTypeCode=body_x.tipoDoc,
                            #LastNumber=0,
                            #WareCode=body_x.almacen,
                            #SeriesType=body_x.tipoSerie,
                            )
                        )
                
                affected = session.execute(stmt)

                if affected.rowcount > 0:  #filas afectadas mayor a 0 ✅, EMPIEZA CON REGISTRO DE LINEAS HIJAS
                    session.commit() #AQUI TERMINA TODO CON UN COMMIT 🎭🎭🎭
                    
                    stmt = (select(DocSeries).filter(DocSeries.c.SeriesCode == body_x.codigo))
                    
                    serie = dict(session.execute(stmt).mappings().first())

                    session.close()

                    for key, value in serie.items():
                        if isinstance(value, dt):
                            serie[key] = value.isoformat()  # o value.strftime('%Y-%m-%d %H:%M:%S')

                        elif key == 'DocTypeCode':
                            dt_x = serie[key]
                            serie[key] = doc_type_map.get(dt_x, dt_x)
                        
                        elif key == 'Status':
                            dt_y = serie[key]
                            serie[key] = status_map.get(dt_y, dt_y)

                    return 200, serie
                
                else:
                    return 422, {}

            if series_body.estado == 'Active':

                stmt = (select(DocSeries)
                        .filter(DocSeries.c.Status == 'Active', #estado
                                DocSeries.c.WareCode == series_body.almacen, #[almacen]
                                DocSeries.c.SeriesType ==  series_body.tipoSerie, #tipo serie [regular, rezagado]
                                DocSeries.c.DocTypeCode == series_body.tipoDoc #tipo documento
                                )
                        )
                
                serie = session.execute(stmt).mappings().first()

                if serie: #ya existe una serie con status activo, asi que no se puede cambiar
                    
                    returned_value.update({
                                            "status": False,
                                            "message": "Ya existe una serie activada, revisar!", 
                                            "data": {},
                                            }
                                        )
                    status_code = 422

                    return JSONResponse(
                    status_code=status_code,
                    content= returned_value
                    )


            status_code, data = await edit_serie(body_x=series_body, user=payload.get("username"))
            returned_value.update({
                                    "status": True,
                                    "message": "Ok!",
                                    "data": data,
                                    }
                                )
            
            return JSONResponse(
            status_code=status_code,
            content= returned_value
            )
                    


        else:
            returned_value.update({
                                    "status": False, 
                                    "message": f"No cuenta con permisos para editar series", 
                                    "data": {},
                                    }
                                )
            status_code = 422
        
            return JSONResponse(
            status_code=status_code,
            content= returned_value
            )

    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()
        returned_value = []

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()
        returned_value = []

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
        returned_value = []

    finally:
        session.close()

    
@series_route.delete("/delete_series_by_code/", status_code=200)
async def Delete_Series_By_Code(series_body: series_request, payload: jwt_dependecy = None):
    status_code = 200
    returned_value = {}
    try:
        #Validacion MODULO NATIVO: SLS
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')
        
        if isinstance(permisos, list) and 'SLS_DSR' in permisos: #VERIFICA PERMISO VER SERIES
       
            stmt = (select( DocSeries.c.Status
                        )
                    .filter(
                        DocSeries.c.SeriesCode == series_body.SeriesCode,
                    )
                    )

            returned_item = session.execute(stmt).mappings().first()

            
            if bool(returned_item) and returned_item["Status"] != "Reserved":
            
                returned_value.update({"status": False, 
                                    "message": "No puede eliminar una serie que no se encuentre en reserva",
                                    "data": {},
                                        }
                                    )
                status_code = 422
                
            elif (bool(returned_item)):
                stmt = (delete( DocSeries
                        )
                    .filter(
                        DocSeries.c.SeriesCode == series_body.SeriesCode,
                    )
                    )

                affected = session.execute(stmt)
                session.commit()
                returned_value.update({
                                        "status": False, 
                                        "message": f"Serie {series_body.SeriesCode} eliminada con exito!", 
                                        "data": {},
                                        }
                                    )
                status_code = 200

            else:
                returned_value.update({
                                        "status": False, 
                                        "message": f"Error: Posible inexistencia de serie", 
                                        "data": {},
                                        }
                                    )
                status_code = 422


        else:
            status_code = 422
            returned_value.update({
                                    "status": False, 
                                    "message": "No cuenta con permisos para eliminar series", 
                                    "data": {},
                                    }
                                )

    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()
        returned_value = []

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()
        returned_value = []

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
        returned_value = []

    finally:
        session.close()
        return JSONResponse(
            status_code=status_code,
            content= returned_value
            )
        # return returned_value