from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, text, desc, asc, or_, func, and_, null, literal
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from utils.validate_jwt import jwt_dependecy
from utils.converters import binary2bool
from config.db import con, session, aliased
from sqlmodel.product import Product
from sqlmodel.ware import Ware
from sqlmodel.language import Language
from sqlmodel.item import Item
from sqlmodel.transfer import Transfer
from sqlmodel.ware_product import Ware_Product
from sqlmodel.transfer_product import Transfer_Product
from sqlmodel.operation_reason import Operation_Reason
from sqlmodel.uom import UOM
from sqlmodel.company import Company
from functions.catalogs import normalize_last_sync
from functions.inventory import get_all_inventory_data, get_all_active_transfer
from sqlalchemy import insert, delete, update
from basemodel.inventory import InOut_Qty, WareProduct
from basemodel.product import ware_product_
from basemodel.ware import ware_edited
# from routes.company import Get_All_Business_Partners_By_Param
from routes.catalogs import Get_Taxes, Get_Time
from decimal import Decimal
import json
from datetime import datetime

inventory_route = APIRouter(
    prefix = '/inventory',
    tags=['Inventory']
)

# json_object = json.dumps(result_format, indent=4, default=repr).encode('utf8')
            # json_object = json.dumps(result_format, ensure_ascii=False).encode('utf8')
            # outfile.write(str(json_object, 'utf-8'))
            # outfile.write(json_object)
#aqui falta agregar la parte donde solo algunos pueden ejecutar este comando

@inventory_route.get("/", status_code=200)
async def Get_All_Inventory_and_Data_Product(token_key: str = None, idProduct: int = None, jwt_dependency: jwt_dependecy = None):
    """Cuando va con la clave, retorna todo el stock con last_sync"""
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)   # 👈 o str(obj) si quieres conservar exactitud
        raise TypeError
    
    def get_statement(idProduct:int=None):
        stmt = (select(Ware.c.code.label("ware_code"), Item.c.code.label("item_code"), Product.c.id.label("id_product"), Product.c.isbn, Product.c.title, Product.c.autor, 
            Product.c.publisher, Product.c.dateOut, Language.c.language, Product.c.pages, Product.c.weight, 
            Product.c.cover, Product.c.width, Product.c.height, Ware_Product.c.qtyNew, Ware_Product.c.qtyOld, 
            Ware_Product.c.qtyMinimun, Ware_Product.c.pvNew, Ware_Product.c.pvOld, Ware_Product.c.loc, 
            Ware_Product.c.isEnabled, Ware_Product.c.dsct, Ware_Product.c.idWare, Ware_Product.c.qtyMaximum, 
            Product.c.isDelete, Product.c.InvntItem, Product.c.SellItem, Product.c.BuyItem, Product.c.InvntryUom, 
            Product.c.LastPurPrc, literal(None).label("LastProvider"), Product.c.VatBuy, Product.c.VatSell). \
            join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True). \
            join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True). \
            join(Language, Product.c.idLanguage == Language.c.id, isouter=True). \
            join(Item, Product.c.idItem == Item.c.id).\
            order_by(asc(Product.c.id))
            )
        
        if idProduct is not None:
            stmt = stmt.filter(Product.c.id == idProduct)
        
        results = session.execute(stmt).mappings().all() #retorna en formato diccionario
        return get_all_inventory_data(results)

    returned = False
    try:
        if bool(token_key):
            if token_key == 'CHUSPa@123':
                result_format = get_statement() #cuando va vacio, trae todos los resultados

                utc_time = await Get_Time()
                returnedVal = {
                    "last_sync": utc_time["lima"],
                    "options":result_format
                }

                with open("sample.json", "w", encoding='utf8') as outfile:
                    json.dump(returnedVal, outfile, ensure_ascii=False, default=convert_decimal)
                returned = True
            else:
                #aqui retorna clave incorrecta, false por ahora
                pass
        elif bool(idProduct) and idProduct > 0:
                result_format = get_statement(idProduct=idProduct) #cuando va vacio, trae todos los resultados
                returned = result_format

    except Exception as e:
        print(f"Get_All_Inventory_and_Data_Product/nopair:get:An error ocurred: {e}")
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        session.rollback()
    finally:
        session.close()
        return returned

