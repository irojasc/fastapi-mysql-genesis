from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, asc, func, insert, and_, desc, text, update, case
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlmodel.cashregister import CashRegister
from sqlmodel.docseries import DocSeries
from sqlmodel.salesorder import SalesOrder
from sqlmodel.salesorderdetail import SalesOrderDetail
from sqlmodel.salesordersunat import SalesOrderSunat
from sqlmodel.sunatcodes import SunatCodes
from sqlmodel.doctype import DocType
from sqlmodel.company import Company
from sqlmodel.companycontacts import CompanyContacts
from sqlmodel.pymntgroup import PymntGroup
from sqlmodel.product import Product
from sqlmodel.odtc import ODTC
from sqlmodel.oafv import OAFV
from basemodel.sales import cash_register, sales_order, Body_Ticket, Body_Ticket_Close, Item_Ticket_Close, sales_request, external_document
from basemodel.series import series_internal
from functions.sales import generar_ticket, build_body_ticket, generar_ticket_close, format_to_8digits, sincronizar_documentos_pendientes
from utils.validate_jwt import jwt_dependecy
from routes.authorization import get_user_permissions_by_module
from routes.catalogs import Get_Time
from config.db import con, session, MIFACT_MIRUC
from datetime import datetime as dt, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from service.sales import post_sales_document
import json

sales_route = APIRouter(
    prefix = '/sales',
    tags=['Sales']
)

@sales_route.post("/open_cash_register/", status_code=201)
async def Open_Cash_Register(cash_register_body: cash_register, payload: jwt_dependecy):
    status_code = 422
    content={
        "body": {},
        "msg": "Error"
    }
    try:
        create_date = await Get_Time() #<-- obtiene hora

        #Validacion MODULO NATIVO: SLS
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')
        if isinstance(permisos, list) and 'SLS_CRG' in permisos: #APRUEBA PERMISO CRG
            
            #Validacion si tiene permisos para caja aperturada
            stmt = (select(CashRegister).filter(and_(CashRegister.c.User == payload.get("username"), CashRegister.c.Status == 'O' )))
            row = session.execute(stmt).mappings().first()

            if row is None:
                referencia = str(int(dt.now().timestamp()))
                stmt = (insert(CashRegister).
                        values(
                            CodeTS= referencia, #si dos graban al mismo tiempo, a uno va rechazar
                            WareID= cash_register_body.WareID,
                            User= payload.get("username") or None,
                            OpenDate= create_date["lima_bd_format"] or None,
                            CashOpen= cash_register_body.CashOpen,
                            Item2Code= cash_register_body.code2count,
                            Item2Total= cash_register_body.total2count,
                        ))
                affected = session.execute(stmt)
                session.commit()

                if affected.rowcount > 0:  #filas afectadas mayor a 0 ✅
                    status_code = 201
                    #aca se realiza la consulta
                    response = await Get_Cash_Register_By_Param(cash_register_body=cash_register(CodeTS = referencia))
                    response = [dict(r) for r in response]
                    if isinstance(response, list) and len(response) == 1:
                        #convierte datetime a string
                        for k, v in response[0].items():
                            if isinstance(v, dt):
                                response[0][k] = v.strftime("%d/%m %H:%M")
                            elif isinstance(v, Decimal):
                                response[0][k] = float(v)  
                        content.update({"body": response[0]}) #considerando que retornar un list con un 1 item
                        content.update({"msg": f'Caja creada: Referencia: {referencia}'})
            else:
                content.update({"msg": f"""Ya cuenta con una caja abierta: Referencia: {row["CodeTS"]}"""})
        else:
            content.update({"msg": "No cuenta con permisos para crear cajas"})

    except Exception as e:
        print(f"An error ocurred: {e}")
        content.update({"msg": f"An error ocurred: {e}"})
        session.rollback()
        session.close()

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        session.rollback()
        session.close()
        content.update({"msg": f"""Detalle SQLAlchemy: {e.orig}"""})

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        session.rollback()
        session.close()
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        content.update({"msg": f"""Error SQLAlchemy: {str(e.__dict__["orig"])}"""})
    finally:
    
        session.close()
        return JSONResponse(
            status_code=status_code,
            content= content
            )
    

@sales_route.get("/get_sales_order_by_cashregistercode/", status_code=200)
async def Get_Sales_Order_By_CashRegisterCode(cash_register_body: cash_register = Depends(), payload: jwt_dependecy = None):
    returned_value = []
    try:

        stmt = (select( SalesOrder.c.DocEntry,
                        SalesOrder.c.DocNum,
                        DocType.c.DocTypeCode.label("DocType"),
                        SalesOrder.c.DocDate,
                        Company.c.docName.label("CardName"),
                        SalesOrder.c.DocTotal,
                        SalesOrder.c.DocCur.label("Moneda"),
                        PymntGroup.c.PymntGroupName.label("TipoPago"),
                        SunatCodes.c.Dscp.label("Status"), #valor por defecto "" cuando sea null
                        SunatCodes.c.IsFinal.label("Status_level"),
                       )
                .join(DocType, SalesOrder.c.DocType == DocType.c.DocTypeCode)
                .join(Company, SalesOrder.c.CardCode == Company.c.cardCode)
                .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
                .join(SalesOrderSunat, SalesOrder.c.DocEntry == SalesOrderSunat.c.DocEntry, isouter=True)
                .join(SunatCodes, SalesOrderSunat.c.Status == SunatCodes.c.Code, isouter=True)
                .filter(SalesOrder.c.CashBoxTS == cash_register_body.CodeTS)
                .order_by(desc(SalesOrder.c.DocDate))
                )

        returned_value = [dict(r) for r in session.execute(stmt).mappings().all()]

        for item in returned_value:
            item["DocDate"] = item["DocDate"].strftime("%d/%m %H:%M")
        
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
    

