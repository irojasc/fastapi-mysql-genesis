from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text, desc, asc, or_, func, and_, null, literal, delete, insert, update
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from utils.validate_jwt import jwt_dependecy
from utils.converters import binary2bool
from config.db import aliased
from sqlmodel.product import Product
from sqlmodel.ware import Ware
from sqlmodel.language import Language
from sqlmodel.item import Item
from sqlmodel.transfer import Transfer
from sqlmodel.ware_product import Ware_Product
from sqlmodel.transfer_product import Transfer_Product
from sqlmodel.operation_reason import Operation_Reason
from sqlmodel.productlanguage import ProductLanguage
from sqlmodel.productcategories import ProductCategories
from sqlmodel.categories import Categories
from sqlmodel.uom import UOM
from sqlmodel.company import Company
from functions.catalogs import normalize_last_sync
from functions.inventory import get_all_inventory_data, get_all_active_transfer, sync_product_languages, makeSelectedCategories, sync_product_categories
from basemodel.inventory import InOut_Qty, WareProduct
from basemodel.product import ware_product_
from basemodel.ware import ware_edited
# from routes.company import Get_All_Business_Partners_By_Param
from routes.catalogs import Get_Taxes, Get_Time
from decimal import Decimal
import json
from datetime import datetime
from config.db import get_db
from sqlalchemy.orm import Session

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
# async def Get_All_Inventory_and_Data_Product(
def Get_All_Inventory_and_Data_Product(
    token_key: str = None, 
    idProduct: int = None, 
    jwt_dependency: jwt_dependecy = None,
    sessionx: Session = Depends(get_db)
    ):
    """Cuando va con la clave, retorna todo el stock con last_sync"""
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)   # 👈 o str(obj) si quieres conservar exactitud
        raise TypeError
    
    def get_statement(idProduct:int=None):
        #se desactiva| LASTPROVIDER, LANGUAGE
        stmt = (select(Ware.c.code.label("ware_code"), Item.c.code.label("item_code"), Product.c.id.label("id_product"), Product.c.isbn, Product.c.title, Product.c.autor,
            Product.c.publisher, Product.c.dateOut, literal(None).label("language"), Product.c.pages, Product.c.weight,
            Product.c.cover, Product.c.width, Product.c.height, Ware_Product.c.qtyNew, Ware_Product.c.qtyOld, 
            Ware_Product.c.qtyMinimun, Ware_Product.c.pvNew, Ware_Product.c.pvOld, Ware_Product.c.loc, 
            Ware_Product.c.isEnabled, Ware_Product.c.dsct, Ware_Product.c.idWare, Ware_Product.c.qtyMaximum, 
            Product.c.isDelete, Product.c.InvntItem, Product.c.SellItem, Product.c.BuyItem, Product.c.InvntryUom, 
            Product.c.LastPurPrc, literal(None).label("LastProvider"), Product.c.VatBuy, Product.c.VatSell). \
            join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True). \
            join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True). \
            join(Item, Product.c.idItem == Item.c.id).\
            order_by(asc(Product.c.id))
            )
        
        if idProduct is not None:
            stmt = stmt.filter(Product.c.id == idProduct)
        
        results = sessionx.execute(stmt).mappings().all() #retorna en formato diccionario
        return get_all_inventory_data(results)

    returned = False
    try:
        if bool(token_key):
            if token_key == 'CHUSPa@123':
                result_format = get_statement() #cuando va vacio, trae todos los resultados

                utc_time = Get_Time()
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
        sessionx.rollback()
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        sessionx.rollback()
    return returned