@inventory_route.get("/lastchanges", status_code=200)
# async def Get_Last_Inventory_Data_Product_Changes(inputDate: str = '2024-01-01', jwt_dependency: jwt_dependecy = None):
async def Get_Last_Inventory_Data_Product_Changes(last_sync: datetime = Query(..., description="Formato esperado: YYYY-MM-DDTHH:MM:SSZ (ISO8601)"), jwt_dependency: jwt_dependecy = None):
    returned = False
    try:
        #QUITA 10 MINUTOS PARA REALIZAR LA CONSULTA
        formated_lastsync = normalize_last_sync(last_sync) #resta 5 minutos para traer todos los cambios

        subquery_ = select(Product.c.id).join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True)\
            .join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True)\
            .join(Language, Product.c.idLanguage == Language.c.id, isouter=True)\
            .join(Item, Product.c.idItem == Item.c.id)\
            .filter(
                or_(Product.c.creationDate >= formated_lastsync, 
                    Product.c.editDate >= formated_lastsync, 
                    Ware_Product.c.creationDate >= formated_lastsync, 
                    Ware_Product.c.editDate >= formated_lastsync))

        #get select subquery sqlalchemy?
        stmt = (select(Ware.c.code.label("ware_code"), Item.c.code.label("item_code"), Product.c.id.label("id_product"), Product.c.isbn, Product.c.title, Product.c.autor, 
                    Product.c.publisher, Product.c.dateOut, Language.c.language, Product.c.pages, Product.c.weight, 
                    Product.c.cover, Product.c.width, Product.c.height, Ware_Product.c.qtyNew, Ware_Product.c.qtyOld, 
                    Ware_Product.c.qtyMinimun, Ware_Product.c.pvNew, Ware_Product.c.pvOld, Ware_Product.c.loc, 
                    Ware_Product.c.isEnabled, Ware_Product.c.dsct, Ware_Product.c.idWare, Ware_Product.c.qtyMaximum, 
                    Product.c.isDelete, Product.c.InvntItem, Product.c.SellItem, Product.c.BuyItem, Product.c.InvntryUom, 
                    Product.c.LastPurPrc, literal(None).label("LastProvider"), Product.c.VatBuy, Product.c.VatSell). \
                    join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True). \
                    join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True). \
                    join(Language, Product.c.idLanguage == Language.c.id, isouter=True).join(Item, Product.c.idItem == Item.c.id). \
                    filter(Product.c.id.in_(subquery_)).order_by(asc(Product.c.id)))
        
        results = session.execute(stmt).mappings().all() #obtine en formato diccionario
        result_format = get_all_inventory_data(results)
        utc_time = await Get_Time() #consulta hora actual del sistema
        # print('Consulta ware products: Hora Lima: ', utc_time["lima"])
        
        returned = {"last_sync": utc_time["lima"], "options" : result_format}
        # print(returned)
    except Exception as e:
        print(f"Get_Last_Inventory_Data_Product_Changes/nopair:get:An error ocurred: {e}")
        returned = False
    except SQLAlchemyError as ex:
        print("roll")
        session.rollback()
        session.close()
        print("An SqlAlchemmy happened ", ex)
    finally:
        session.close()
        return returned