@sales_route.get("/get_sales_order_by_ware_and_date/", status_code=200)
async def Get_Sales_Order_By_Ware_And_Date(cash_register_body: sales_request = Depends(), payload: jwt_dependecy = None):
    returned_value = {}
    date_current = cash_register_body.Date
    date_bottom = None
    date_top = None

    try:
        
        #Validacion MODULO NATIVO: SLS
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')
        
        if isinstance(permisos, list) and 'SLS_ASR' in permisos: #APRUEBA PERMISO SLS_ASR
            
            if isinstance(permisos, list) and 'SLS_WDY' in permisos: #APRUEBA PERMISO SLS_WDY, PARA VER TODOS LOS REGISTROS
                start_date = dt.strptime(cash_register_body.Date, "%Y-%m-%d")
                end_date = start_date + timedelta(days=1)
            else:
                async def validate_date_range(input_date_str: str) -> dict:

                    # Fecha superior: hoy (formato del sistema)
                    time_x = await Get_Time()
                    date_top = dt.strptime(time_x["lima_transfer_format"], "%Y-%m-%d").date()

                    # Fecha inferior: 4 días atrás
                    date_bottom = date_top - timedelta(days=4) # intervalo permitido para que los que no tienen permiso

                    # Convertimos input a fecha
                    try:
                        input_date = dt.strptime(input_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        # Si el input no tiene formato correcto, forzamos fecha superior
                        input_date = date_top

                    # Evaluación del rango
                    if input_date < date_bottom or input_date > date_top:
                        current_date = date_top
                    else:
                        current_date = input_date

                    # Construir respuesta en formato string
                    return date_top.strftime("%Y-%m-%d"), date_bottom.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")
                
                date_top, date_bottom, date_current  = await validate_date_range(input_date_str = cash_register_body.Date)
                
                # date_current = date_bottom
                start_date = dt.strptime(date_current, "%Y-%m-%d")
                end_date = start_date + timedelta(days=1)

       
            #FUNCIONA PARA CAMBIAR A BASE36
            def to_base36(num_str):
                num = int(num_str)
                chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                base36 = ""
                while num > 0:
                    num, i = divmod(num, 36)
                    base36 = chars[i] + base36
                return base36

            #FUNCIONA PARA DAR FORMATO CABECERA / DETALLE
            def build_sales_response(ventas):
                # --- 1) Calcular totales por tipo de pago ---
                totales = defaultdict(Decimal)

                for v in ventas:
                    totales[v["TipoPago"]] += v["DocTotal"]

                # Convertir Decimal → string para JSON seguro
                cabecera = {tipo: format(total, "f") for tipo, total in totales.items()}

                # --- 2) Preparar detalle con conversiones seguras ---
                detalle = []
                for v in ventas:
                    item = v.copy()
                    item["DocTotal"] = format(item["DocTotal"], "f")  # Decimal → string

                    # convertir fecha a un formato estándar
                    item["DocDate"] = item["DocDate"].strftime("%d/%m %H:%M")

                    # convertir CODETS a hex36
                    item["CodeTS"] = "" if item["CodeTS"] is None else to_base36(item["CodeTS"])

                    detalle.append(item)

                # --- 3) Armar diccionario final ---
                return {
                    "cabecera": cabecera,
                    "detalle": detalle
                }
                

            stmt = (select( SalesOrder.c.DocEntry,
                            SalesOrder.c.CashBoxTS.label("CodeTS"),
                            SalesOrder.c.DocNum,
                            SalesOrder.c.DocType,
                            SalesOrder.c.DocDate,
                            SalesOrder.c.SlpCode,
                            Company.c.docName.label("CardName"),
                            SalesOrder.c.DocTotal,
                            SalesOrder.c.DocCur.label("Moneda"),
                            PymntGroup.c.PymntGroupName.label("TipoPago"),
                            SunatCodes.c.Dscp.label("Status"), #valor por defecto "" cuando sea null
                            SunatCodes.c.IsFinal.label("Status_level")
                        )
                    .join(Company, SalesOrder.c.CardCode == Company.c.cardCode)
                    .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
                    .join(SalesOrderSunat, SalesOrder.c.DocEntry == SalesOrderSunat.c.DocEntry, isouter=True)
                    .join(SunatCodes, SalesOrderSunat.c.Status == SunatCodes.c.Code, isouter=True)
                    .join(CashRegister, SalesOrder.c.CashBoxTS == CashRegister.c.CodeTS)
                    .filter(
                        SalesOrder.c.DocDate >= start_date,
                        SalesOrder.c.DocDate < end_date,
                        CashRegister.c.WareID == cash_register_body.WareID
                    )
                    .order_by(desc(SalesOrder.c.DocDate))
                    )

            returned_value = [dict(r) for r in session.execute(stmt).mappings().all()]

            returned_value = build_sales_response(returned_value)
            returned_value.update({"status": True, 
                                   "message": "ok",
                                   "dates": {
                                        "date_current": date_current,
                                        "date_bottom": date_bottom,
                                        "date_top": date_top
                                        }
                                    }
                                   )

        else:
            returned_value.update({
                                    "status": False, 
                                    "message": "No cuenta con permisos revisar los reportes", 
                                    "cabecera": {}, 
                                    "detalle": [],
                                    "dates": {
                                        "date_current": date_current,
                                        "date_bottom": None,
                                        "date_top": None
                                        }
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

@sales_route.get("/get_detail_sales_order/", status_code=200)
async def Get_Detail_Sales_Order(cash_register_body: sales_request = Depends(), payload: jwt_dependecy = None):
    returned_value = {}
    date_current = cash_register_body.Date
    date_bottom = None
    date_top = None

    try:
        #Validacion MODULO NATIVO: SLS
        permisos = await get_user_permissions_by_module(user=payload.get("username"), module='SLS')
        
        if isinstance(permisos, list) and 'SLS_ASR' in permisos: #APRUEBA PERMISO SLS_ASR
            if isinstance(permisos, list) and 'SLS_WDY' in permisos: #APRUEBA PERMISO SLS_WDY, PARA VER TODOS LOS REGISTROS
                start_date = dt.strptime(cash_register_body.Date, "%Y-%m-%d")
                end_date = start_date + timedelta(days=1)
            else:
                async def validate_date_range(input_date_str: str) -> dict:

                    # Fecha superior: hoy (formato del sistema)
                    time_x = await Get_Time()
                    date_top = dt.strptime(time_x["lima_transfer_format"], "%Y-%m-%d").date()

                    # Fecha inferior: 4 días atrás
                    date_bottom = date_top - timedelta(days=4) # intervalo permitido para que los que no tienen permiso

                    # Convertimos input a fecha
                    try:
                        input_date = dt.strptime(input_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        # Si el input no tiene formato correcto, forzamos fecha superior
                        input_date = date_top

                    # Evaluación del rango
                    if input_date < date_bottom or input_date > date_top:
                        current_date = date_top
                    else:
                        current_date = input_date

                    # Construir respuesta en formato string
                    return date_top.strftime("%Y-%m-%d"), date_bottom.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")
                
                date_top, date_bottom, date_current  = await validate_date_range(input_date_str = cash_register_body.Date)
                
                # date_current = date_bottom
                start_date = dt.strptime(date_current, "%Y-%m-%d")
                end_date = start_date + timedelta(days=1)

    
            #FUNCIONA PARA CAMBIAR A BASE36
            def to_base36(num_str):
                num = int(num_str)
                chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                base36 = ""
                while num > 0:
                    num, i = divmod(num, 36)
                    base36 = chars[i] + base36
                return base36

            #FUNCIONA PARA DAR FORMATO CABECERA / DETALLE
            def build_sales_response(ventas):
                # --- 1) Calcular totales por tipo de pago ---
                totales = defaultdict(Decimal)

                for v in ventas:
                    totales[v["TipoPago"]] += v["DocTotal"]

                # Convertir Decimal → string para JSON seguro
                cabecera = {tipo: format(total, "f") for tipo, total in totales.items()}

                # --- 2) Preparar detalle con conversiones seguras ---
                detalle = []
                for v in ventas:
                    item = v.copy()
                    item["DocTotal"] = format(item["DocTotal"], "f")  # Decimal → string

                    # convertir fecha a un formato estándar
                    item["DocDate"] = item["DocDate"].strftime("%H:%M")

                    # convertir CODETS a hex36
                    item["CodeTS"] = "" if item["CodeTS"] is None else to_base36(item["CodeTS"])

                    detalle.append(item)

                # --- 3) Armar diccionario final ---
                return {
                    "cabecera": cabecera,
                    "detalle": detalle
                }

            stmt = (select( 
                            SalesOrder.c.DocEntry,
                            SalesOrder.c.CashBoxTS.label("CodeTS"),
                            SalesOrder.c.DocNum,
                            SalesOrder.c.SlpCode,
                            SalesOrder.c.DocDate,
                            Product.c.id,
                            Product.c.isbn.label("ISBN"),
                            Product.c.title.label("Title"),
                            SalesOrder.c.DocCur.label("Moneda"),
                            SalesOrderDetail.c.Total.label("DocTotal"),
                            PymntGroup.c.PymntGroupName.label("TipoPago")
                        )
                    .join(SalesOrderDetail, SalesOrder.c.DocEntry == SalesOrderDetail.c.DocEntry)
                    .join(Product, SalesOrderDetail.c.idProduct == Product.c.id)
                    .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
                    .join(CashRegister, SalesOrder.c.CashBoxTS == CashRegister.c.CodeTS)
                    .filter(
                        SalesOrder.c.DocDate >= start_date,
                        SalesOrder.c.DocDate < end_date,
                        CashRegister.c.WareID == cash_register_body.WareID,
                        Product.c.idItem == cash_register_body.IdItem
                    )
                    .order_by(desc(SalesOrder.c.DocDate))
                    )

            returned_value = [dict(r) for r in session.execute(stmt).mappings().all()]

            returned_value = build_sales_response(returned_value)
            returned_value.update({"status": True, 
                                   "message": "ok",
                                    "dates": {
                                        "date_current": date_current,
                                        "date_bottom": date_bottom,
                                        "date_top": date_top
                                    }})

        else:
            returned_value.update({
                                    "status": False, 
                                    "message": "No cuenta con permisos revisar los reportes", 
                                    "cabecera": {}, 
                                    "detalle": [],
                                    "dates": {
                                        "date_current": date_current,
                                        "date_bottom": None,
                                        "date_top": None
                                        }
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
    
@sales_route.get("/get_cash_register/", status_code=200)
async def Get_Cash_Register_By_Param(cash_register_body: cash_register = Depends(), payload: jwt_dependecy = None):
    returned_value = []
    try:
        #Validacion si tiene permisos para caja aperturada
        stmt = (select(CashRegister).
                order_by(desc(CashRegister.c.OpenDate)))
        
        if cash_register_body.CodeTS is not None:
            stmt = stmt.filter(CashRegister.c.CodeTS == cash_register_body.CodeTS)
        
        if cash_register_body.WareID is not None:
            stmt = stmt.filter(CashRegister.c.WareID == cash_register_body.WareID)
        
        if cash_register_body.User is not None:
            stmt = stmt.filter(CashRegister.c.User == cash_register_body.User)
        
        if cash_register_body.Status is not None:
            stmt = stmt.filter(CashRegister.c.Status == cash_register_body.Status)

        rows = session.execute(stmt).mappings().all()

        returned_value = rows if (isinstance(rows, list) and len(rows) > 0) else []
        
    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
    finally:
        session.close()
        return returned_value
    

@sales_route.get("/get_sale_order_detail/", status_code=200)
async def Obtiene_Detalle_Orden_Venta(DocEntry:int=None, payload: jwt_dependecy=None):
    returnedVal = {
                    "message": "Something wrong happen",
                    "status": False, 
                    "data": []
                   }
    try:
        if DocEntry is not None:

            stmt = (
                select(SalesOrder.c.DocNum.label("doc_num"), 
                        SalesOrder.c.DocDate.label("doc_date"), 
                        Company.c.docName.label("card_name"), 
                        Company.c.LicTradNum.label("card_num"), 
                        SalesOrder.c.SubTotal.label("sub_total"),
                        SalesOrder.c.DiscSum.label("dscto_total"),
                        SalesOrder.c.VatSum.label("tax_total"),
                        SalesOrder.c.DocTotal.label("total"),
                        PymntGroup.c.PymntGroupName.label("pay_method"),
                        Product.c.id.label("Id"),
                        Product.c.title.label("dscp"),
                        Product.c.isbn.label("cod"),
                        SalesOrderDetail.c.Quantity.label("qty"),
                        SalesOrderDetail.c.UnitPrice.label("pvp"),
                        SalesOrderDetail.c.DiscSum.label("dsct"),
                        SalesOrderDetail.c.Total.label("total_linea"))
                .join(SalesOrderDetail, SalesOrder.c.DocEntry == SalesOrderDetail.c.DocEntry)
                .join(Company, SalesOrder.c.CardCode == Company.c.cardCode)
                .join(Product, SalesOrderDetail.c.idProduct == Product.c.id)
                .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
                .order_by(asc(SalesOrderDetail.c.LineNum))
                .filter(SalesOrder.c.DocEntry == DocEntry)
            )

            result = session.execute(stmt).mappings().all()

            if isinstance(result, list) and len(result) > 0:
                body=build_body_ticket(result)

                doc = {
                    "doc_num": body.doc_num,
                    "doc_date": body.doc_date,
                    "card_name": body.card_name,
                    "card_num": body.card_num,
                    "sub_total": body.sub_total,
                    "dscto_total": body.dscto_total,
                    "tax_total": body.tax_total,
                    "total": body.total,
                    "pay_method": body.pay_method,
                    "doc_time": body.doc_time,
                    "items": [{"id": idx.id, "dscp": idx.dscp, "cod": idx.cod , "qty": idx.qty, "pvp": idx.pvp, "dsct": idx.dsct,"total_linea": idx.total_linea} 
                            for idx in body.items]
                }

                returnedVal.update({"message": "ok", "status": True, "data": doc})

            else:
                returnedVal.update({"message": "Something wrong happen", "status": False, "data": []})

        else:
            returnedVal.update({"message": "Debe ingresar un DocEntry Valido", "status": False, "data": []})
        
        
        return returnedVal
        
    except Exception as e:
        print(f"An error occurred: {e}")
        returnedVal.update({"message": f"An error occurred: {e}", "status": False})
        return returnedVal

@sales_route.get("/get_all_sales_order_of_cashregister/", status_code=200)
async def Get_All_Sales_Order_Of_CashRegister(cash_register_body: cash_register = Depends(), payload: jwt_dependecy = None):
    returned_value = []
    try:
        if cash_register_body.CodeTS is not None:
            stmt = (
                select(
                    func.dense_rank().over(order_by=asc(SalesOrder.c.DocEntry)).label("enum"),
                    PymntGroup.c.PymntGroup.label("pay_method"),
                    Product.c.title.label("dscp"),
                    SalesOrderDetail.c.Quantity.label("qty"),
                    SalesOrderDetail.c.Total.label("total_linea")
                )
                .join(SalesOrderDetail, SalesOrder.c.DocEntry == SalesOrderDetail.c.DocEntry)
                .join(Product, SalesOrderDetail.c.idProduct == Product.c.id)
                .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
                .where(SalesOrder.c.CashBoxTS == cash_register_body.CodeTS)
                .order_by(asc(SalesOrder.c.DocEntry))
                )

            rows = session.execute(stmt).mappings().all()

            returned_value = rows if (isinstance(rows, list) and len(rows) > 0) else []
        
        else:
            returned_value = []
        
    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback()
        session.close()

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback()
        session.close()

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback()
        session.close()
    finally:
        session.close()
        return returned_value

@sales_route.get("/get_header_data_cash_register/", status_code=200)
async def Get_Header_Data_Cash_Register_By_Param(cash_register_body: cash_register = Depends(), flag=True, payload: jwt_dependecy = None):
    returned_value = {
        "user": None,
        "OpenDate": None,
        "CashOpen": None,
        "message": "ok",
        "status_code": 200
    }
    try:
        caja_abierta = session.execute(
                select(CashRegister.c.Status, CashRegister.c.WareID, CashRegister.c.User)
                .filter(CashRegister.c.CodeTS == cash_register_body.CodeTS)
                )
        
        rows = caja_abierta.mappings().all()

        if(isinstance(rows, list) and len(rows) > 0 and rows[0]["Status"] == 'O'):
            
            #SUBCONSULTA PARA CALCULAR EL TOTAL DE ITEM SELECCIONADO VENDIDOS
            subq_units = (
                select(func.coalesce(func.sum(SalesOrderDetail.c.Quantity), 0))
                .select_from(
                    SalesOrderDetail.join(
                        SalesOrder, 
                        SalesOrderDetail.c.DocEntry == SalesOrder.c.DocEntry
                    )
                )
                .where(
                    SalesOrderDetail.c.idProduct == CashRegister.c.Item2Code,
                    SalesOrder.c.CashBoxTS == CashRegister.c.CodeTS
                )
                .correlate(CashRegister)
                .scalar_subquery()
            )

            #Validacion si tiene permisos para caja aperturada
            stmt = (
                    select(
                        CashRegister.c.User,
                        CashRegister.c.OpenDate,
                        CashRegister.c.CashOpen,
                        CashRegister.c.Item2Total,
                        CashRegister.c.Item2Code,
                        subq_units.label("Item2Sold"),
                        (
                            func.coalesce(func.sum(
                                    case(
                                        (SalesOrder.c.PymntGroup == 'CASH', SalesOrder.c.DocTotal), #solo efectivo
                                        else_=0
                                        )
                                ),
                                0
                            )
                        ).label("CASH"),
                        (
                            func.coalesce(func.sum(
                                    case(
                                        (SalesOrder.c.PymntGroup == 'CRDN', SalesOrder.c.DocTotal), #solo tarjeta
                                        else_=0
                                        )
                                ),
                                0
                            )
                        ).label("CRDN"),
                        (
                            func.coalesce(func.sum(
                                    case(
                                        (SalesOrder.c.PymntGroup == 'TRAN', SalesOrder.c.DocTotal), #solo transferencia
                                        else_=0
                                        )
                                ),
                                0
                            )
                        ).label("TRAN"),
                        (
                            func.coalesce(func.sum(
                                    case(
                                        (SalesOrder.c.PymntGroup == 'WMCH', SalesOrder.c.DocTotal), #solo billera maquina
                                        else_=0
                                        )
                                ),
                                0
                            )
                        ).label("WMCH"),
                        (
                            func.coalesce(func.sum(
                                    case(
                                        (SalesOrder.c.PymntGroup == 'WPHN', SalesOrder.c.DocTotal), #solo billera celular
                                        else_=0
                                        )
                                ),
                                0
                            )
                        ).label("WPHN"),
                        )
                    .outerjoin(SalesOrder, CashRegister.c.CodeTS == SalesOrder.c.CashBoxTS)
                    .filter(CashRegister.c.CodeTS == cash_register_body.CodeTS)
                    .group_by(
                        CashRegister.c.User,
                        CashRegister.c.OpenDate,
                        CashRegister.c.CashOpen
                        )
                    )

            row = session.execute(stmt).mappings().one()
            row_dict= dict(row)

            row_dict["OpenDate"] = row_dict["OpenDate"].strftime("%d/%m")

            row_dict.update({
                "status_code": 200,
                "message": "ok"
            })

            returned_value = row_dict
        else:
            returned_value.update({
                "message": "La caja se encuentra cerrada",
                "status_code": 422
            })
        
    except Exception as e:
        print(f"An error ocurred: {e}")
        session.rollback() #no hace efecto por que es consulta
        session.close()

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback() #no hace efecto por que es consulta
        session.close()

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback() #no hace efecto por que es consulta
        session.close()
    finally:
        session.close()

        if flag:
            return JSONResponse(
                status_code= returned_value["status_code"],
                content= jsonable_encoder({
                        "data": returned_value,
                    })
            )
        else:
            return returned_value


@sales_route.post("/close_cash_register/", status_code=201)
async def Close_Cash_Register(cash_register_body: cash_register, payload: jwt_dependecy = None):
    returned_value = {
        "message": "ok",
        "status_code": 201,
        "file": None
    }
    try:

        caja_abierta = session.execute(
                select(CashRegister.c.Status, CashRegister.c.WareID, CashRegister.c.User)
                .filter(CashRegister.c.CodeTS == cash_register_body.CodeTS)
                )
        
        rows = caja_abierta.mappings().all()


        if(isinstance(rows, list) and len(rows) > 0 and rows[0]["Status"] == 'O'):
            #Validacion si tiene permisos para caja aperturada
            create_date = await Get_Time() #<-- obtiene hora

            Montos_totales = await Get_Header_Data_Cash_Register_By_Param(cash_register_body=cash_register_body, flag=False)

            stmt = (update(CashRegister)
                    .where(CashRegister.c.CodeTS == cash_register_body.CodeTS)
                    .values(
                        CloseDate=create_date["lima_bd_format"] or None, #hora cierre de caja
                        CashTotalClose=Decimal(cash_register_body.CashClose),
                        Obs=cash_register_body.Obs,
                        CashDiff=Decimal(cash_register_body.CashDiff),
                        Status = 'C', #cambiar a C
                        CashSystem=Montos_totales["CASH"] or None,
                        CardTotal=Montos_totales["CRDN"] or None,
                        TransferTotal=Montos_totales["TRAN"] or None,
                        WalletTotalM=Montos_totales["WMCH"] or None,
                        WalletTotalC=Montos_totales["WPHN"] or None
                    )
                )
            
            # Ejecutar la instrucción de actualización
            result = session.execute(stmt)

            if result.rowcount > 0:

                session.commit()

                ##################### GRABA CIERRE DE CAJA
                ##################### INICIA GENERACIONDE TICKET PDF
                                #    CashRegister.c.CashOpen + CashRegister.c.CashSystem + CashRegister.c.CashDiff
                                #    CashRegister.c.CardTotal + CashRegister.c.WalletTotalM

                stmt = (select(CashRegister.c.CashOpen.label("caja"),
                               CashRegister.c.CashSystem.label("cash_teory"),
                               CashRegister.c.CashDiff.label("diff"),
                               (
                                   func.coalesce(CashRegister.c.CashOpen, 0)
                                    + func.coalesce(CashRegister.c.CashSystem, 0)
                                    + func.coalesce(CashRegister.c.CashDiff, 0)
                                ).label("total"),
                               (
                                   func.coalesce(CashRegister.c.CardTotal, 0)
                                    + func.coalesce(CashRegister.c.WalletTotalM, 0)
                                ).label("card_total_walletmch"),
                                func.coalesce(CashRegister.c.WalletTotalC, 0).label("wallet_total_phone"),
                               CashRegister.c.CloseDate.label("date"),
                               CashRegister.c.User.label("vendedor")
                               )
                        .filter(CashRegister.c.CodeTS == cash_register_body.CodeTS))
                
                response = session.execute(stmt).mappings().all()
            
                # results = await Get_All_Sales_Order_Of_CashRegister(cash_register_body=cash_register(CodeTS = cash_register_body.CodeTS))
                items = await Get_All_Sales_Order_Of_CashRegister(cash_register_body=cash_register(CodeTS = cash_register_body.CodeTS))
                header = [
                            {
                            "caja": idx["caja"].to_eng_string(),
                            "cash_teory": "0.00" if idx["cash_teory"] is None else idx["cash_teory"].to_eng_string(),
                            "diff": "0.00" if idx["diff"] is None else idx["diff"].to_eng_string(),
                            "total": "0.00" if idx["total"] is None else idx["total"].to_eng_string(),
                            "card_total_walletmch": "0.00" if idx["card_total_walletmch"] is None else idx["card_total_walletmch"].to_eng_string(),
                            "wallet_total_phone": "0.00" if idx["wallet_total_phone"] is None else idx["wallet_total_phone"].to_eng_string(),
                            "date": "no-date" if idx["date"] is None else idx["date"].strftime("%d/%m/%Y"),
                            "vendedor": "no-vendedor" if idx["vendedor"] is None else idx["vendedor"],
                            "item2Sold": 0 if Montos_totales["Item2Sold"] is None else int(Montos_totales["Item2Sold"]),
                            "item2Total": 0 if Montos_totales["Item2Total"] is None else Montos_totales["Item2Total"]
                            } 
                           for idx in response]
                
                header = header[0]
                header.update({"items": [
                    Item_Ticket_Close(**{
                        "enum": str(idx["enum"]),
                        "pay_method": idx["pay_method"],
                        "dscp": idx["dscp"],
                        "qty": str(idx["qty"]),
                        "total_linea": idx["total_linea"].to_eng_string()
                    }) for idx in items
                ]})
                
                respuesta = await Crear_Cierre_Ticket_PDF(body=Body_Ticket_Close(**header), payload=payload)

                # returnedVal.update({"message": message, "status": status, "file": file})

                returned_value.update({
                    "status_code": 201,
                    "message": f""""Solo afecto datos de caja y {respuesta["message"]}""" if not(respuesta["status"]) else "Datos de caja y ticket generado " ,
                    "file":  None if respuesta["file"] is None else respuesta["file"]
                })

            else:
                returned_value.update({
                    "status_code": 201,
                    "message": "No se hizo ningun cambio"
                })
                session.rollback()


        elif (isinstance(rows, list) and len(rows) > 0 and rows[0]["Status"] == 'C'):
            returned_value.update({
                "message": "La caja ya se encuentra cerrada",
                "status_code": 422
            })
        
        else:
            returned_value.update({
                "message": "No se encontro caja",
                "status_code": 422
            })
        
    except Exception as e:
        print(f"An error ocurred: {e}")
        returned_value.update({
                                "message": f"An error ocurred: {e}",
                                "status_code": 422
                                })
        session.rollback() #no hace efecto por que es consulta
        session.close()

    except IntegrityError as e:  # errores típicos de FK, UNIQUE, NOT NULL
        print(f"""Detalle SQLAlchemy: {e.orig}""")
        session.rollback() #no hace efecto por que es consulta
        session.close()

    except SQLAlchemyError as e:  # captura cualquier otro error de SQLAlchemy
        print("Error SQLAlchemy:", str(e.__dict__["orig"]))  # error original
        session.rollback() #no hace efecto por que es consulta
        session.close()
    finally:
        session.close()
        return JSONResponse(
            status_code= returned_value["status_code"],
            content= {
                    "data": returned_value,
                }
        )
      
@sales_route.post("/create_external_sales_document/", status_code=201)
async def Crear_Documento_Externo_De_Venta(body=sales_order, series=series_internal, payload: jwt_dependecy = None):

    returnedValue={"message": "Error indeterminado",
                   "status_code": 422,
                   "data": {}}

    try:

        #OBTENEMOS DATOS DEL CLIENTE
        stmt = (
                select(
                    CompanyContacts.c.Email.label("TXT_CORREO_ENVIO"),
                    ODTC.c.SunatCode.label("COD_TIP_NIF_RECP"),
                    Company.c.LicTradNum.label("NUM_NIF_RECP"),
                    Company.c.docName.label("NOM_RZN_SOC_RECP"),
                    Company.c.address.label("TXT_DMCL_FISC_RECEP")
                )
                .join(ODTC, Company.c.DocType == ODTC.c.DocType)
                .outerjoin(CompanyContacts, and_(   Company.c.cardCode == CompanyContacts.c.cardCode,
                                                    CompanyContacts.c.DefaultContact == 1
                                                ))
                .filter(and_(
                            Company.c.cardCode == body.receptor_cod,
                            Company.c.type == 'C',
                             )
                    )
                )

        customer = session.execute(stmt).mappings().first()
        
        #OBTIENE DATOS DEL DOCUMENTO (FACTURA, BOLETA, NOTA D CREDITO)
        stmt = (
                select(
                    DocType.c.SunatCode.label("COD_TIP_CPE"),
                )
                .filter(DocType.c.DocTypeCode == body.doc_tipo)
                )


        doctype_code = session.execute(stmt).mappings().first()
        
        #OBTIENE CODIGOS DE AFECTACION Y TRIBUTOS
        stmt = (select(OAFV))
        oafv_list = session.execute(stmt).mappings().all()
        
        #OBTIENE NOMBRE FORMA DE PAGO
        stmt = (select(PymntGroup.c.PymntGroupName.label("forma_pago_nombre")).filter(PymntGroup.c.PymntGroup == body.forma_pago))

        pymntgroup_name = session.execute(stmt).mappings().first()

        if customer and doctype_code and len(oafv_list) and pymntgroup_name: #verifica si cliente existe y si existe codigo de documento y si existe codigos tributarios
            
            #FORMATEA CLIENTE
            customer_f = {key: ("" if value is None else value) for key, value in customer.items()} #clientes a diccionario

            #OBTIENE HORA
            create_date = await Get_Time()
            time_f = {
                "FEC_EMIS": create_date["lima_transfer_format"],
                "FEC_VENCIMIENTO": create_date["lima_transfer_format"]
            }
            
            #OBTIENE TIPO DOCUMENTO
            doctype_f = dict(doctype_code)

            #OBTIENE SERIE
            serie_f = {
                "NUM_SERIE_CPE": series.Prefix,
                "NUM_CORRE_CPE": series.NextNumber
            }

            # OBTIENE DOMICILIO FISCAL
            customer_f["TXT_DMCL_FISC_RECEP"] = customer_f["TXT_DMCL_FISC_RECEP"] or ""

            # FILTRA CORREO DE CLIENTE PARA ENVIO SI EXISTE INFORMACION
            if (customer_f["TXT_CORREO_ENVIO"] is None) or (customer_f["TXT_CORREO_ENVIO"] == ""): customer_f.pop("TXT_CORREO_ENVIO")

            total_gravado_inner = str(Decimal(body.total_gravado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            total_exonerado_inner = str(Decimal(body.total_exonerado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            total_igv_inner = str(Decimal(body.total_igv).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            total_inner = str(Decimal(body.total_monto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

            
            # "TOKEN":"gN8zNRBV+/FVxTLwdaZx0w==", # token del emisor, este token gN8zNRBV+/FVxTLwdaZx0w== es de pruebas
            boleta_json =  {
                "COD_TIP_NIF_EMIS": "6", # "6": RUC PARA EMISOR
                "NUM_NIF_EMIS": MIFACT_MIRUC, # RUC DE PRODUCCION
                "NOM_RZN_SOC_EMIS": "ROJAS CARRASCO IVAN ALEXIS", # RAZON SOCIAL EMISOR PRUEBA
                "NOM_COMER_EMIS": "MUSEO LIBRERIA GENESIS", # NOMBRE COMERCIAL EMISOR | ESTE DATO PUEDE IR EN EL DOCUMENTO ?
                "COD_UBI_EMIS": "080101", # DATO REAL UBIGEO 🎃
                "TXT_DMCL_FISC_EMIS": "CAL. SANTA CATALINA ANCHA 307", # DATO REAL 🎃
                "COD_MND": "PEN", #DATO REAL FIJO 🎃
                "COD_PRCD_CARGA": "001", #DATO REAL FIJO PARA PROCEDENCIA WEB SERVICE 🎃
                # "TIP_CAMBIO":"1.000", # NO VA POR QUE TODO SERA (PEN)
                "COD_PTO_VENTA": payload.get("username") or "", #codigo vendedor
                "ENVIAR_A_SUNAT": "true",
                "RETORNA_XML_ENVIO": "true",
                "RETORNA_XML_CDR": "false",
                "RETORNA_PDF": "true",
                "COD_FORM_IMPR":"004", #FORMATO TICKET TERMICO 80 mm
                "TXT_VERS_UBL":"2.1", #DEJAMOS ASI | DESDE OCTUBRE DEL 2018
                "TXT_VERS_ESTRUCT_UBL":"2.0", #DEJAMOS ASI | DESDE OCTUBRE DEL 2018
                "COD_ANEXO_EMIS":"0000", #DEJAMOS ASI  | "0000" CODIGO PARA DOMICILIO FISCAL | "0001" CODIGO PARA DIRECCION ALAYZA
                "COD_TIP_OPE_SUNAT": "0101", #Tipo de operacion: "0101" (Venta Interna) (OJO): "0112" (SOLO FACTURA) PARA PERSONA NATURAL SIN NEGOCIO (MEDICOS, PINTORES ETC) QUE QUIERE JUSTIFICAR GASTOS
                "MNT_TOT_GRAVADO" : total_gravado_inner,
                "MNT_TOT_EXONERADO" : total_exonerado_inner,
                "MNT_TOT_TRIB_IGV" : total_igv_inner,
                "MNT_TOT" : total_inner
            }


            #SE CONVIERTE EN EN DICCIONARIO INDEXADO LAS AFECTACIONES Y TRIBUTOS
            oafv_map = {
                oafv_item["Code"]: (oafv_item["SunatAfectacion"], oafv_item["SunatTributo"])
                for oafv_item in oafv_list
            }
            
            # #ITEMS
            items = []
            for index, item in enumerate(body.items):
                VAL_UNIT_ITEM_SIN_FORMATO = (Decimal(item.pv_no_igv) - Decimal(item.dsct_user_unit_no_igv))
                VAL_UNIT_ITEM = VAL_UNIT_ITEM_SIN_FORMATO.quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP) #<- 6 deciamles para evitar problema de redondeo

                VAL_VTA_ITEM_SIN_FORMATO = VAL_UNIT_ITEM_SIN_FORMATO * Decimal(item.qty)
                VAL_VTA_ITEM = VAL_VTA_ITEM_SIN_FORMATO.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                items.append({
                "COD_ITEM": str(item.id),
                "COD_UNID_ITEM": item.uom,
                "CANT_UNID_ITEM": str(item.qty),
                "COD_TIP_PRC_VTA": "01",
                "TXT_DESC_ITEM": str(item.dscp)[:30], #30 CARACTERES
                "COD_TIP_AFECT_IGV_ITEM": oafv_map.get(item.oafv, (None, None))[0],
                "COD_TRIB_IGV_ITEM": oafv_map.get(item.oafv, (None, None))[1],
                "POR_IGV_ITEM": str(int(float(item.ovtg_rate))),
                "MNT_PV_ITEM": item.total_si_igv, #SUBTOTAL MONTO TOTAL CON IGV CON TODO, DESCUENTOS, CARGOS ADICIONALES
                "VAL_UNIT_ITEM": str(VAL_UNIT_ITEM),      #VALOR UNITARIO SIN IGV
                "PRC_VTA_UNIT_ITEM": str((Decimal(item.total_si_igv) / (Decimal(item.qty))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), # PRC_VTA_UNIT_ITEM CON IGV
                "VAL_VTA_ITEM": str(VAL_VTA_ITEM), # VAL_UNIT_ITEM * CANTIDAD
                "MNT_BRUTO": str(VAL_VTA_ITEM), # PUEDE SER IGUAL A VAL_VTA_ITEM (PROBAR SIN ENVIAR ESTO)
                "MNT_IGV_ITEM": str(item.VatSum),  
                })

            
            boleta_json.update(customer_f) # <- AGREGA CLIENTE
            boleta_json.update(time_f) # <- AGREGA TIEMPO
            boleta_json.update(doctype_f) # <- AGREGA TIPO DOCUMENTO
            boleta_json.update(serie_f) # <- AGREGA SERIE
            boleta_json.update({"items": items}) # <- AGREGA ITEMS
            boleta_json.update({"datos_adicionales": [ # <- ESTO SE TIENE QUE ARREGLAR PARA FORMA DE PAGO
                {
                    "COD_TIP_ADIC_SUNAT": "01",
                    "TXT_DESC_ADIC_SUNAT": str(pymntgroup_name["forma_pago_nombre"]).upper()
                }
            ]})

            # print(boleta_json)

            #SE PROCEDE A GRABAR EL CUERPO EN MI FACT
            json_data, status_code = await post_sales_document(params=boleta_json)

            print(json_data)

            #RECHAZADO POR EL PROVEEDOR 👻
            if "estado_documento" in json_data and json_data["estado_documento"] == '' and status_code == 200:
                
                returnedValue.update({"message": json_data["errors"],
                        "status_code": 422,
                        "data": {}
                        })
            
            elif "estado_documento" in json_data and json_data["estado_documento"] != '104' and status_code == 200:
                create_date = await Get_Time()
                returnedValue.update({"message": json_data["sunat_description"],
                                      "status_code": 201,
                                      "data": {
                                          "QR": json_data["cadena_para_codigo_qr"],
                                          "Hash": json_data["codigo_hash"],
                                          "Status": int(json_data["estado_documento"]),
                                          "SendDate": create_date["lima_bd_format"],
                                          "pdf_bytes": json_data["pdf_bytes"],
                                          "pdf_url": json_data["url"],
                                          "Ticket": json_data["ticket_sunat"] if json_data["ticket_sunat"] else None
                                        }
                                      })
            
            #RECHAZADO POR EL PROVEEDOR 👻
            elif "estado_documento" in json_data and json_data["estado_documento"] == '104' \
            and "cdr_sunat" in json_data and not(bool(json_data["cdr_sunat"])) \
            and "xml_enviado" in json_data and not(bool(json_data["xml_enviado"])) \
            and status_code == 200:
                returnedValue.update({"message": json_data["errors"],
                                      "status_code": 422,
                                      "data": {}
                                      })
            #RECHAZADO POR SUNAT 👻
            elif "estado_documento" in json_data and json_data["estado_documento"] == '104' \
            and "cdr_sunat" in json_data and bool(json_data["cdr_sunat"]) \
            and status_code == 200:
                returnedValue.update({"message": json_data["sunat_description"],
                                        "status_code": 201,
                                        "data": {
                                          "QR": json_data["cadena_para_codigo_qr"],
                                          "Hash": json_data["codigo_hash"],
                                          "Status": int(json_data["estado_documento"]),
                                          "SendDate": create_date["lima_bd_format"],
                                          "pdf_bytes": json_data["pdf_bytes"],
                                          "pdf_url": json_data["url"],
                                          "Ticket": json_data["ticket_sunat"] if json_data["ticket_sunat"] else None
                                        }
                                      })
                
            else:
                if "errors" in json_data and json_data["errors"]:
                    returnedValue.update({"message": json_data["errors"]})
                    returnedValue.update({"status_code": 422})
                else:
                    returnedValue.update({"message": "Error indeterminado in sales routes line 1121"})
                    returnedValue.update({"status_code": 422})

        return returnedValue

    except Exception as e:
        session.rollback()
        session.close()
        returnedValue.update({"message": f"An error ocurred: {e}"})
        returnedValue.update({"status_code": 422})
        return returnedValue
    finally:

        session.close()



@sales_route.post("/register_external_document_state/", status_code=201)
async def Registrar_Estado_Documento_Externo(body=external_document, payload: jwt_dependecy = None):

    returnedValue={"message": "Error indeterminado",
                   "status_code": 422,
                   "data": {}}

    try:
      
        if body.DocEntry and body.Status:
            create_date = await Get_Time()
            stmt = (insert(SalesOrderSunat).
                    values(
                        DocEntry= body.DocEntry,
                        Status= body.Status,
                        Hash= body.Hash or None,
                        QR= body.QR or None,
                        SendDate= body.SendDate,
                        CreateDate=create_date["lima_bd_format"],
                        Ticket= body.Ticket or None
                    )
            )

            affected = session.execute(stmt)

            if affected.rowcount > 0:  #filas afectadas mayor a 0 ✅, EMPIEZA CON REGISTRO DE LINEAS HIJAS
                returnedValue.update({"message": f"Registro Sunat creado, Estado: {str(body.Status)}"})
                returnedValue.update({"status_code": 201})
                session.commit()
            else:
                session.rollback()
                session.close()
                returnedValue.update({"message": "Error durante registro de documento externo en sistema"})
                returnedValue.update({"status_code": 422})

        else:
            session.rollback()
            session.close()
            returnedValue.update({"message": "DocEntry o Status Sunat incorrecto"})
            returnedValue.update({"status_code": 422})

        return returnedValue

    except Exception as e:
        session.rollback()
        session.close()
        returnedValue.update({"message": f"An error ocurred: {e}"})
        returnedValue.update({"status_code": 422})
        return returnedValue
    finally:

        session.close()


@sales_route.post("/create_internal_sales_document/", status_code=201)
async def Crear_Documento_Interno_De_Venta(body=sales_order, series=series_internal, payload: jwt_dependecy = None):

    returnedValue={"message": "Error indeterminado",
                   "status_code": 422,
                   "data": {}}
    grabo_fila = 0

    try:
        serie = series.Prefix
        correlativo = series.NextNumber

        #NUEVO SERIE-CORRELATIVO EN DOCUMENTO
        numero_documento = f"""{serie}-{correlativo}""" 

        ##HORA DE REGISTRO
        create_date = await Get_Time()
        subtotal_sinredo_subtotal = Decimal(body.SubTotal)
        subtotal = subtotal_sinredo_subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        igv = Decimal(body.VatSum).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        descuento_sinredo = Decimal(body.total_descuentos)
        descuento = descuento_sinredo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = Decimal(body.total_monto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        subtotal_con_dscto = (subtotal_sinredo_subtotal - descuento_sinredo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) #calculo en backend
        
        #GRABA CABECERA
        cant_productos = len(body.items)
        if cant_productos > 0:
            stmt = (insert(SalesOrder).
                    values(
                        DocNum=numero_documento,
                        DocType=body.doc_tipo,
                        DocDate= create_date["lima_bd_format"] or None, 
                        DocDueDate= create_date["lima_bd_format"] or None, #esto tiene que venir del frond, por el momento sera la misma fecha que la creacion
                        CardCode=body.receptor_cod,
                        SubTotal=subtotal or None, #<- esta en formato decimal, calculo sin descuentos
                        DiscSum=descuento or None, #contiene todo el descuento por linea y por documento
                        VatSum=igv or None,
                        DocTotal=total or None,
                        DocStatus='C', #<-cerrado por que ya esta facturado / si es para canjear en el frond debe existir esa opcion y quedan en open
                        DocCur="PEN",
                        CashBoxTS=body.codigo_caja,
                        RefDocEntry=None,
                        PymntGroup=body.forma_pago,
                        SlpCode=payload.get("username"),
                        CreateDate=create_date["lima_bd_format"] or None,
                        UpdateDate=None
                    )
            )
            affected = session.execute(stmt)

            if affected.rowcount > 0:  #filas afectadas mayor a 0 ✅, EMPIEZA CON REGISTRO DE LINEAS HIJAS
                docentry = affected.inserted_primary_key[0] #DocEntry del padre

                #AQUI GRABA DETALLE
                for lineNum, item in enumerate(body.items):
                    stmt1 = (insert(SalesOrderDetail)
                            .values(
                                LineNum=lineNum,
                                DocEntry=docentry,
                                idProduct=item.id,
                                Quantity=int(item.qty),
                                UnitPrice=Decimal(item.pv_si_igv), #este es el precio con igv
                                DiscSum= Decimal(item.dsct_user_total_no_igv), #dsct total x todas las cantidades
                                LineTotal=Decimal(item.total_no_igv), #subtotal sin igv sin descuentos
                                VatSum=Decimal(item.VatSum), #igv (subtotal - dscto) * 0.18
                                Total=Decimal(item.total_si_igv), #total con igv (subtotal - dscto) * 0.18 * cantidad
                                idWare=body.id_ware,
                                Uom=item.uom,
                                VatPrcnt=item.ovtg_rate,
                                Oafv=item.oafv,
                                Ovtg=item.ovtg,
                                CreateDate=create_date["lima_bd_format"] or None,
                                UpdateDate=None
                            )
                    )
                    res_contact = session.execute(stmt1)
                    if (res_contact.rowcount > 0):
                        grabo_fila += 1
                        # print(f"Grabo salesorder linea: {lineNum}") 
                    else:
                        returnedValue.update({"message": "Error al intetar grabar fila de documentos"})
                        break
                
                if grabo_fila == len(body.items):
                    #DESCONTAR CANTIDAD DE ALMACEN
                    params = list(map(lambda x: {
                                'qtyN': int(x.qty),
                                'editDa': create_date["lima_bd_format"] or None,
                                'idPro' : x.id,
                                'idWa' : body.id_ware
                                }, 
                            body.items)
                            )

                    stmt = text(f"UPDATE ware_product set qtyNew = qtyNew - :qtyN, editDate = :editDa where idProduct = :idPro and idWare = :idWa")
                    response = session.execute(stmt, params)
                    if (response.rowcount > 0):
                        # print(f"Actualizo filas en warehouse_product: {response.rowcount}") 
                        #ACTUALIZAR ULTIMO CORRELATIVO 
                        stmt = (update(DocSeries)
                                .filter(DocSeries.c.DocTypeCode == body.doc_tipo,
                                        DocSeries.c.WareCode == body.id_ware)
                                .values(
                                LastNumber=correlativo,
                                UpdateDate=create_date["lima_bd_format"] or None
                            )
                        )

                        res_docseries = session.execute(stmt)

                        if (res_docseries.rowcount > 0):
                            cant_items = 0
                            for item in body.items:
                                cant_items += int(item.qty)
                            
                            stmt = (select(Company.c.docName).filter(Company.c.cardCode == body.receptor_cod))
                            response = session.execute(stmt).mappings().one()
                            #response: {'docName': 'VARIOS'}

                            returnedValue.update({"message": f"Orden de venta aceptada DocEntry: {numero_documento}"})
                            returnedValue.update({"data": {
                                "docentry": docentry or None,
                                "doc_num": numero_documento or None,
                                "subtotal": subtotal_con_dscto.to_eng_string() or None,
                                "igv": igv.to_eng_string(),
                                "total": total.to_eng_string(),
                                "cant_titulos": cant_productos or 0,
                                "cant_items": cant_items or 0,
                                "cliente": response["docName"] or ""
                            }})
                            returnedValue.update({"status_code": 201})
                            session.commit() #AQUI TERMINA TODO CON UN COMMIT 🎭🎭🎭
                            session.close()
                        else:
                            session.rollback()
                            session.close()
                            returnedValue.update({"message": "Error: No actualizo correlativo, fase ultima de commit"})
                            returnedValue.update({"status_code": 422})
                    else:
                        session.rollback()
                        session.close()
                        returnedValue.update({"message": "Error: No desconto cantidades de almacen"})
                        returnedValue.update({"status_code": 422})
                        
                else:
                    session.rollback()
                    session.close()
                    returnedValue.update({"message": "Error: No grabo detalle de documento"})
                    returnedValue.update({"status_code": 422})

            else:
                session.rollback()
                session.close()
                returnedValue.update({"message": "Error: No se grabo cabecera"})
                returnedValue.update({"status_code": 422})
        else:
            session.rollback()
            session.close()
            returnedValue.update({"message": "Documento no contiene items"})
            returnedValue.update({"status_code": 422})

        return returnedValue

    except Exception as e:
        session.rollback()
        session.close()
        returnedValue.update({"message": f"An error ocurred: {e}"})
        returnedValue.update({"status_code": 422})
        return returnedValue
    finally:

        session.close()


@sales_route.post("/create_sales_order/", status_code=201)
async def Crear_Orden_Venta(body:sales_order, payload: jwt_dependecy):
    #ABSORVE URL
    pdf_url = ""
    #PDF BYTES
    pdf_bytes = ""
    try:

        if body.codigo_caja is not None: #venta por caja

            #VERIFICAMOS CAJA VALIDA
            caja_abierta = session.execute(
                    select(CashRegister.c.Status, CashRegister.c.WareID, CashRegister.c.User)
                    .filter(and_(CashRegister.c.CodeTS == body.codigo_caja,
                                CashRegister.c.WareID == body.id_ware,
                                CashRegister.c.Status == 'O'))
                    )
            
            caja = caja_abierta.mappings().first()

            if not(bool(caja)):
                return JSONResponse(
                    status_code= 422,
                    content= {
                            "data": {},
                            "message": "No existe una caja activa!",
                            "pdf": None
                        }
                )

            else:
                #OBTENER CORRELATIVO
                #CONSULTA Y BLOQUEA FILA DE SERIE
                response = session.execute(
                    select(DocSeries.c.Prefix, DocSeries.c.NextNumber)
                    .filter(DocSeries.c.DocTypeCode == body.doc_tipo,
                            DocSeries.c.WareCode == body.id_ware,
                            DocSeries.c.Status == 'Active', #ESTO SE AGREGA
                            DocSeries.c.SeriesType == 'Regular') #ESTO SE AGREGA
                    .with_for_update() #congela la fila hasta no exista un commit o un rollback
                )

                serie = response.mappings().first()

                if not(bool(serie)): # valida series disponibles
                    return JSONResponse(
                        status_code= 422,
                        content= {
                                "data": {},
                                "message": "No hay series disponibles!",
                                "pdf": None
                            }
                    )

                #VERIFICAMOS SI CORRELATIVO LLEGA AL MAXIMO
                correlativo = format_to_8digits(n=serie["NextNumber"], limit=8) #limite maximo de 8 digitos

                if not(bool(correlativo)):
                    return JSONResponse(
                        status_code= 422,
                        content= {
                                "data": {},
                                "message": "Correlativo llego a su limite, cambiar serie!",
                                "pdf": None
                            }
                    )

                #CREA PREFIJO Y CORRELATIVO SIGUIENTE
                series = series_internal(Prefix=serie["Prefix"], NextNumber=correlativo) #NextNumber en formato string

                #CREA DOCUMENTO NUBEFACT
                if body.doc_tipo in ('FAC', 'BOL'):

                    response =  await Crear_Documento_Externo_De_Venta(body=body, series=series, payload=payload) #creacion externa
                    status_code_doc = response.get("status_code", 422)
                    msg = response.get("message", "Error on Sales Route Line 1390")
                    data = response.get("data", {})

                elif body.doc_tipo in ('NV'):
                    status_code_doc = 201
                    msg = "ok"
                    data = {}
                else:
                    status_code_doc = 422
                    msg = "Error indeterminado"
                    data = {}
                
                if status_code_doc == 201: #verifica si creo documento externo
                
                    #CREA DOCUMENTO INTERNO
                    response =  await Crear_Documento_Interno_De_Venta(body=body, series=series, payload=payload) #creacion interna

                    #REGISTRAR DOCUMENTO EXTERNO
                    if (isinstance(data, dict) and data) and body.doc_tipo in ('FAC', 'BOL') and response["status_code"] == 201:

                        params = data
                        data_inner = response["data"]
                        params.update({"DocEntry": data_inner["docentry"] if "docentry" in data_inner else None})
                        
                        #ABSORVE URL
                        pdf_url = params.pop("pdf_url")
                        #PDF BYTES
                        pdf_bytes = params.pop("pdf_bytes")

                        data = external_document(**params)

                        response_x =  await Registrar_Estado_Documento_Externo(body=data, payload=payload) #creacion interna
                        
                        response={
                            "message": f"""Interno: {response["message"]} | Externo-Interno: {response_x["message"]}""",
                            "status_code": 201 if (response_x["status_code"] == 201 and response["status_code"] == 201) else 422,
                            "data": response["data"]
                            }
                 
                    else:
                        response = {
                            "status_code" : response["status_code"],
                            "data": response["data"],
                            "message": response["message"]
                        }
                
                    if response["status_code"] == 201 and body.doc_tipo in ('NV'):
                        stmt = (
                                    select(SalesOrder.c.DocNum.label("doc_num"), 
                                            SalesOrder.c.DocDate.label("doc_date"), 
                                            Company.c.docName.label("card_name"), 
                                            Company.c.LicTradNum.label("card_num"), 
                                            SalesOrder.c.SubTotal.label("sub_total"),
                                            SalesOrder.c.DiscSum.label("dscto_total"),
                                            SalesOrder.c.VatSum.label("tax_total"),
                                            SalesOrder.c.DocTotal.label("total"),
                                            PymntGroup.c.PymntGroupName.label("pay_method"),
                                            Product.c.title.label("dscp"),
                                            Product.c.isbn.label("cod"),
                                            SalesOrderDetail.c.Quantity.label("qty"),
                                            SalesOrderDetail.c.UnitPrice.label("pvp"),
                                            SalesOrderDetail.c.DiscSum.label("dsct"),
                                            SalesOrderDetail.c.Total.label("total_linea"))
                                    .join(SalesOrderDetail, SalesOrder.c.DocEntry == SalesOrderDetail.c.DocEntry)
                                    .join(Company, SalesOrder.c.CardCode == Company.c.cardCode)
                                    .join(Product, SalesOrderDetail.c.idProduct == Product.c.id)
                                    .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
                                    .order_by(asc(SalesOrderDetail.c.LineNum))
                                    .filter(SalesOrder.c.DocEntry == response["data"]["docentry"])
                                )
                        
                        result = session.execute(stmt).mappings().all()

                        if isinstance(result, list) and len(result) > 0:
                            respuesta = await Crear_Ticket_PDF(body=build_body_ticket(result), payload=payload)


                        return JSONResponse(
                            status_code= response["status_code"],
                            content= {
                                    "data": response["data"],
                                    "message": respuesta["message"] if not(respuesta["status"]) else response["message"],
                                    "pdf": respuesta["file"],
                                    "url": None
                                }
                        )
                    
                    elif response["status_code"] == 201 and body.doc_tipo in ('FAC', 'BOL'):
                        
                        return JSONResponse(
                            status_code= response["status_code"],
                            content= {
                                    "data": response["data"],
                                    "message": response["message"],
                                    "pdf": pdf_bytes,
                                    "url": pdf_url
                                }
                        )

                    
                    else:
                        return JSONResponse(
                            status_code= response["status_code"],
                            content= {
                                    "data": response["data"],
                                    "message": response["message"],
                                    "pdf": None,
                                    "url": None
                            }
                            )
                else:
                    return JSONResponse(
                            status_code= status_code_doc,
                            content= {
                                    "data": {},
                                    "message": msg,
                                    "pdf": None,
                                    "url": None
                                }
                        )
                
        else: #venta sin caja (por desarrollar)
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse(
        status_code= 422,
        content= {
                "data": None,
                "message": f"An error occurred: {e}",
                "pdf": None,
                "url": None
            }
        )
    finally:
        session.close()

@sales_route.post("/create_ticket_pdf/", status_code=201)
async def Crear_Ticket_PDF(body:Body_Ticket, payload: jwt_dependecy):
    returnedVal = {
                    "message": "Error indeterminado",
                    "status": False,
                    "file": None 
                   }
    
    try:

        doc = {
            "doc_num": body.doc_num,
            "doc_date": body.doc_date,
            "card_name": body.card_name,
            "card_num": body.card_num,
            "sub_total": body.sub_total,
            "dscto_total": body.dscto_total,
            "tax_total": body.tax_total,
            "total": body.total,
            "pay_method": body.pay_method,
            "doc_time": body.doc_time
        }

        items = [{"dscp": idx.dscp, "cod": idx.cod , "qty": idx.qty, "pvp": idx.pvp, "dsct": idx.dsct,"total_linea": idx.total_linea} for idx in body.items]

        status, message, file = generar_ticket(
                        nombre_archivo="ticket_venta.pdf",
                        logo_path="./logo.svg",
                        items=items,
                        do_c=doc
                    )
        
        returnedVal.update({"message": message, "status": status, "file": file})

        return returnedVal
        
    except Exception as e:
        print(f"An error occurred: {e}")
        returnedVal.update({"message": f"An error occurred: {e}", "status": False})
        return returnedVal


@sales_route.post("/create_close_ticket_pdf/", status_code=201)
async def Crear_Cierre_Ticket_PDF(body:Body_Ticket_Close, payload: jwt_dependecy):
    returnedVal = {
                    "message": "Error indeterminado",
                    "status": False,
                    "file": None 
                   }
    
    try:

        doc = {
            "caja": body.caja,
            "cash_teory": body.cash_teory,
            "diff": body.diff,
            "total": body.total,
            "card_total_plus_wallet_machine": body.card_total_walletmch,
            "wallet_no_machine_total": body.wallet_total_phone,
            "date": body.date,
            "vendedor": body.vendedor,
            "item2Sold": body.item2Sold,
            "item2Total": body.item2Total
        }

        items = [{"enum": idx.enum, "pay_method": idx.pay_method , "dscp": idx.dscp, "qty": idx.qty, "total_linea": idx.total_linea}
                 for idx in body.items]
        
        # print(doc)

        status, message, file = generar_ticket_close(
                        nombre_archivo="ticket_cierre.pdf",
                        items=items,
                        do_c=doc
                    )
        
        returnedVal.update({"message": message, "status": status, "file": file})

        return returnedVal
        
    except Exception as e:
        print(f"An error occurred: {e}")
        returnedVal.update({"message": f"An error occurred: {e}", "status": False, "file": None})
        return returnedVal
    
    
@sales_route.post("/sincronizar_documentos/", status_code=201)
async def sincronizacion_diaria_madrugada():
    print("Inicia sincronizacion a la 1 am ....... correcto!")

    # #solo se va considerar dos dias de antiguedad
    # today_server = await Get_Time() #<-- obtiene hora
    # today = dt.strptime(today_server["lima_transfer_format"], "%Y-%m-%d")
    # start_date = today - timedelta(days=2)  # TOMA LOS DOS DIAS ANTERIORES

    # stmt = (select( 
    #             SalesOrder.c.DocEntry,
    #             #Serie
    #             func.substring_index(SalesOrder.c.DocNum, '-', 1).label("NUM_SERIE_CPE"),
    #             #Correlativo
    #             func.substring_index(SalesOrder.c.DocNum, '-', -1).label("NUM_CORRE_CPE"),
    #             DocType.c.SunatCode.label("COD_TIP_CPE"),
    #             SalesOrder.c.DocDate.label("FEC_EMIS"),
    #             SalesOrderSunat.c.Status.label("estado_documento")
    #             )
    #     .join(DocType, SalesOrder.c.DocType == DocType.c.DocTypeCode)
    #     .join(SalesOrderSunat, SalesOrder.c.DocEntry == SalesOrderSunat.c.DocEntry)
    #     .join(SunatCodes, SalesOrderSunat.c.Status == SunatCodes.c.Code)
    #     .filter(and_(SunatCodes.c.IsFinal == 2,
    #                  SalesOrder.c.DocDate >= start_date))
    #     .order_by(asc(SalesOrder.c.DocEntry))
    #     )
    
    # returned_value = [dict(r) for r in session.execute(stmt).mappings().all()]

    # for row in returned_value:
    #     row["FEC_EMIS"] = row["FEC_EMIS"].strftime("%Y-%m-%d")


    # result  = await sincronizar_documentos_pendientes(docList=returned_value)

    # print(result)
