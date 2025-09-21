from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, asc, func, insert, and_, or_
from sqlmodel.ware_product import Ware_Product
from sqlmodel.product import Product
from sqlmodel.ware import Ware
from functions.prices import get_all_pricelist_format
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from datetime import date
import json

price_route = APIRouter(
    prefix = '/price',
    tags=['Prices']
)


@price_route.get("/list_and_relations/")
async def Get_PriceList_And_Relations(request_date: date = Query(..., description="Formato: YYYY-MM-DD"), jwt_dependency: jwt_dependecy = None):
    returned_value = False
    try:
        stmt = (select(Ware.c.code, Ware_Product.c.idProduct, Ware_Product.c.pvNew, Ware_Product.c.dsct).
                join(Ware, Ware_Product.c.idWare == Ware.c.id).
                order_by(Ware.c.code)
                )
        returned_value = session.execute(stmt).mappings().all()
        returned_value = get_all_pricelist_format(data=returned_value) #obtiene todos los precios del almacen, esto falta migrar a otra tabla
        
        #NO SE PUEDE GESTIONAR DELETE DESDE ESTE CASO POR QUE EL PRECIO ESTA AMARRADO AL DATO DE ALMACEN
        body = {"listas": returned_value,
                "relaciones": {
                    "almacenes": {
                        "STC": "LISTA_STC", #HARDCODEADO
                        "SNTG": "LISTA_SNTG", #HARDCODEADO
                        "ALYZ": "LISTA_ALYZ", #HARDCODEADO
                        "BIBL": "LISTA_BIBL", #HARDCODEADO
                        "FRA": "LISTA_FRA", #HARDCODEDADO
                        "WEB": "LISTA_WEB" #HARDCODEADO
                    },
                    "clientes": {}
                },
                "last_sync": request_date.strftime("%Y-%m-%d")}
        
        #guardamos en cache archivo .json
        with open("lists.json", "w", encoding='utf8') as outfile:
            json.dump(body, outfile, ensure_ascii=False, indent=4)
            returned_value = True #valida que se exporto el archivo

    except Exception as e:
        session.rollback()
        session.close()
        print(f"An error ocurred: {e}")
        returned_value = False
    finally:
        session.close()
        return returned_value


@price_route.get("/lastchanges", status_code=200)
async def Get_Last_Price_List_Changes(last_sync: date = Query(..., description="Formato: YYYY-MM-DD"), jwt_dependency: jwt_dependecy = None):
    returned_value = {}
    try:
        #trae las los ultimos cambios desde la ultima fecha
        stmt = (select(Ware.c.code, Ware_Product.c.idProduct, Ware_Product.c.pvNew, Ware_Product.c.dsct).
                join(Ware, Ware_Product.c.idWare == Ware.c.id).
                filter(or_(Ware_Product.c.creationDate >= last_sync, Ware_Product.c.editDate >= last_sync)).
                order_by(Ware.c.code)
                )

        returned_value = session.execute(stmt).mappings().all()
        returned_value = get_all_pricelist_format(data=returned_value) #obtiene todos los precios del almacen, esto falta migrar a otra tabla
        
    except Exception as e:
        session.rollback()
        session.close()
        print(f"An error ocurred: {e}")
        returned_value = {}
    finally:
        session.close()
        return returned_value