@inventory_route.get("/warehouse_product", status_code=200)
async def Get_WareHouse_Product_By_Id(idProduct: str = None, jwt_dependency: jwt_dependecy = None):
    """Id vacio, trae formato para creacion de articulo"""
    try:
        body = {}
        waredata = {}
        #ITEM, Obtiene tipos de items
        itemList = session.query(Item.c.code, Item.c.item).all()
        #LANGUAGE, Obtiene tipos de lenguajes
        langList = session.query(Language.c.code, Language.c.language).all()
        
        if not(idProduct): #CASO 1| CREAR NUEVO ARTICULO
            #ID
            body.update({'id': str(session.query(func.max(Product.c.id) + 1).scalar())}) #carga id
            
            #ITEM
            body.update({'item': {
                'itemCode': None,
                'options': list(map(lambda idx: {'code': idx[0], 'name': idx[1]}, itemList))}})

            #ISBN
            body.update({'isbn': None})
            #TITLE
            body.update({'title': None})
            #AUTOR
            body.update({'autor': None})
            #PUBLISHER
            body.update({'publisher': None})
            #RELEASE
            body.update({'release': None})
            #RELEASE
            body.update({'pages': 0})
            #LANGUAGE
            body.update({'language': {
                'langCode': None,
                'options': list(map(lambda idx: {'code': idx[0], 'name': idx[1]}, langList))}})

            #WEIGHT
            body.update({'weight': None})
            #LARGE
            body.update({'large': None})
            #WIDTH
            body.update({'width': None})
            #HEIGHT
            body.update({'height': None})
            #COVER
            body.update({'cover': None})
            #SUMMARY
            body.update({'summary': None})
            #WHOLESALE
            body.update({'wholesale': False})
            #ANTIQUE
            body.update({'antique': False})

            #WEBPROMOTION
            body.update({'webprom': False })

            #CardCode
            body.update({'CardCode': None })

            # #BusinessPartner (opciones para que muestren en el frond)
            # list_ = await Get_All_Business_Partners_By_Param(CardType='S') #obtine proveedores
            # if isinstance(list_, list):
            #     list_modified = list(map(lambda x: {"CardCode": x["CardCode"], "CardName": x["CardName"]}, list_))
            #     body.update({'BusinessPartners': list_modified})
            # else:
            #     body.update({'BusinessPartners': []})
            # #
            body.update({'InvntItem': 'N'})
            body.update({'SellItem': 'N'})
            body.update({'BuyItem': 'N'})
          
            #Unidades de inventario 
            body.update({'InvntryUom': 'NIU'}) #ESTO IRA POR DEFECTO

            #(opciones para unidades)
            list_units = await Get_All_Units_Of_Measurement() #obtine unidades
            if isinstance(list_units, list):
                body.update({'UOMS': [dict(x) for x in list_units]})
            else:
                body.update({'UOMS': []})
            #

            #taxes compra
            body.update({'VatBuy': None})

            #opciones para impuesto compra
            list_pur_taxes = await Get_Taxes(type='p') #purchase
            if isinstance(list_pur_taxes, list):
                body.update({'Pur_Taxes': [{'VatCode': item['VatCode'], 'VatName': item['VatName'].upper()} for item in list_pur_taxes]})
            else:
                body.update({'Pur_Taxes': []})
            #
         
            #taxes venta
            body.update({'VatSell': None})

            #opciones para impuesto venta
            list_sel_taxes = await Get_Taxes(type='s') #sell
            if isinstance(list_sel_taxes, list):
                body.update({'Sel_Taxes': [{'Code': item['Code'], 'Name': item['Name']} for item in list_sel_taxes]})
            else:
                body.update({'Sel_Taxes': []})
            #

            #WAREDATA
            # wareDataList = session.query(Ware.c.code, Ware.c.isVirtual).all()
            # SE OBTIENE DATA DE WARE QUE SOLO ESTA ACTIVO
            wareDataList = session.query(Ware.c.code, Ware.c.isVirtual) \
            .filter(Ware.c.enabled == 1) \
            .all()

            for key in wareDataList:
                waredata.update({
                    key[0]: {
                    'exits': False,
                    'active': False,
                    'location': '',
                    'stockMin': 0,
                    'stockMax': 0,
                    'pvp1': 0.0,
                    'pvp2': 0.0,
                    'dsct': 0.0,
                    'isVirtual': binary2bool(key[1]),
                        }
                })
            body.update({'waredata': waredata})
            #ISDELETE
            body.update({'isDelete': False})
            #FORMDATE
            body.update({'formDate': ''})
            session.close()
            
            content = {
            "success": True,
            "message": "Todo ok!",
            "object": body
            }   
            return JSONResponse(content=content, status_code=200)
        
        else: #CASO 2| EDITAR ARTICULO EXISTENTE
            stmt = (
                select(Product, Item.c.code.label("item_code"), Language.c.code.label("lang_code"))
                .join(Item, Product.c.idItem == Item.c.id)
                .outerjoin(Language, Product.c.idLanguage == Language.c.id)
                .where(Product.c.id == int(idProduct))
            )

            product = session.execute(stmt).mappings().first() #obtine en formato diccionario

            # #PRODUCT
            body.update({'id': str(product["id"])}) #ID
            body.update({'item': {
                'itemCode': product["item_code"] or None,
                'options': list(map(lambda idx: {'code': idx[0], 'name': idx[1]}, itemList))}}) #ID
            body.update({'isbn': product["isbn"] or None}) #ISBN
            body.update({'title': product["title"] or None}) #TITLE
            body.update({'autor': product["autor"] or None}) #AUTOR
            body.update({'publisher': product["publisher"] or None}) #PUBLISHER
            body.update({'release': str(product["dateOut"].year or '') if bool(product["dateOut"]) else None}) #RELEASE
            body.update({'pages': product["pages"] or None}) #PAGES
            body.update({'language': {
                'langCode': product["lang_code"] or None,
                'options': list(map(lambda idx: {'code': idx[0], 'name': idx[1]}, langList))}}) #LANGUAGE
            body.update({'weight': product["weight"] or None}) #WEIGHT
            body.update({'large': product["large"] or None}) #LARGE
            body.update({'width': product["width"] or None}) #WIDTH
            body.update({'height': product["height"] or None}) #HEIGHT
            body.update({'cover': None if product["cover"] is None else binary2bool(product["cover"])}) #COVER
            body.update({'summary': product["content"] or ''}) #SUMMARY
            body.update({'wholesale': False if product["wholesale"] is None else binary2bool(product["wholesale"])}) #WHOLESALE
            body.update({'antique': False if product["antique"] is None else binary2bool(product["antique"])}) #ANTIQUE
            body.update({'webprom': False if product["atWebProm"] is None else binary2bool(product["atWebProm"])}) #WEBPROMOTION
            body.update({'CardCode': product["CardCode"]}) #proveedor

            #BusinessPartner (opciones para que muestren en el frond)
            # list_ = await Get_All_Business_Partners_By_Param(CardType='S') #obtine proveedores
            # if isinstance(list_, list):
            #     list_modified = list(map(lambda x: {"CardCode": x["CardCode"], "CardName": x["CardName"]}, list_))
            #     body.update({'BusinessPartners': list_modified})
            # else:
            #     body.update({'BusinessPartners': []})
            #
            body.update({'InvntItem': product["InvntItem"]})
            body.update({'SellItem': product["SellItem"]})
            body.update({'BuyItem': product["BuyItem"]})

            #Unidades de inventario 
            body.update({'InvntryUom': product["InvntryUom"]})

            #(opciones para unidades)
            list_units = await Get_All_Units_Of_Measurement() #obtine unidades
            if isinstance(list_units, list):
                body.update({'UOMS': [dict(x) for x in list_units]})
            else:
                body.update({'UOMS': []})
            #

            #taxes compra
            body.update({'VatBuy': product["VatBuy"]})

            #opciones para impuesto compra
            list_pur_taxes = await Get_Taxes(type='p') #purchase
            if isinstance(list_pur_taxes, list):
                body.update({'Pur_Taxes': [{'VatCode': item['VatCode'], 'VatName': item['VatName'].upper()} for item in list_pur_taxes]})
            else:
                body.update({'Pur_Taxes': []})
            #
         
            #taxes venta
            body.update({'VatSell': product["VatSell"]})

            #opciones para impuesto venta
            list_sel_taxes = await Get_Taxes(type='s') #sell
            if isinstance(list_sel_taxes, list):
                body.update({'Sel_Taxes': [{'Code': item['Code'], 'Name': item['Name']} for item in list_sel_taxes]})
            else:
                body.update({'Sel_Taxes': []})
            #

            #WAREDATA
            # SE OBTIENE DATA DE WARE QUE SOLO ESTA ACTIVO
            wareData = session.query(Ware.c.code, Ware_Product, Ware.c.isVirtual). \
                        outerjoin(Ware_Product, (Ware.c.id == Ware_Product.c.idWare) & (Ware_Product.c.idProduct == int(idProduct))) \
                        .filter(Ware.c.enabled == 1) \
                        .all()
            for key in wareData:
                waredata.update({
                    key[0]: {
                    'exits': False if key[2] is None else True,
                    'active': False if key[10] is None else binary2bool(key[10]),
                    'location': '' if key[7] is None else ('' if key[7] == 'SIN UBICACION' else key[7]),
                    'stockMin': key[9] or 0,
                    'stockMax': key[13] or 0,
                    'pvp1': key[5] or 0.0,
                    'pvp2': key[6] or 0.0,
                    'dsct': key[8] or 0.0,
                    'isVirtual': None if key[14] is None else binary2bool(key[14]),
                        }
                })
            body.update({'waredata': waredata})
            body.update({'isDelete': False if product["isDelete"] is None else binary2bool(product["isDelete"])}) #ISDELETE
            body.update({'formDate': ''})

            session.close()

            content = {
            "success": True,
            "message": "Todo ok!",
            "object": body
            }   
            
            return JSONResponse(content=content, status_code=200)
    except Exception as e:
        print(f"Get_WareHouse_Product_By_Id :get:An error ocurred: {e}")
        content = {
            "success": False,
            "message": f"{e}",
            "object": None
            } 
        return JSONResponse(content=content, status_code=500)
    except SQLAlchemyError as ex:
        session.rollback()
        session.close()
        content = {
            "success": False,
            "message": f"{ex}",
            "object": None
            } 
        return JSONResponse(content=content, status_code=500)
        # print("Get_WareHouse_Product_By_Id: An error ocurred", ex)



