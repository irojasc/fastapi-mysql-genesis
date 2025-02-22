import json
import gspread
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text, func
from typing import Optional
from utils.validate_jwt import jwt_dependecy
from config.db import con, session, CREDENTIALS_JSON
from sqlmodel.product import Product
from sqlmodel.ware_product import Ware_Product
from sqlmodel.user_perm_mdl import User_perm_mdl
from functions.product import get_all_publishers
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
from gspread.exceptions import GSpreadException
from basemodel.product import product_maintenance
from sqlalchemy.exc import SQLAlchemyError

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
                query = f"wp.idProduct as idProduct, pr.isbn, pr.title, pr.autor, pr.publisher, wr.code, wp.pvNew, wp.isEnabled as enabled, wp.qtyNew as stock from genesisDB.ware_product wp inner join genesisDB.product pr on wp.idProduct = pr.id inner join genesisDB.ware wr on wp.idWare = wr.id where {get_isbn_isExists(Isbn)} pr.title like '%{Title.upper()}%' and pr.autor like '%{Autor.upper()}%' and pr.publisher like '%{Publisher.upper()}%' group by wp.idProduct , pr.isbn, pr.title, pr.publisher, wr.code, wp.pvNew, wp.isEnabled, wp.qtyNew order by wp.idProduct asc"
                # stock = con.execute(select(text(query)))
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
                            "isEnabled": item[7] != b'\x00',
                            "stock": int(item[8]),
                            "pv": {item[5]: item[6]}
                        })
                    else:
                        result[_index]["isEnabled"] = result[_index]["isEnabled"] or (item[7] != b'\x00')
                        result[_index]["stock"] = result[_index]["stock"] + int(item[8])
                        result[_index]["pv"][item[5]] = item[6]
        
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
            
@product_route.get("/publisher", status_code=200)
async def Get_All_Publishers(jwt_dependency: jwt_dependecy):
    returned = []
    try:
        results = session.query(Product.c.publisher).distinct().all()
        returned = list(map(get_all_publishers,enumerate(results)))
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"An error ocurred: {e}")
        returned = []
    finally:
        session.close()
        return returned

@product_route.get("/price", status_code=200)
async def get_price_by_ware_house(
                                    idWare: Optional[int] = 1,
                                    isbn: Optional[str] = "",
                                ):
    status = False
    result = (None, None)
    try:
        if bool(idWare) or bool(isbn):
            query = f"p.title, p.autor, p.publisher, wp.pvNew from ware_product wp inner join genesisDB.product p on p.id = wp.idProduct where isbn like '%{isbn}%' and idWare={str(idWare)} and isEnabled = True;"
            productPrice = session.execute(select(text(query)))
            data = productPrice.fetchall()
            (title, autor, publisher, pvNew) = ((data[0][0], data[0][1], data[0][2], data[0][3]) if ((data is not None) and (len(data) == 1)) else (None, None, None, None))
            if not title:
                status = False
            else:
                status = True
                result = {"productDetail": f"{title.replace('Ñ','N').replace('¡', '!')} - {autor.replace('Ñ','N').replace('¡', '!')} - {publisher.replace('ñ','n').replace('¡', '!')}",
                          "productPrice": f"{str(pvNew)}"}
        else:
            raise HTTPException(status_code=404, detail='Nothing to show you')
    except:
        session.rollback()
        # raise
    finally:
        session.close()
        if not status:
            raise HTTPException(status_code=404, detail='Nothing to show you')
        elif status:
            return JSONResponse(
            status_code=200,
            content= result
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