@inventory_route.get("/lastchanges", status_code=200)
# async def Get_Last_Inventory_Data_Product_Changes(
def Get_Last_Inventory_Data_Product_Changes(
    last_sync: datetime = Query(..., description="Formato esperado: YYYY-MM-DDTHH:MM:SSZ (ISO8601)"), 
    jwt_dependency: jwt_dependecy = None,
    sessionx:Session=Depends(get_db)
    ):
    returned = False
    try:
        #QUITA 10 MINUTOS PARA REALIZAR LA CONSULTA
        formated_lastsync = normalize_last_sync(last_sync) #resta 5 minutos para traer todos los cambios

        subquery_ = select(Product.c.id)\
            .join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True)\
            .join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True)\
            .join(Item, Product.c.idItem == Item.c.id)\
            .filter(
                or_(Product.c.creationDate >= formated_lastsync, 
                    Product.c.editDate >= formated_lastsync, 
                    Ware_Product.c.creationDate >= formated_lastsync, 
                    Ware_Product.c.editDate >= formated_lastsync)
                    )

        #get select subquery sqlalchemy?
        stmt = (select(Ware.c.code.label("ware_code"), Item.c.code.label("item_code"), Product.c.id.label("id_product"), Product.c.isbn, Product.c.title, Product.c.autor,
                    Product.c.publisher, Product.c.dateOut, literal(None).label("language"), Product.c.pages, Product.c.weight, 
                    Product.c.cover, Product.c.width, Product.c.height, Ware_Product.c.qtyNew, Ware_Product.c.qtyOld, 
                    Ware_Product.c.qtyMinimun, Ware_Product.c.pvNew, Ware_Product.c.pvOld, Ware_Product.c.loc, 
                    Ware_Product.c.isEnabled, Ware_Product.c.dsct, Ware_Product.c.idWare, Ware_Product.c.qtyMaximum, 
                    Product.c.isDelete, Product.c.InvntItem, Product.c.SellItem, Product.c.BuyItem, Product.c.InvntryUom, 
                    Product.c.LastPurPrc, literal(None).label("LastProvider"), Product.c.VatBuy, Product.c.VatSell). \
                    join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True). \
                    join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True). \
                    join(Item, Product.c.idItem == Item.c.id). \
                    filter(Product.c.id.in_(subquery_)).order_by(asc(Product.c.id)))
        
        results = sessionx.execute(stmt).mappings().all() #obtine en formato diccionario
        result_format = get_all_inventory_data(results)
        utc_time = Get_Time() #consulta hora actual del sistema
        # print('Consulta ware products: Hora Lima: ', utc_time["lima"])
        
        returned = {"last_sync": utc_time["lima"], "options" : result_format}
        # print(returned)
    except Exception as e:
        print(f"Get_Last_Inventory_Data_Product_Changes/nopair:get:An error ocurred: {e}")
        sessionx.rollback()
        returned = False
    except SQLAlchemyError as ex:
        sessionx.rollback()
        print("An SqlAlchemmy happened ", ex)
        returned = False
    return returned