#obtiene las trasferencias entre almacenes y los ingresos como salidas
@inventory_route.get("/transfer/checkcurrents", status_code=200)
async def Get_Current_Transfers_By_Ware_And_Date(curIdWare: int = None, curDate: str = None, stateAbove: int = 1, jwt_dependency: jwt_dependecy = None):
    
    returned = {
        "status": 406,
        "message": "No data available",
        "result": [],
    }
    try:
        # Create aliases for the Ware table
        fWare = aliased(Ware)
        tWare = aliased(Ware)

        results = session.query(Transfer.c.codeTS,
                                fWare.c.code,
                                tWare.c.code,
                                Transfer.c.fromUser,
                                Transfer.c.toUser, 
                                Transfer.c.fromDate, 
                                Transfer.c.toDate, 
                                Transfer.c.state,
                                Transfer.c.note,
                                Transfer.c.cardCode,
                                #cambiar docName por cardName
                                Company.c.docName,
                                Operation_Reason.c.operation,
                                Operation_Reason.c.reason,
                                Transfer_Product.c.idProduct,
                                Product.c.isbn,
                                Product.c.title, 
                                Product.c.autor, #<-- nuevo 1
                                Product.c.publisher, #<-- nuevo 2
                                Transfer_Product.c.qtyNew,
                                Transfer_Product.c.qtyOld,
                                )  \
                                .join(Transfer_Product, Transfer.c.codeTS == Transfer_Product.c.idTransfer) \
                                .join(Product, Transfer_Product.c.idProduct == Product.c.id) \
                                .join(fWare, Transfer.c.fromWareId == fWare.c.id) \
                                .join(tWare, Transfer.c.toWareId == tWare.c.id, isouter=True) \
                                .join(Operation_Reason, Transfer.c.idOperReas == Operation_Reason.c.idOperReas, isouter=True) \
                                .join(Company, Transfer.c.cardCode == Company.c.cardCode, isouter=True) \
                                .filter(
                                    or_(Transfer.c.state > stateAbove, Transfer.c.toDate == curDate), 
                                    or_(Transfer.c.fromWareId == curIdWare, Transfer.c.toWareId == curIdWare)) \
                                .order_by(desc(Transfer.c.codeTS)) \
                                .all()
        (results, message) = get_all_active_transfer(results)
        returned = {
        "status": 200,
        "message": message,
        "result": results,
        }
    except Exception as e:
        print(f"Get_Open_Transfers :get:An error ocurred: {e}")
    except SQLAlchemyError as ex:
        print("roll")
        session.rollback()
        session.close()
        print("Get_Open_Transfers: An error ocurred", ex)
    finally:
        session.close()
        return returned

@inventory_route.get("/transfer/checkbytimestamp", status_code=200)
async def Get_Transfer_By_TimeStamp(curIdWare: int = None, timeStamp: str = '', jwt_dependency: jwt_dependecy = None):
    returned = {
        "status": 406,
        "message": "No data available",
        "result": [],
    }
    try:
        # Create aliases for the Ware table
        fWare = aliased(Ware)
        tWare = aliased(Ware)

        results = session.query(Transfer.c.codeTS,
                                fWare.c.code,
                                tWare.c.code,
                                Transfer.c.fromUser,
                                Transfer.c.toUser, 
                                Transfer.c.fromDate, 
                                Transfer.c.toDate, 
                                Transfer.c.state,
                                Transfer.c.note,
                                Transfer.c.cardCode,
                                #cambiar docName por cardName
                                Company.c.docName,
                                Operation_Reason.c.operation,
                                Operation_Reason.c.reason,
                                Transfer_Product.c.idProduct,
                                Product.c.isbn,
                                Product.c.title,
                                Product.c.autor, #<-- nuevo 1
                                Product.c.publisher, #<-- nuevo 2
                                Transfer_Product.c.qtyNew,
                                Transfer_Product.c.qtyOld,
                                Ware_Product.c.pvNew,
                                )  \
                                .join(Transfer_Product, Transfer.c.codeTS == Transfer_Product.c.idTransfer) \
                                .join(Ware_Product, and_(Transfer_Product.c.idProduct == Ware_Product.c.idProduct, Ware_Product.c.idWare == curIdWare), isouter=True) \
                                .join(Product, Transfer_Product.c.idProduct == Product.c.id) \
                                .join(fWare, Transfer.c.fromWareId == fWare.c.id) \
                                .join(tWare, Transfer.c.toWareId == tWare.c.id, isouter=True) \
                                .join(Operation_Reason, Transfer.c.idOperReas == Operation_Reason.c.idOperReas, isouter=True) \
                                .join(Company, Transfer.c.cardCode == Company.c.cardCode, isouter=True) \
                                .filter(Transfer.c.codeTS == timeStamp) \
                                .all()
        (results, message) = get_all_active_transfer(results)

        returned = {
        "status": 200,
        "message": message,
        "result": results,
        }
    except Exception as e:
        print(f"Get_Transfer_By_TimeStamp :get:An error ocurred: {e}")
    except SQLAlchemyError as ex:
        print("roll")
        session.rollback()
        session.close()
        print("Get_Transfer_By_TimeStamp: An error ocurred", ex)
    finally:
        session.close()
        return returned

