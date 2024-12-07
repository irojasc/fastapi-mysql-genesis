from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text, desc, asc, or_
from sqlalchemy.exc import SQLAlchemyError
from utils.validate_jwt import jwt_dependecy
from config.db import con, session, aliased
from sqlmodel.product import Product
from sqlmodel.ware import Ware
from sqlmodel.language import Language
from sqlmodel.item import Item
from sqlmodel.transfer import Transfer
from sqlmodel.ware_product import Ware_Product
from sqlmodel.transfer_product import Transfer_Product
from sqlmodel.operation_reason import Operation_Reason
from sqlmodel.company import Company
from sqlmodel.ware import Ware
# from functions.product import get_all_publishers
from functions.inventory import get_all_inventory_data, get_all_active_transfer
from sqlalchemy import insert, delete, update
from basemodel.inventory import InOut_Qty, WareProduct
import json
from datetime import datetime

inventory_route = APIRouter(
    prefix = '/inventory',
    tags=['Inventory']
)

#aqui falta agregar la parte donde solo algunos pueden ejecutar este comando
@inventory_route.get("/", status_code=200)
# async def Get_All_Inventory_and_Data_Product(token_key: str, jwt_dependency: jwt_dependecy):
async def Get_All_Inventory_and_Data_Product(token_key: str, jwt_dependency: jwt_dependecy):
    returned = False
    try:
        if token_key == 'CHUSPa@123':
            results = session.query(Ware.c.code, Item.c.code, Product.c.id,Product.c.isbn, Product.c.title, Product.c.autor, 
                                    Product.c.publisher, Product.c.dateOut, Language.c.language, Product.c.pages, Product.c.edition, Product.c.cover,
                                    Product.c.width, Product.c.height,
                                    Ware_Product.c.qtyNew, Ware_Product.c.qtyOld, Ware_Product.c.qtyMinimun, Ware_Product.c.pvNew, Ware_Product.c.pvOld,
                                    Ware_Product.c.loc, Ware_Product.c.isEnabled, Ware_Product.c.dsct, Ware_Product.c.idWare).join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True).join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True).join(Language, Product.c.idLanguage == Language.
            c.id, isouter=True).join(Item, Product.c.idItem == Item.c.id).order_by(asc(Product.c.id)).all()
            result_format = get_all_inventory_data(results)
            json_object = json.dumps(result_format, indent=4, default=repr).encode('utf8')
            with open("sample.json", "w", encoding='utf8') as outfile:
                json_object = json.dumps(result_format, ensure_ascii=False).encode('utf8')
                outfile.write(str(json_object, 'utf-8'))
            returned = True
    except Exception as e:
        print(f"Get_All_Inventory_and_Data_Product/nopair:get:An error ocurred: {e}")
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        session.rollback()
    finally:
        session.close()
        return returned

@inventory_route.get("/lastchanges", status_code=200)
async def Get_Last_Inventory_Data_Product_Changes(inputDate: str = '2024-01-01', jwt_dependency: jwt_dependecy = None):
    returned = False
    try:
        innerDate = datetime.strptime(inputDate, "%Y-%m-%d")

        # subquery_ = session.query(Product.c.id).join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True).join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True).join(Language, Product.c.idLanguage == Language.c.id, isouter=True).join(Item, Product.c.idItem == Item.c.id).filter(or_(Product.c.creationDate >= inputDate, Product.c.editDate >= inputDate, Ware_Product.c.creationDate >= inputDate, Ware_Product.c.editDate >= inputDate)).subquery()
        subquery_ = select(Product.c.id).join(Ware_Product, Product.c.id == Ware_Product.c.idProduct, isouter=True).join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True).join(Language, Product.c.idLanguage == Language.c.id, isouter=True).join(Item, Product.c.idItem == Item.c.id).filter(or_(Product.c.creationDate >= inputDate, Product.c.editDate >= inputDate, Ware_Product.c.creationDate >= inputDate, Ware_Product.c.editDate >= inputDate))
        #get select subquery sqlalchemy?
        results = session.query(Ware.c.code, Item.c.code, Product.c.id,Product.c.isbn, Product.c.title, Product.c.autor, 
                                Product.c.publisher, Product.c.dateOut, Language.c.language, Product.c.pages, Product.c.edition, 
                                Product.c.cover, Product.c.width, Product.c.height, Ware_Product.c.qtyNew, Ware_Product.c.qtyOld, 
                                Ware_Product.c.qtyMinimun, Ware_Product.c.pvNew, Ware_Product.c.pvOld, Ware_Product.c.loc, 
                                Ware_Product.c.isEnabled, Ware_Product.c.dsct, Ware_Product.c.idWare).join(Ware_Product, 
                                                                                                           Product.c.id == Ware_Product.c.idProduct, isouter=True).join(Ware, Ware_Product.c.idWare == Ware.c.id, isouter=True).join(Language, Product.c.idLanguage == Language.c.id, isouter=True).join(Item, Product.c.idItem == Item.c.id).filter(Product.c.id.in_(subquery_)).order_by(asc(Product.c.id)).all()
        result_format = get_all_inventory_data(results)
        returned = result_format
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

@inventory_route.get("/transfers_by_ware", status_code=200)
async def Get_Transfers_By_Ware(curIdWare: int = None, curDate: str = None, stateAbove: int = 1, jwt_dependency: jwt_dependecy = None):
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
                                    or_(Transfer.c.fromWareId == curIdWare, Transfer.c.toWareId == curIdWare)).all()
                                
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