@inventory_route.get("/warehouse_product", status_code=200)
# async def Get_WareHouse_Product_By_Id(
def Get_WareHouse_Product_By_Id(
    idProduct: str = None, 
    jwt_dependency: jwt_dependecy = None,
    sessionx: Session = Depends(get_db)
    ):
    # """Id vacio, trae formato para creacion de articulo"""
    try:
        body = {}
        waredata = {}
        #ITEM, Obtiene tipos de items
        itemList = sessionx.query(Item.c.code, Item.c.item).all()
        item_options = [{'code': idx[0], 'name': idx[1]} for idx in itemList]

        # 2. Obtener Unidades e Impuestos (Operaciones Async)
        # Podrías usar asyncio.gather para que corran en paralelo si quieres más velocidad
        list_units = Get_All_Units_Of_Measurement(sessionx=sessionx)

        list_pur_taxes = Get_Taxes(type='p', sessionx=sessionx)
        list_sel_taxes = Get_Taxes(type='s', sessionx=sessionx)

        uoms = [dict(x) for x in list_units] if isinstance(list_units, list) else []
        pur_taxes = [{'VatCode': it['VatCode'], 'VatName': it['VatName'].upper()} for it in list_pur_taxes] if isinstance(list_pur_taxes, list) else []
        sel_taxes = [{'Code': it['Code'], 'Name': it['Name']} for it in list_sel_taxes] if isinstance(list_sel_taxes, list) else []
                
        if not(idProduct): #CASO 1| CREAR NUEVO ARTICULO

            wareDataList = sessionx.query(Ware.c.code, Ware.c.isVirtual).filter(Ware.c.enabled == 1).all()
            waredata = {
                key[0]: {
                    'exits': False, 'active': False, 'location': '',
                    'stockMin': 0, 'stockMax': 0, 'pvp1': 0.0, 'pvp2': 0.0, 'dsct': 0.0,
                    'isVirtual': binary2bool(key[1])
                } for key in wareDataList
            }


            body = {
                'id': 'Pendiente',
                'item': {'itemCode': None, 'options': item_options},
                'isbn': None, 'title': None, 'autor': None, 'publisher': None,
                'release': None, 'pages': 0, 'language': [], 'category': [],
                'weight': None, 'large': None, 'width': None, 'height': None,
                'cover': None, 'summary': None, 'wholesale': False, 'antique': False,
                'webprom': False, 'CardCode': None, 'InvntItem': 'N', 'SellItem': 'N',
                'BuyItem': 'N', 'InvntryUom': 'NIU',
                'UOMS': uoms, 'Pur_Taxes': pur_taxes, 'Sel_Taxes': sel_taxes,
                'waredata': waredata, 'isDelete': False, 'formDate': '',
                'VatBuy': None, 'VatSell': None
            }

        
        else: #CASO 2| EDITAR ARTICULO EXISTENTE
            stmt = (
                select(Product, Item.c.code.label("item_code"), literal(None).label("lang_code"))
                .join(Item, Product.c.idItem == Item.c.id)
                .where(Product.c.id == int(idProduct))
            )
            product = sessionx.execute(stmt).mappings().first()

            if not product:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
             

            stmt_1_pairs_languages = (
                select(Language.c.id.label("idLang"), Language.c.code.label("codeLang"), Language.c.language.label("nameLang"))
                .join(ProductLanguage, Language.c.id == ProductLanguage.c.idLanguage)
                .filter(ProductLanguage.c.idProduct == int(idProduct))
            )

            pairs_languages = sessionx.execute(stmt_1_pairs_languages).mappings().all()

            
            stmt_2_pairs_categories = (
                        select(
                            ProductCategories.c.idCategory.label("idUltimo"),
                            ProductCategories.c.isMain,

                            Categories.c.Name.label("nameUltimo"),
                            Categories.c.Level.label("levelUltimo"),
                            Categories.c.idParent.label("parent_id"),
                        )
                        .join(Categories, Categories.c.id == ProductCategories.c.idCategory)
                        .where(ProductCategories.c.idProduct == int(idProduct))
                    )
            
            
            pairs_all_categories = sessionx.execute(
                                select(
                                    Categories.c.id,
                                    Categories.c.Name.label('name'),
                                    Categories.c.Level.label('level'),
                                    Categories.c.idParent.label('id_parent'),
                                )
                            ).mappings().all()
            
            #OBTIENE LANG CODES Y ITEMS CODES
            product = sessionx.execute(stmt).mappings().first() #obtine en formato diccionario de item codes
            #OBTIENE LANGUAGES
            # pairs_languages = sessionx.execute(stmt_1_pairs_languages).mappings().all()#obtiene pares de lenguages
            pairs_languages = [dict(row) for row in pairs_languages] #convierte formato row mapping en dict

            #OBTIENE CATEGORIES
            pairs_categories = sessionx.execute(stmt_2_pairs_categories).mappings().all()# obtiene pares de categorias para idProduct
            cat_by_id = {c["id"]: c for c in pairs_all_categories}
            pairs_categories, status = makeSelectedCategories(lines=pairs_categories, cat_by_id=cat_by_id)
            
            if not status:
                raise RuntimeError("Error obteniendo categorias de producto")
            

            # Warehouse Data con Outer Join
            ware_query = sessionx.query(Ware.c.code, Ware_Product, Ware.c.isVirtual). \
                         outerjoin(Ware_Product, (Ware.c.id == Ware_Product.c.idWare) & (Ware_Product.c.idProduct == int(idProduct))). \
                         filter(Ware.c.enabled == 1).all()
            
            waredata = {
                key[0]: {
                    'exits': key[2] is not None,
                    'active': binary2bool(key[10]) if key[10] is not None else False,
                    'location': '' if not key[7] or key[7] == 'SIN UBICACION' else key[7],
                    'stockMin': key[9] or 0,
                    'stockMax': key[13] or 0,
                    'pvp1': key[5] or 0.0,
                    'pvp2': key[6] or 0.0,
                    'dsct': key[8] or 0.0,
                    'isVirtual': binary2bool(key[14]) if key[14] is not None else None,
                } for key in ware_query
            }


            # Construcción del objeto final (más limpio que usar .update)
            body = {
                'id': str(product["id"]),
                'item': {'itemCode': product["item_code"], 'options': item_options},
                'isbn': product["isbn"], 'title': product["title"], 'autor': product["autor"],
                'publisher': product["publisher"],
                'release': str(product["dateOut"].year) if product["dateOut"] else None,
                'pages': product["pages"],
                'language': [dict(row) for row in pairs_languages],
                'category': pairs_categories,
                'weight': product["weight"], 'large': product["large"], 
                'width': product["width"], 'height': product["height"],
                'cover': binary2bool(product["cover"]) if product["cover"] is not None else None,
                'summary': product["content"] or '',
                'wholesale': binary2bool(product["wholesale"]) if product["wholesale"] is not None else False,
                'antique': binary2bool(product["antique"]) if product["antique"] is not None else False,
                'webprom': binary2bool(product["atWebProm"]) if product["atWebProm"] is not None else False,
                'CardCode': product["CardCode"],
                'InvntItem': product["InvntItem"], 'SellItem': product["SellItem"], 'BuyItem': product["BuyItem"],
                'InvntryUom': product["InvntryUom"],
                'VatBuy': product["VatBuy"] or None,
                'UOMS': uoms, 'Pur_Taxes': pur_taxes, 
                'VatSell': product["VatSell"] or None,
                'Sel_Taxes': sel_taxes,
                'waredata': waredata,
                'isDelete': binary2bool(product["isDelete"]) if product["isDelete"] is not None else False,
                'formDate': ''
            }

        return JSONResponse(content={"success": True, "message": "Todo ok!", "object": body}, status_code=200)
            
    except Exception as e:
        print(f"Get_WareHouse_Product_By_Id :get:An error ocurred: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e), "object": None}
        )
    
    except SQLAlchemyError as ex:
        print(f"Get_WareHouse_Product_By_Id :get:An error ocurred: {ex}")
        content = {
            "success": False,
            "message": f"{ex}",
            "object": None
            } 
        return JSONResponse(content=content, status_code=500)