@inventory_route.patch("/updatequantities", status_code=200)
async def Update_Inventory_Quantities(invoice: InOut_Qty, jwt_dependency: jwt_dependecy = None):
    returned = False
    message = 'Ok'
    try:
        #HORA DE REGISTRO
        create_date = await Get_Time()

        def UpdateQtyWareProduct(objInvoic_e = None):
            #state 1, transferencia cerrada [WARE_PRODUCT]
            id_ware = session.query(Ware.c.id).filter(Ware.c.code == objInvoic_e.fromWare).first()[0]
            params = list(map(lambda x: {'qtyN': (x.qtyNew if objInvoic_e.operacion == 'ingreso' or objInvoic_e.operacion == 'inventario' else -abs(x.qtyNew)),
                                            'qtyO': (x.qtyOld if objInvoic_e.operacion == 'ingreso' or objInvoic_e.operacion == 'inventario' else -abs(x.qtyOld)),
                                            # 'editDa': objInvoic_e.fromDate,
                                            'editDa': create_date["lima_bd_format"] or None,
                                            'location': objInvoic_e.ubicacion if bool(objInvoic_e.ubicacion) else None,
                                            'idPro' : int(x.code.split('_')[1]),
                                            'idWa' : id_ware}, objInvoic_e.list_main))
            if bool(objInvoic_e.ubicacion):
                stmt = text(f"UPDATE ware_product set qtyNew = qtyNew + :qtyN, qtyOld = qtyOld + :qtyO, editDate = :editDa, loc = :location where idProduct = :idPro and idWare = :idWa")
            else:
                stmt = text(f"UPDATE ware_product set qtyNew = qtyNew + :qtyN, qtyOld = qtyOld + :qtyO, editDate = :editDa where idProduct = :idPro and idWare = :idWa")
            response_3 = session.execute(stmt, params)
            session.commit()

            return response_3.rowcount > 0


        # if(response_3.rowcount > 0 and invoice.operacion != 'inventario'): #REGISTRA EN LA TABLA TRANSFER
        if(invoice.operacion != 'inventario'): #REGISTRA EN LA TABLA TRANSFER

            id_operation_reason = session.query(Operation_Reason.c.idOperReas).filter(Operation_Reason.c.operation == invoice.operacion).filter(Operation_Reason.c.reason == invoice.operacion_motivo).subquery()
            id_fromWare = session.query(Ware.c.id).filter(Ware.c.code == invoice.fromWare).subquery()
            id_toWare = session.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).subquery()
            stmt1 = (
                insert(Transfer).
                values(
                    codeTS = invoice.codeTS,
                    fromWareId= id_fromWare.as_scalar(),
                    toWareId= id_toWare.as_scalar(),
                    fromUser=invoice.curUser,
                    fromDate= create_date["lima_transfer_format"],
                    toDate= None if invoice.toDate is None else create_date["lima_transfer_format"] if invoice.fromDate == invoice.toDate else invoice.toDate,
                    state= invoice.state,
                    note= invoice.comentario,
                    cardCode= invoice.socio_docNum,
                    idOperReas=id_operation_reason.as_scalar(),
                    )
                )
            response_1 = session.execute(stmt1)
            session.commit()

            if(response_1.rowcount > 0 and invoice.operacion != 'inventario'): #REGISTRA EN LA TABLA TRANSFER PRODUCTO DETALLE
                stmt2 = Transfer_Product.insert()
                products_to_insert = list(map(lambda x: {'idTransfer': invoice.codeTS, 'idProduct': int(x.code.split('_')[1]), 'qtyNew': x.qtyNew, 'qtyOld': x.qtyOld}, invoice.list_main))
                response_2 = session.execute(stmt2, products_to_insert)
                session.commit()
                if(response_2.rowcount > 0):
                    #AQUI RECIEN DESCUENTA EN LA TABLA WARE_PRODUCT
                    returned = UpdateQtyWareProduct(objInvoic_e = invoice)
            else:
                returned = False

        elif(invoice.operacion == 'inventario'): #(PARA MODO INVENTARIO)
            returned = UpdateQtyWareProduct(objInvoic_e = invoice)

        else:
            returned = False

    except Exception as e:
        print(f"Update_Inventory_Quantities/nopair:patch:An error ocurred: {e}")
        session.close()
        returned = False
        message = f"Exception: {e}"
    except SQLAlchemyError as ex:
        returned = False
        print("roll")
        session.rollback()
        session.close()
        message = f"Sql Exception: {ex}"
    finally:
        session.close()
        return {
            "state":  returned,
            "message": message
        }

