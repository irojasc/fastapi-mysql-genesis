from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, asc, func, insert, and_, desc, text, update, case
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlmodel.cashregister import CashRegister
from sqlmodel.docseries import DocSeries
from sqlmodel.salesorder import SalesOrder
from sqlmodel.doctype import DocType
from sqlmodel.salesorderdetail import SalesOrderDetail
from sqlmodel.company import Company
from sqlmodel.pymntgroup import PymntGroup
from sqlmodel.product import Product
from basemodel.sales import cash_register, sales_order, Body_Ticket, Body_Ticket_Close, Item_Ticket_Close
from functions.sales import generar_ticket, build_body_ticket, generar_ticket_close
from utils.validate_jwt import jwt_dependecy
from routes.authorization import get_user_permissions_by_module
from routes.catalogs import Get_Time
from config.db import con, session
from datetime import datetime as dt
from decimal import Decimal, ROUND_HALF_UP

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
                            OpenDate= cash_register_body.OpenDate or None,
                            CashOpen= cash_register_body.CashOpen
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
                        DocType.c.DocTypeName.label("DocType"),
                        SalesOrder.c.DocDate,
                        Company.c.docName.label("CardName"),
                        SalesOrder.c.DocTotal,
                        SalesOrder.c.DocCur.label("Moneda"),
                        PymntGroup.c.PymntGroupName.label("TipoPago")
                       )
                .join(DocType, SalesOrder.c.DocType == DocType.c.DocTypeCode)
                .join(Company, SalesOrder.c.CardCode == Company.c.cardCode)
                .join(PymntGroup, SalesOrder.c.PymntGroup == PymntGroup.c.PymntGroup)
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

@sales_route.get("/get_detail_sale_order/", status_code=200)
async def Get_Detail_Sale_Order(cash_register_body: cash_register = Depends(), payload: jwt_dependecy = None):
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
            #Validacion si tiene permisos para caja aperturada
            stmt = (
                    select(
                        CashRegister.c.User,
                        CashRegister.c.OpenDate,
                        CashRegister.c.CashOpen,
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

                stmt = (select(CashRegister.c.CashOpen.label("caja"),
                               CashRegister.c.CashSystem.label("cash_teory"),
                               CashRegister.c.CashDiff.label("diff"),
                               (CashRegister.c.CashOpen + CashRegister.c.CashSystem + CashRegister.c.CashDiff).label("total"),
                               CashRegister.c.CloseDate.label("date"),
                               CashRegister.c.User.label("vendedor")
                               )
                        .filter(CashRegister.c.CodeTS == cash_register_body.CodeTS))
                

                response = session.execute(stmt).mappings().all()
            
                # results = await Get_Detail_Sale_Order(cash_register_body=cash_register(CodeTS = cash_register_body.CodeTS))
                items = await Get_Detail_Sale_Order(cash_register_body=cash_register(CodeTS = cash_register_body.CodeTS))
                header = [
                            {
                            "caja": idx["caja"].to_eng_string(),
                            "cash_teory": "0.00" if idx["cash_teory"] is None else idx["cash_teory"].to_eng_string(),
                            "diff": "0.00" if idx["diff"] is None else idx["diff"].to_eng_string(),
                            "total": "0.00" if idx["total"] is None else idx["total"].to_eng_string(),
                            "date": "no-date" if idx["date"] is None else idx["date"].strftime("%d/%m/%Y"),
                            "vendedor": "no-vendedor" if idx["vendedor"] is None else idx["vendedor"]
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
      
@sales_route.post("/create_sales_note/", status_code=201)
async def Crear_Nota_De_Venta(body=sales_order, payload: jwt_dependecy = None):
    returnedValue={"message": "Error indeterminado",
                   "status_code": 422,
                   "data": {}}
    grabo_fila = 0

    try:
        #VERIFICAMOS CAJA ABIERTA SIEMRPE QUE LA PETICION VENGA DE UNA CAJA
        caja_abierta = session.execute(
                select(CashRegister.c.Status, CashRegister.c.WareID, CashRegister.c.User)
                .filter(CashRegister.c.CodeTS == body.codigo_caja)
                )
        
        rows = caja_abierta.mappings().all()

        if(isinstance(rows, list) and len(rows) > 0 and rows[0]["Status"] == 'O'):

            #CONSULTA Y BLOQUEA FILA DE SERIE
            response = session.execute(
                select(DocSeries.c.Prefix, DocSeries.c.NextNumber)
                .filter(DocSeries.c.DocTypeCode == body.doc_tipo,
                        DocSeries.c.WareCode == rows[0]["WareID"])
                .with_for_update() #congela la fila hasta no exista un commit o un rollback
            )

            series = response.mappings().all()
            serie = series[0]["Prefix"]
            correlativo = series[0]["NextNumber"]

            #NUEVO SERIE-CORRELATIVO EN DOCUMENTO
            numero_documento = f"""{serie}-{str(correlativo).rjust(8, '0')}""" 

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
                            SlpCode=rows[0]["User"],
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
                                    idWare=rows[0]["WareID"],
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
                                    'idWa' : rows[0]["WareID"]
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
                                            DocSeries.c.WareCode == rows[0]["WareID"])
                                    .values(
                                    LastNumber=correlativo,
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
        else:
            returnedValue.update({"status_code": 422})
            returnedValue.update({"message": "La caja se encuentra cerrada"})

        return returnedValue

    
    except Exception as e:
        session.rollback()
        session.close()
        returnedValue.update({"message": f"An error ocurred: {e}"})
        returnedValue.update({"status_code": 422})
        return returnedValue

    

@sales_route.post("/create_sales_order/", status_code=201)
async def Crear_Orden_Venta(body:sales_order, payload: jwt_dependecy):
    try:
        if body.doc_tipo == 'NV':
            response =  await Crear_Nota_De_Venta(body=body)

            response = {
                "status_code" : response["status_code"],
                "data": response["data"],
                "message": response["message"]
            }
     
            # respuesta = {
            #     "status" : False,
            #     "data": {},
            #     "message": "error al generar ticket",
            #     "file": None
            # }

            # print(response)
            
            # print(respuesta)

            if response["status_code"] == 201:
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
                    # status_code= 422 if not(respuesta["status"]) else response["status_code"],
                    status_code= response["status_code"],
                    content= {
                            "data": response["data"],
                            "message": respuesta["message"] if not(respuesta["status"]) else response["message"],
                            "pdf": respuesta["file"]
                        }
                )
            
            else:
                return JSONResponse(
                    status_code= response["status_code"],
                    content= {
                            "data": response["data"],
                            "message": response["message"],
                            "pdf": None
                        }
                )
            

        else:
            #aqui va el caso cuando no es nota de venta
            pass

    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse(
        status_code= 422,
        content= {
                "data": None,
                "message": f"An error occurred: {e}",
                "pdf": None
            }
        )

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
            "date": body.date,
            "vendedor": body.vendedor
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