#obtiene las trasferencias entre almacenes y los ingresos como salidas
@inventory_route.get("/transfer/checkcurrents", status_code=200)
# async def Get_Current_Transfers_By_Ware_And_Date(
def Get_Current_Transfers_By_Ware_And_Date(
    curIdWare: int = None, 
    curDate: str = None, 
    stateAbove: int = 1, 
    jwt_dependency: jwt_dependecy = None,
    sessionx:Session=Depends(get_db)
    ):
    
    returned = {
        "status": 406,
        "message": "No data available",
        "result": [],
    }
    try:
        # Create aliases for the Ware table
        fWare = aliased(Ware)
        tWare = aliased(Ware)

        results = sessionx.query(Transfer.c.codeTS,
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
        sessionx.rollback()
        print(f"Get_Open_Transfers :get:An error ocurred: {e}")
    except SQLAlchemyError as ex:
        sessionx.rollback()
        print("Get_Open_Transfers: An error ocurred", ex)
    
    return returned

@inventory_route.get("/transfer/checkbytimestamp", status_code=200)
# async def Get_Transfer_By_TimeStamp(curIdWare: int = None, 
def Get_Transfer_By_TimeStamp(curIdWare: int = None, 
                                    timeStamp: str = '', 
                                    jwt_dependency: jwt_dependecy = None,
                                    sessionx: Session=Depends(get_db)
                                    ):
    returned = {
        "status": 406,
        "message": "No data available",
        "result": [],
    }
    try:
        # Create aliases for the Ware table
        fWare = aliased(Ware)
        tWare = aliased(Ware)

        results = sessionx.query(Transfer.c.codeTS,
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
        sessionx.rollback()
        print(f"Get_Transfer_By_TimeStamp :get:An error ocurred: {e}")
    except SQLAlchemyError as ex:
        sessionx.rollback()
        print("Get_Transfer_By_TimeStamp: An error ocurred", ex)
    return returned

@inventory_route.patch("/updatequantities", status_code=200)
# async def Update_Inventory_Quantities(
def Update_Inventory_Quantities(
    invoice: InOut_Qty, 
    jwt_dependency: 
    jwt_dependecy = None,
    sessionx:Session=Depends(get_db)
    ):
    returned = False
    message = 'Ok'
    try:
        #HORA DE REGISTRO
        create_date = Get_Time()

        def UpdateQtyWareProduct(objInvoic_e = None):
            #state 1, transferencia cerrada [WARE_PRODUCT]
            id_ware = sessionx.query(Ware.c.id).filter(Ware.c.code == objInvoic_e.fromWare).first()[0]
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
            response_3 = sessionx.execute(stmt, params)
            sessionx.commit()

            return response_3.rowcount > 0


        # if(response_3.rowcount > 0 and invoice.operacion != 'inventario'): #REGISTRA EN LA TABLA TRANSFER
        if(invoice.operacion != 'inventario'): #REGISTRA EN LA TABLA TRANSFER

            id_operation_reason = sessionx.query(Operation_Reason.c.idOperReas).filter(Operation_Reason.c.operation == invoice.operacion).filter(Operation_Reason.c.reason == invoice.operacion_motivo).subquery()
            id_fromWare = sessionx.query(Ware.c.id).filter(Ware.c.code == invoice.fromWare).subquery()
            id_toWare = sessionx.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).subquery()
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
            response_1 = sessionx.execute(stmt1)
            sessionx.commit()

            if(response_1.rowcount > 0 and invoice.operacion != 'inventario'): #REGISTRA EN LA TABLA TRANSFER PRODUCTO DETALLE
                stmt2 = Transfer_Product.insert()
                products_to_insert = list(map(lambda x: {'idTransfer': invoice.codeTS, 'idProduct': int(x.code.split('_')[1]), 'qtyNew': x.qtyNew, 'qtyOld': x.qtyOld}, invoice.list_main))
                response_2 = sessionx.execute(stmt2, products_to_insert)
                sessionx.commit()
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
        returned = False
        message = f"Exception: {e}"
    except SQLAlchemyError as ex:
        returned = False
        sessionx.rollback()
        message = f"Sql Exception: {ex}"
    return {
        "state":  returned,
        "message": message
    }

@inventory_route.patch("/product/changelocation", status_code=200)
# async def change_product_location(
def change_product_location(
    invoice: WareProduct = None, 
    jwt_dependency: jwt_dependecy = None,
    sessionx:Session=Depends(get_db)
    ):
    # response model
    response = {
        "state": False,
        "result": [],
        "message": ""
    }
    try:
        #HORA DE REGISTRO
        create_date = Get_Time()

        idWare = select(Ware.c.id).where(Ware.c.code == invoice.wareCode).limit(1).subquery()
        sessionx.execute(update(Ware_Product)
                        .where(Ware_Product.c.idProduct == invoice.idProduct, Ware_Product.c.idWare == idWare.as_scalar())
                        .values(loc = invoice.loc, editDate = create_date["lima_bd_format"] or None)
                        # .values(loc = invoice.loc, editDate = invoice.editDate)
                        )
        sessionx.commit()
        response["state"] = True
        response["message"] = 'Cambios aplicados'

    except Exception as e:
        sessionx.rollback()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"

    except SQLAlchemyError as e:
        sessionx.rollback()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"
        
    return response

@inventory_route.post("/inventorymode", status_code=200)
# async def run_inventory_mode(
def run_inventory_mode(
    input_param: ware_edited = None, 
    jwt_dependency: jwt_dependecy = None,
    sessionx:Session=Depends(get_db)
    ): 
    # response model
    response = {
        "state": False,
        "result": [],
        "message": ""
    }
    try:
        
        #HORA DE REGISTRO
        create_date = Get_Time()

        result_1 = sessionx.execute(update(Ware_Product)
                                   .where(and_(Ware_Product.c.idWare == input_param.wareCode,
                                               or_(Ware_Product.c.qtyNew != 0,
                                                   Ware_Product.c.qtyOld != 0)
                                                   )
                                   )
                                   .values(qtyNew=0, qtyOld=0)
                                    )   
        sessionx.commit()
        if(result_1.rowcount >= 0):
            result_2 = sessionx.execute(update(Ware)
                                        .where(and_(Ware.c.id == input_param.wareCode,
                                                   or_(Ware.c.inv_date != create_date["lima_transfer_format"],
                                                       Ware.c.inv_date == None)))
                                        .values(inv_date = create_date["lima_transfer_format"])
                                        )
            
            result_3 = sessionx.execute(update(Ware)
                                       .where(and_(Ware.c.id == input_param.wareCode, Ware.c.inv_clean == 1))
                                       .values(inv_clean = b'\x00')
                                     )
            sessionx.commit()
            if(result_2.rowcount >= 0 and result_3.rowcount >= 0):
                response["state"] = True
                response["message"] = f"Afectadas ware_product: {result_1.rowcount}, Ware: {result_2.rowcount}, invt_clean: {result_3.rowcount}"

    except Exception as e:
        sessionx.rollback()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"

    except SQLAlchemyError as e:
        sessionx.rollback()
        response["state"] = False
        response["message"] = f"An error ocurred: {e}"
        
    return response

@inventory_route.patch("/transfer/downgradestate", status_code=200)
# async def downgrade_transfer_state(invoice: InOut_Qty = False, 
def downgrade_transfer_state(invoice: InOut_Qty = False, 
                                   jwt_dependency: jwt_dependecy = None, 
                                   sessiono: Session = Depends(get_db)
                                   ):
    # response model
    response = {
        "state": False,
        "result": [],
        "message": "",
        "toDate": None,
        "doDelete": False,
        "level": None,
        "toUser": None
    }

    try:
        #HORA DE REGISTRO
        create_date = Get_Time()
        lima_ts = create_date["lima_transfer_format"]

        #primero verifica que nadie lo haya tomado

        transfer_data = sessiono.query(Transfer.c.state, Transfer.c.toUser).filter(Transfer.c.codeTS == invoice.codeTS).first()

        if not transfer_data:
            response["message"] = "Transferencia no encontrada"
            response["doDelete"] = True
            return response
            #aqui devolver datos  ✅
        
        state_db, user_db = transfer_data

        fecha_front = "-".join(lima_ts.split("-")[::-1])
        
        if state_db == 1: #si el estado ya llego a 1, no se puede realizar ningun cambio
            response["message"] = "¡El traslado se encuentra cerrado!"
            response["toUser"] = user_db
            response["level"] = state_db
            response["toDate"] = fecha_front

            return response
            #aqui devolver datos  ✅
        
        # Lógica de estados
        is_final = invoice.isFinalState
            
        
        #si no es final state
        # Caso A: No es estado final y nadie lo ha tomado
        if not is_final and user_db is None:
            #solamente baja en uno el state
            sessiono.execute(update(Transfer).
                            where(Transfer.c.codeTS == invoice.codeTS).
                            values(state = Transfer.c.state - 1, 
                                   toUser= invoice.curUser))
            sessiono.commit()
            response.update({"state": True, "message": f'Traslado atendido con codigo {invoice.codeTS}', "result": False}) # result False indica que bajo a nivel 2
        
        # Caso B: Ya está tomado por otro usuario (aplica para final y no final)
        elif user_db != invoice.curUser and (is_final or user_db is not None):
            response.update({
                "state": True, 
                "message": 
                "¡El traslado está siendo atendido por otro usuario!", 
                "result": None,
                "toUser" : user_db,
                "level": state_db
                })
            #aqui devolver datos ✅
        
        # Caso C: De que si sea el usuario pero ya esta en otro nivel
        elif user_db == invoice.curUser and invoice.level != state_db:
            response.update({
                "state": True, 
                "message": 
                "¡El traslado se encuentra en otro estado de atención!", 
                "result": None,
                "toUser" : user_db,
                "level": state_db
                })
            #aqui devolver datos ✅

        
        elif is_final and user_db == invoice.curUser:
            #baja en uno el state y actuliza las cantidades en ware_product
            sessiono.execute(
                            update(Transfer)
                            .where(Transfer.c.codeTS == invoice.codeTS)
                            .values(state = Transfer.c.state - 1, toDate = lima_ts)
                            )
            
            # sessiono.commit()
            #id de toWare suqquery
            # id_toWare = sessiono.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).first()[0]
            id_toWare = sessiono.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).scalar()

            #actualiza las cantidades en ware_product
            items_quantity = sessiono.query(
                                Transfer_Product.c.idProduct, 
                                Transfer_Product.c.qtyNew, 
                                Transfer_Product.c.qtyOld
                                ).filter(Transfer_Product.c.idTransfer == invoice.codeTS).all()

            params = list(map(lambda item: {
                'qtyN': item.qtyNew,
                'qtyO': item.qtyOld,
                'editDa': create_date["lima_bd_format"] or None,
                'idPro' : int(item.idProduct),
                'idWa' : id_toWare
                }, items_quantity))
            

            stmt = text("""
                        UPDATE ware_product 
                        SET qtyNew = qtyNew + :qtyN, 
                            qtyOld = qtyOld + :qtyO, 
                            editDate = :editDa 
                        WHERE idProduct = :idPro AND idWare = :idWa
                        """)


            response_3 = sessiono.execute(stmt, params)
            sessiono.commit()


            if(response_3.rowcount > 0):

                response.update({
                    "state": True,
                    "message": f'Se agregaron items con codigo {invoice.codeTS}',
                    "result": True,
                    "toDate": fecha_front
                })

    except Exception as e:
        sessiono.rollback()
        response["state"] = False
        response["message"] = f"An error ocurred: {str(e)}"

    return response
    