@inventory_route.patch("/product/changelocation", status_code=200)
async def change_product_location(invoice: WareProduct = None, jwt_dependency: jwt_dependecy = None):
    # response model
    response = {
        "state": False,
        "result": [],
        "message": ""
    }
    try:
        #HORA DE REGISTRO
        create_date = await Get_Time()

        idWare = select(Ware.c.id).where(Ware.c.code == invoice.wareCode).limit(1).subquery()
        session.execute(update(Ware_Product)
                        .where(Ware_Product.c.idProduct == invoice.idProduct, Ware_Product.c.idWare == idWare.as_scalar())
                        .values(loc = invoice.loc, editDate = create_date["lima_bd_format"] or None)
                        # .values(loc = invoice.loc, editDate = invoice.editDate)
                        )
        session.commit()
        response["state"] = True
        response["message"] = 'Cambios aplicados'

    except Exception as e:
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"

    except SQLAlchemyError as e:
        print("roll")
        session.rollback()
        session.close()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"
        
    finally:
        session.close()
        return response

@inventory_route.post("/inventorymode", status_code=200)
async def run_inventory_mode(input_param: ware_edited = None, jwt_dependency: jwt_dependecy = None): 
    # response model
    response = {
        "state": False,
        "result": [],
        "message": ""
    }
    try:
        
        #HORA DE REGISTRO
        create_date = await Get_Time()

        result_1 = session.execute(update(Ware_Product)
                                   .where(and_(Ware_Product.c.idWare == input_param.wareCode,
                                               or_(Ware_Product.c.qtyNew != 0,
                                                   Ware_Product.c.qtyOld != 0)
                                                   )
                                   )
                                   .values(qtyNew=0, qtyOld=0)
                                    )   
        session.commit()
        if(result_1.rowcount >= 0):
            #(2)#luego actualiza la fecha de inventario
            # 2025-04-13
            # result_2 = session.execute(update(Ware)
            #                             .where(and_(Ware.c.id == input_param.wareCode,
            #                                        or_(Ware.c.inv_date != input_param.editDate,
            #                                            Ware.c.inv_date == None)))
            #                             .values(inv_date = input_param.editDate)
            #                             )
            result_2 = session.execute(update(Ware)
                                        .where(and_(Ware.c.id == input_param.wareCode,
                                                   or_(Ware.c.inv_date != create_date["lima_transfer_format"],
                                                       Ware.c.inv_date == None)))
                                        .values(inv_date = create_date["lima_transfer_format"])
                                        )
            # result_3 = session.execute(update(Ware).where((Ware.c.id == input_param.wareCode) & (Ware.c.inv_clean == 1)).\
            #                          values(inv_clean = b'\x00'))
            
            result_3 = session.execute(update(Ware)
                                       .where(and_(Ware.c.id == input_param.wareCode, Ware.c.inv_clean == 1))
                                       .values(inv_clean = b'\x00')
                                     )
            session.commit()
            if(result_2.rowcount >= 0 and result_3.rowcount >= 0):
                response["state"] = True
                response["message"] = f"Afectadas ware_product: {result_1.rowcount}, Ware: {result_2.rowcount}, invt_clean: {result_3.rowcount}"

    except Exception as e:
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"
        session.close()

    except SQLAlchemyError as e:
        session.rollback()
        session.close()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"
    finally:
        session.close()
        return response

@inventory_route.patch("/transfer/downgradestate", status_code=200)
async def downgrade_transfer_state(invoice: InOut_Qty = False, jwt_dependency: jwt_dependecy = None):
    # response model
    response = {
        "state": False,
        "result": [],
        "message": "",
        "toDate": None
    }
    try:
        #HORA DE REGISTRO
        create_date = await Get_Time()

        #si no es final state
        if(not(invoice.isFinalState)):
            #solamente baja en uno el state
            session.execute(update(Transfer).
                            where(Transfer.c.codeTS == invoice.codeTS).
                            values(state = Transfer.c.state - 1, 
                                   toUser= invoice.curUser))
            session.commit()
            response["state"] = True
            response["message"] = f'Se actualizo Transfer con codigo {invoice.codeTS}'
            response["result"] = False
        else:
            toDat_e = create_date["lima_transfer_format"]
            #baja en uno el state y actuliza las cantidades en ware_product
            session.execute(update(Transfer).
                            where(Transfer.c.codeTS == invoice.codeTS).
                            values(state = Transfer.c.state - 1,
                                    toDate= toDat_e))
            session.commit()
            #actualiza las cantidades en ware_product
            items_quantity = session.query(Transfer_Product.c.idProduct, Transfer_Product.c.qtyNew, Transfer_Product.c.qtyOld). \
            filter(Transfer_Product.c.idTransfer == invoice.codeTS).all()
            #id de toWare suqquery
            id_toWare = session.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).first()[0]

            params = list(map(lambda x: {
                'qtyN': x[1],
                'qtyO': x[2],
                # 'editDa': invoice.toDate,
                'editDa': toDat_e or None,
                'idPro' : int(x[0]),
                'idWa' : id_toWare}, items_quantity))
            
            stmt = text(f"UPDATE ware_product set qtyNew = qtyNew + :qtyN, qtyOld = qtyOld + :qtyO, editDate = :editDa where idProduct = :idPro and idWare = :idWa")
            response_3 = session.execute(stmt, params)
            session.commit()
            if(response_3.rowcount > 0):
                response["state"] = True
                response["message"] = f'Se agregaron items con codigo {invoice.codeTS}'
                response["result"] = True
                partes = toDat_e.split("-") # <- split para cambiar el orden de la fecha
                response["toDate"] = partes[2] + '-' + partes[1] + '-' + partes[0] #<- fecha requerida para frond

    except Exception as e:
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"

    except SQLAlchemyError as e:
        print("roll")
        session.rollback()
        session.close()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"
        
    finally:
        session.close()
        return response