@inventory_route.patch("/updatequantities", status_code=200)
async def Update_Inventory_Quantities(invoice: InOut_Qty, jwt_dependency: jwt_dependecy = None):
    returned = False
    message = 'Ok'
    try:
        #state 1, transferencia cerrada
        id_operation_reason = session.query(Operation_Reason.c.idOperReas).filter(Operation_Reason.c.operation == invoice.operacion).filter(Operation_Reason.c.reason == invoice.operacion_motivo).subquery()
        id_fromWare = session.query(Ware.c.id).filter(Ware.c.code == invoice.fromWare).subquery()
        id_toWare = session.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).subquery()
        id_ware = session.query(Ware.c.id).filter(Ware.c.code == invoice.fromWare).first()[0]
        params = list(map(lambda x: {'qtyN': (x.qtyNew if invoice.operacion == 'ingreso' else -abs(x.qtyNew)),
                                        'qtyO': (x.qtyOld if invoice.operacion == 'ingreso' else -abs(x.qtyOld)),
                                        'editDa': invoice.fromDate,
                                        'location': invoice.ubicacion if bool(invoice.ubicacion) else None,
                                        'idPro' : int(x.code.split('_')[1]),
                                        'idWa' : id_ware}, invoice.list_main))
        if bool(invoice.ubicacion):
            stmt = text(f"UPDATE ware_product set qtyNew = qtyNew + :qtyN, qtyOld = qtyOld + :qtyO, editDate = :editDa, loc = :location where idProduct = :idPro and idWare = :idWa")
        else:
            stmt = text(f"UPDATE ware_product set qtyNew = qtyNew + :qtyN, qtyOld = qtyOld + :qtyO, editDate = :editDa where idProduct = :idPro and idWare = :idWa")
        response_3 = session.execute(stmt, params)
        session.commit()
        if(response_3.rowcount > 0):
            stmt1 = (
                insert(Transfer).
                values(
                    codeTS = invoice.codeTS,
                    fromWareId= id_fromWare.as_scalar(),
                    toWareId= id_toWare.as_scalar(),
                    fromUser=invoice.curUser,
                    fromDate= invoice.fromDate,
                    toDate= invoice.toDate,
                    state= invoice.state,
                    note= invoice.comentario,
                    cardCode= invoice.socio_docNum,
                    idOperReas=id_operation_reason.as_scalar(),
                    )
                )
            response_1 = session.execute(stmt1)
            session.commit()
            if(response_1.rowcount > 0):
                stmt2 = Transfer_Product.insert()
                products_to_insert = list(map(lambda x: {'idTransfer': invoice.codeTS, 'idProduct': int(x.code.split('_')[1]), 'qtyNew': x.qtyNew, 'qtyOld': x.qtyOld}, invoice.list_main))
                response_2 = session.execute(stmt2, products_to_insert)
                session.commit()
                if(response_2.rowcount > 0):
                    returned = True
            else:
                returned = False
    except Exception as e:
        print(f"Update_Inventory_Quantities/nopair:patch:An error ocurred: {e}")
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
        idWare = select(Ware.c.id).where(Ware.c.code == invoice.wareCode).limit(1).subquery()
        session.execute(update(Ware_Product).where(Ware_Product.c.idProduct == invoice.idProduct, Ware_Product.c.idWare == idWare.as_scalar()).values(loc = invoice.loc, editDate = invoice.editDate))
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

@inventory_route.patch("/transfer/downgradestate", status_code=200)
# async def downgrade_transfer_state(codeTS: str = None, userName: str = None, toIdWare: int = None, isFinalStep: bool = False, jwt_dependency: jwt_dependecy = None):
async def downgrade_transfer_state(invoice: InOut_Qty = False, jwt_dependency: jwt_dependecy = None):
    # response model
    response = {
        "state": False,
        "result": [],
        "message": ""
    }
    try:
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
            #baja en uno el state y actuliza las cantidades en ware_product
            session.execute(update(Transfer).
                            where(Transfer.c.codeTS == invoice.codeTS).
                            values(state = Transfer.c.state - 1,
                                   toDate= invoice.toDate))
            session.commit()
            #actualiza las cantidades en ware_product
            items_quantity = session.query(Transfer_Product.c.idProduct, Transfer_Product.c.qtyNew, Transfer_Product.c.qtyOld). \
            filter(Transfer_Product.c.idTransfer == invoice.codeTS).all()
            #id de toWare suqquery
            id_toWare = session.query(Ware.c.id).filter(Ware.c.code == invoice.toWare).first()[0]

            params = list(map(lambda x: {
                'qtyN': x[1],
                'qtyO': x[2],
                'editDa': invoice.toDate,
                'idPro' : int(x[0]),
                'idWa' : id_toWare}, items_quantity))
            
            stmt = text(f"UPDATE ware_product set qtyNew = qtyNew + :qtyN, qtyOld = qtyOld + :qtyO, editDate = :editDa where idProduct = :idPro and idWare = :idWa")
            response_3 = session.execute(stmt, params)
            session.commit()
            if(response_3.rowcount > 0):
                print("Si ingresa aqui")
                response["state"] = True
                response["message"] = f'Se agregaron items con codigo {invoice.codeTS}'
                response["result"] = True

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