@inventory_route.patch("/product/", status_code=200)
# async def update_warehouse_product(
def update_warehouse_product(
                                    product_: ware_product_ = None, 
                                    jwt_dependency: jwt_dependecy = None,
                                    sessionx:Session=Depends(get_db)
                                   ):
    try:
        try:
            idProduct = int(product_.id)
        
        except (TypeError, ValueError):
            idProduct = None
            

        stock_checked = 0

        def encontrar_posicion(lista, valor):
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
        exits_ware_codes = sessionx.query(Ware.c.code, Ware_Product.c.idWare). \
                            join(Ware_Product, and_(Ware_Product.c.idWare == Ware.c.id, Ware_Product.c.idProduct == idProduct), isouter=True). \
                            order_by(Ware.c.id.asc()). \
                            all()
        dict_exits_ware_codes = dict(exits_ware_codes)
        

        ##aqui valida que no desabilite ware con stock positivo
        ware_not_enabled = list(map(lambda dato: dato.wareCode, filter(lambda data: not(data.active),product_.waredata)))
        ware_not_enabled = obtener_posiciones(exits_ware_codes, ware_not_enabled) if bool(len(ware_not_enabled)) else () #devuelve una tuple de idWares que no estan habilitados

        #FALTA 🚨🚨🚨🚨 FALTA QUE NO DESABILITE CON PRODUCTOS EN TRANSITO NI GIRADOS EN DOCUMENTOS
        

        if bool(len(ware_not_enabled)):
            
            #obtiene stock de ware not enabled
            stock_checked = sessionx.query(func.sum(Ware_Product.c.qtyNew)). \
                            filter(Ware_Product.c.idWare.in_(ware_not_enabled)). \
                            filter(Ware_Product.c.idProduct == idProduct).scalar()
            
            ##IMPORTANTE, CUANDO stock_checked is None, entonces es por que solo se esta creando data en almacen, pero no se esta activando
            stock_checked = stock_checked if stock_checked is not None else 0
        
        if stock_checked < 1:
            # trae idIitem apartir de itemCode
            scalarIdItem = sessionx.query(Item.c.id).filter(Item.c.code == product_.idItem).scalar()

            # trae stock positivo para wareCodes con enable false

            #HORA DE ACTUALIZACION
            create_date = Get_Time()

            stmt = (update(Product)
                    .where(Product.c.id == idProduct)
                    .values(
                            idItem= scalarIdItem,
                            isbn=product_.isbn,
                            title=product_.title,
                            autor=product_.autor,
                            publisher=product_.publisher,
                            content=product_.content,
                            dateOut=datetime.strptime(product_.dateOut, '%Y-%m-%d').date() if product_.dateOut is not None else None,
                            idLanguage=None, #se mantiene para no romper estructura frond UI
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
                    )
            
            # Ejecutar la instrucción de actualización
            result = sessionx.execute(stmt)

            ##Actualiza los datos de los almacenes
            #emp: [('STC', None), ('SNTG', 2), ('ALYZ', None), ('WEB', None), ('FRA', None)]
            
            dict_exits_ware_code_not_none = {k: v for k, v in dict_exits_ware_codes.items() if v is not None}
            

            for dato in product_.waredata: #solo los wares que existen
                if(dato.wareCode in dict_exits_ware_code_not_none.keys()): #si esta dentro de la lista, es por que existe
                    stmt = (update(Ware_Product)
                            .where(and_(
                                        Ware_Product.c.idWare == dict_exits_ware_code_not_none[dato.wareCode],
                                        Ware_Product.c.idProduct == idProduct))
                            .values(
                            pvNew = dato.pvp1 or 0.0,
                            pvOld = dato.pvp2 or 0.0,
                            loc = dato.location or None,
                            dsct = dato.dsct or 0.0,
                            qtyMinimun = dato.stockMin or 0,
                            qtyMaximum = dato.stockMax or 0,
                            isEnabled = b'\x01' if bool(dato.active) else b'\x00',
                            editDate = create_date["lima_bd_format"] or None
                            )
                            )
                    # Ejecutar la instrucción de actualización
                    result = sessionx.execute(stmt)
                    # print(f"""Filas actualizadas en tabla ware_product {result.rowcount}""")

                elif (dato.exits and (dato.wareCode not in dict_exits_ware_code_not_none.keys())):
                    stmt = Ware_Product.insert().values(
                        {'idWare': encontrar_posicion(exits_ware_codes, dato.wareCode), #esto se tiene que revisar
                        'idProduct': idProduct,
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
                    result = sessionx.execute(stmt)
            
            #PROCESO DE ACTUALIZACION DE IDIOMAS
            status, msg = sync_product_languages(sessionx=sessionx, product_id=idProduct, langs=product_.idLanguage, ProductLanguage=ProductLanguage)
            if not status:
                raise RuntimeError(f"No se realizo el commit durante actualizacion de idiomas, revisar {msg}")
            
            #PROCESO DE ACTUALIZACION DE CATEGORIAS
            status, msg = sync_product_categories(sessionx=sessionx, product_id=idProduct, desired=product_.idCategory, ProductCategories=ProductCategories)
            if not status:
                raise RuntimeError(f"No se realizo el commit durante actualizacion de categorias, revisar {msg}")
                
            # Confirmar la transacción
            sessionx.commit()

            result_format = Get_All_Inventory_and_Data_Product(idProduct=idProduct, sessionx=sessionx)

            # Retornar el número de filas afectadas (puedes también retornar algo más si lo necesitas)
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
        sessionx.rollback()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)
    
    except SQLAlchemyError as e:
        sessionx.rollback()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)

@inventory_route.post("/product/", status_code=200)
# async def create_warehouse_product(
def create_warehouse_product(
    product_: ware_product_ = None, 
    jwt_dependency: jwt_dependecy = None,
    sessionx: Session = Depends(get_db)
    ):
    
    def buscar_valor(lista, clave):
        for item in lista:
            if item[0] == clave:
                return item[1]
        return None  # Si no encuentra la clave, devuelve None
    
    try:
        
        #OBTIENE ID CONSECUTIVO
        last_id = sessionx.execute(
                    select(Product.c.id)
                    .order_by(Product.c.id.desc())
                    .limit(1)
                    .with_for_update() #congela la fila para evitar colision con otros registros
                    ).scalar_one_or_none()
        idProduct = (last_id or 0) + 1

        # trae idIitem apartir de itemCode
        scalarIdItem = sessionx.query(Item.c.id).filter(Item.c.code == product_.idItem).scalar()

        # obtener la lista de wares
        wares = sessionx.query(Ware.c.code, Ware.c.id).all()
        #[('STC', 1), ('SNTG', 2), ('ALYZ', 3), ('WEB', 4), ('FRA', 5)]

        #HORA DE REGISTRO
        create_date = Get_Time()


        stmt = insert(Product).values(
            id=idProduct,
            idItem= scalarIdItem,
            isbn=product_.isbn,
            title=product_.title,
            autor=product_.autor,
            publisher=product_.publisher,
            content=product_.content,
            dateOut=datetime.strptime(product_.dateOut, '%Y-%m-%d').date() if product_.dateOut is not None else None,
            idLanguage=None, #se mantiene para no romper estructura frond UI
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

        result = sessionx.execute(stmt)
    
        if result.rowcount > 0:
            #Aqui evalua el tema de los languages
            if isinstance(product_.idLanguage, list) and product_.idLanguage:
                rows = [
                    {
                        "idProduct": idProduct,
                        "idLanguage": lang["idLang"]
                    }
                    for lang in product_.idLanguage
                    if "idLang" in lang
                ]
                result = sessionx.execute(insert(ProductLanguage).values(rows))
                if result.rowcount == 0: #no afecta ninguna fila o es failed
                    sessionx.rollback()
                    raise RuntimeError("Error cargando lenguajes de producto | antes de ware dialog")
                

            #Aqui evalua el tema de las categorias
            if isinstance(product_.idCategory, list) and product_.idCategory:
                rows = [
                    {
                        "idProduct": idProduct,
                        "idCategory": cate["idCategory"],
                        "isMain": cate["isMain"]
                    }
                    for cate in product_.idCategory
                    if "idCategory" in cate
                ]
                result = sessionx.execute(insert(ProductCategories).values(rows))
                if result.rowcount == 0: #no afecta ninguna fila o es failed
                    sessionx.rollback()
                    raise RuntimeError("Error cargando categorias de producto | antes de ware_dialog")


            #continua agregando los datos de los almacenes
            for dato in product_.waredata: #solo los wares que existen
                stmt = Ware_Product.insert().values(
                    {'idWare': buscar_valor(wares, dato.wareCode), #retornar el id del Ware cuando envio ejmp. 'SNTG'
                    'idProduct': idProduct,
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
                result = sessionx.execute(stmt)
                if result.rowcount > 0:
                    pass
                else:
                    break

            sessionx.commit()

            result_format = Get_All_Inventory_and_Data_Product(idProduct=idProduct, sessionx=sessionx) #consulta ware product creado

            content = {
                "success": True,
                "message": f"¡Producto registrado!",
                "object": result_format[0] #devuelve ware product creado
            }

            return JSONResponse(content=jsonable_encoder(content), status_code=200)
        
    
    except IntegrityError:
        sessionx.rollback()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)
    
    except Exception as e:
        sessionx.rollback()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)
    
    except SQLAlchemyError as e:
        sessionx.rollback()
        content = {
            "success": False,
            "message": f"An error ocurred: {e}",
            "object": None
        }
        return JSONResponse(content=content, status_code=500)


@inventory_route.get("/units_of_measurement/", status_code=200)
# async def Get_All_Units_Of_Measurement(
def Get_All_Units_Of_Measurement(
    jwt_dependency: jwt_dependecy = None,
    sessionx: Session = Depends(get_db)
    ):
    try:
        stmt = (
            select(UOM.c.UomCode, UOM.c.UomName)
            .filter(UOM.c.IsActive == 1) #activos
        )
        Uoms = sessionx.execute(stmt).mappings().all() #obtine en formato diccionario
        return list(Uoms)

    except Exception as e:
        print(f"Get_All_Units_Of_Measurement: An error ocurred: {e}")
        return []
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        return []