@inventory_route.patch("/product/", status_code=200)
async def update_warehouse_product(product_: ware_product_ = None, jwt_dependency: jwt_dependecy = None):
    try:
        stock_checked = 0

        def encontrar_posicion(lista, valor):
            # print(lista, valor)
            for indice, tupla in enumerate(lista):
                if tupla[0] == valor:
                    return indice + 1
            return None  # Si no se encuentra el valor
        
        def obtener_posiciones(lista_original, lista_buscada):
            posiciones = []
            for item in lista_buscada:
                for i, (clave, _) in enumerate(lista_original):
                    if clave == item:
                        posiciones.append(i + 1)
                        break
            return posiciones
        
        # trae warecodes existentes, los que no con null
        exits_ware_codes = session.query(Ware.c.code, Ware_Product.c.idWare). \
                            join(Ware_Product, and_(Ware_Product.c.idWare == Ware.c.id, Ware_Product.c.idProduct == product_.id), isouter=True). \
                            order_by(Ware.c.id.asc()). \
                            all()
        dict_exits_ware_codes = dict(exits_ware_codes)

        ##aqui valida que no desabilite ware con stock positivo
        ware_not_enabled = list(map(lambda dato: dato.wareCode, filter(lambda data: not(data.active),product_.waredata)))
        ware_not_enabled = obtener_posiciones(exits_ware_codes, ware_not_enabled) if bool(len(ware_not_enabled)) else () #devuelve una tuple de idWares que no estan habilitados

        #FALTA 🚨🚨🚨🚨 FALTA QUE NO DESABILITE CON PRODUCTOS EN TRANSITO NI GIRADOS EN DOCUMENTOS

        if bool(len(ware_not_enabled)):
            
            #obtiene stock de ware not enabled
            stock_checked = session.query(func.sum(Ware_Product.c.qtyNew)). \
                            filter(Ware_Product.c.idWare.in_(ware_not_enabled)). \
                            filter(Ware_Product.c.idProduct == product_.id).scalar()
            
            ##IMPORTANTE, CUANDO stock_checked is None, entonces es por que solo se esta creando data en almacen, pero no se esta activando
            stock_checked = stock_checked if stock_checked is not None else 0
        
        if stock_checked < 1:
            # trae idIitem apartir de itemCode
            scalarIdItem = session.query(Item.c.id).filter(Item.c.code == product_.idItem).scalar()

            # trae idLanguage apartir de languageCode
            scalarIdLanguage = session.query(Language.c.id).filter(Language.c.code == product_.idLanguage).scalar() if product_.idLanguage is not None else None

            # trae stock positivo para wareCodes con enable false

            #HORA DE ACTUALIZACION
            create_date = await Get_Time()


            stmt = update(Product).where(Product.c.id == product_.id).values(
                idItem= scalarIdItem,
                isbn=product_.isbn,
                title=product_.title,
                autor=product_.autor,
                publisher=product_.publisher,
                content=product_.content,
                dateOut=datetime.strptime(product_.dateOut, '%Y-%m-%d').date() if product_.dateOut is not None else None,
                idLanguage=scalarIdLanguage,
                pages=product_.pages,
                weight=product_.weight,
                cover=None if product_.cover is None else b'\x01' if bool(product_.cover) else b'\x00',
                width=product_.width,
                height=product_.height,
                editDate=create_date["lima_bd_format"] or None,
                large=product_.large,
                wholesale=b'\x01' if bool(product_.wholesale) else None,
                antique=b'\x01' if bool(product_.antique) else None,
                atWebProm=b'\x01' if bool(product_.atWebProm) else None,
                CardCode=product_.CardCode,
                InvntItem=product_.InvntItem,
                SellItem=product_.SellItem,
                BuyItem=product_.BuyItem,
                InvntryUom=product_.InvntryUom,
                VatBuy=product_.VatBuy,
                VatSell=product_.VatSell
            )
            
            # Ejecutar la instrucción de actualización
            result = session.execute(stmt)
            # print(f"""Filas actualizadas en tabla product {result.rowcount}""")  

            ##Actualiza los datos de los almacenes
            #emp: [('STC', None), ('SNTG', 2), ('ALYZ', None), ('WEB', None), ('FRA', None)]
            
            dict_exits_ware_code_not_none = {k: v for k, v in dict_exits_ware_codes.items() if v is not None}

            for dato in product_.waredata: #solo los wares que existen
                if(dato.wareCode in dict_exits_ware_code_not_none.keys()): #si esta dentro de la lista, es por que existe
                    stmt = update(Ware_Product).where(and_(Ware_Product.c.idWare == dict_exits_ware_code_not_none[dato.wareCode],
                                                        Ware_Product.c.idProduct == product_.id)).values(
                        pvNew = dato.pvp1 or 0.0,
                        pvOld = dato.pvp2 or 0.0,
                        loc = dato.location or None,
                        dsct = dato.dsct or 0.0,
                        qtyMinimun = dato.stockMin or 0,
                        qtyMaximum = dato.stockMax or 0,
                        isEnabled = b'\x01' if bool(dato.active) else b'\x00',
                        editDate = create_date["lima_bd_format"] or None
                    )
                    # Ejecutar la instrucción de actualización
                    result = session.execute(stmt)
                    # print(f"""Filas actualizadas en tabla ware_product {result.rowcount}""")

                elif (dato.exits and (dato.wareCode not in dict_exits_ware_code_not_none.keys())):
                    stmt = Ware_Product.insert().values(
                        {'idWare': encontrar_posicion(exits_ware_codes, dato.wareCode), #esto se tiene que revisar
                        'idProduct': product_.id,
                        'qtyNew': 0,
                        'qtyOld': 0,
                        'pvNew': dato.pvp1 or 0.0,
                        'pvOld': dato.pvp2 or 0.0, 
                        'loc': dato.location or None,
                        'dsct': dato.dsct or 0.0, 
                        'qtyMinimun': dato.stockMin or 0,
                        'isEnabled': b'\x01' if bool(dato.active) else b'\x00',
                        'creationDate': create_date["lima_bd_format"] or None,
                        'qtyMaximum': dato.stockMax or 0,
                    })
                    result = session.execute(stmt)
                    # print(f"""Filas agregadas en tabla ware_product {result.rowcount}""")
            
            # Confirmar la transacción
            session.commit()
            session.close()

            result_format = await Get_All_Inventory_and_Data_Product(idProduct=product_.id)

            # Retornar el número de filas afectadas (puedes también retornar algo más si lo necesitas)
            print(result_format)
            content = {
                "success": True,
                "message": "Producto actualizado con éxito",
                "object": result_format[0]
            }
            return JSONResponse(content=jsonable_encoder(content), status_code=200)
        else:
            content = {
                "success": False,
                "message": "No se puede desactivar almacenes, stock positvo",
                "object": None
            }
            return JSONResponse(content=content, status_code=406)
        
    except Exception as e:
        print(f"An error ocurred: {e}")
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)
    
    except SQLAlchemyError as e:
        session.rollback()
        session.close()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)

@inventory_route.post("/product/", status_code=200)
async def create_warehouse_product(product_: ware_product_ = None, jwt_dependency: jwt_dependecy = None):
    def buscar_valor(lista, clave):
        for item in lista:
            if item[0] == clave:
                return item[1]
        return None  # Si no encuentra la clave, devuelve None
    
    try:
        # trae idIitem apartir de itemCode
        scalarIdItem = session.query(Item.c.id).filter(Item.c.code == product_.idItem).scalar()

        # trae idLanguage apartir de languageCode
        scalarIdLanguage = session.query(Language.c.id).filter(Language.c.code == product_.idLanguage).scalar() if product_.idLanguage is not None else None

        # obtener la lista de wares
        wares = session.query(Ware.c.code, Ware.c.id).all()
        #[('STC', 1), ('SNTG', 2), ('ALYZ', 3), ('WEB', 4), ('FRA', 5)]

        #HORA DE REGISTRO
        create_date = await Get_Time()
        
        stmt = insert(Product).values(
            id=product_.id,
            idItem= scalarIdItem,
            isbn=product_.isbn,
            title=product_.title,
            autor=product_.autor,
            publisher=product_.publisher,
            content=product_.content,
            dateOut=datetime.strptime(product_.dateOut, '%Y-%m-%d').date() if product_.dateOut is not None else None,
            idLanguage=scalarIdLanguage,
            pages=product_.pages,
            weight=product_.weight,
            cover=None if product_.cover is None else b'\x01' if bool(product_.cover) else b'\x00',
            width=product_.width,
            height=product_.height,
            creationDate=create_date["lima_bd_format"] or None,
            large=product_.large,
            wholesale=b'\x01' if bool(product_.wholesale) else None,
            antique=b'\x01' if bool(product_.antique) else None,
            atWebProm=b'\x01' if bool(product_.atWebProm) else None,
            CardCode=product_.CardCode,
            InvntItem=product_.InvntItem,
            SellItem=product_.SellItem,
            BuyItem=product_.BuyItem,
            InvntryUom=product_.InvntryUom,
            VatBuy=product_.VatBuy,
            VatSell=product_.VatSell
        )

        result = session.execute(stmt)
    
        if result.rowcount > 0:
            #continua agregando los datos de los almacenes
            for dato in product_.waredata: #solo los wares que existen
                stmt = Ware_Product.insert().values(
                    {'idWare': buscar_valor(wares, dato.wareCode), #retornar el id del Ware cuando envio ejmp. 'SNTG'
                    'idProduct': product_.id,
                    'qtyNew': 0,
                    'qtyOld': 0,
                    'pvNew': dato.pvp1 or 0.0,
                    'pvOld': dato.pvp2 or 0.0, 
                    'loc': dato.location or None,
                    'dsct': dato.dsct or 0.0, 
                    'qtyMinimun': dato.stockMin or 0,
                    'isEnabled': b'\x01' if bool(dato.active) else b'\x00',
                    'creationDate': create_date["lima_bd_format"] or None,
                    'qtyMaximum': dato.stockMax or 0,
                })
                result = session.execute(stmt)
                if result.rowcount > 0:
                    pass
                else:
                    break

            session.commit()

            result_format = await Get_All_Inventory_and_Data_Product(idProduct=product_.id) #consulta ware product creado

            session.close() #cierra conexion si todo va bien

            content = {
                "success": True,
                "message": f"¡Producto registrado!",
                "object": result_format[0] #devuelve ware product creado
            }
            return JSONResponse(content=jsonable_encoder(content), status_code=200)
        
    
    except Exception as e:
        session.close()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)
    
    except SQLAlchemyError as e:
        session.rollback()
        session.close()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)


@inventory_route.get("/units_of_measurement/", status_code=200)
async def Get_All_Units_Of_Measurement(jwt_dependency: jwt_dependecy = None):
    returned = []
    try:
        stmt = (
            select(UOM.c.UomCode, UOM.c.UomName)
            .filter(UOM.c.IsActive == 1) #activos
        )
        Uoms = session.execute(stmt).mappings().all() #obtine en formato diccionario
        returned = Uoms
    except Exception as e:
        print(f"Get_All_Units_Of_Measurement: An error ocurred: {e}")
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        session.rollback()
    finally:
        session.close()
        return returned


