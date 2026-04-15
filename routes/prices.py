from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, asc, func, insert, and_, or_
from sqlmodel.ware_product import Ware_Product
from sqlmodel.product import Product
from sqlmodel.ware import Ware
from functions.prices import get_all_pricelist_format
from functions.catalogs import normalize_last_sync
from routes.catalogs import Get_Time, Get_Taxes
from utils.validate_jwt import jwt_dependecy
from config.db import get_db
from datetime import date, datetime
from sqlalchemy.orm import Session
import json

price_route = APIRouter(
    prefix = '/price',
    tags=['Prices']
)


@price_route.get("/list_and_relations/")
# async def Get_PriceList_And_Relations(jwt_dependency: jwt_dependecy = None,
def Get_PriceList_And_Relations(jwt_dependency: jwt_dependecy = None,
                                      sessionx:Session=Depends(get_db)
                                      ):
    returned_value = False
    try:
        #HORA CONSULTA
        utc_time = Get_Time()

        stmt = (select(Ware.c.code, Ware_Product.c.idProduct, Ware_Product.c.pvNew, Ware_Product.c.dsct).
                join(Ware, Ware_Product.c.idWare == Ware.c.id).
                order_by(Ware.c.code)
                )
        returned_value = sessionx.execute(stmt).mappings().all()
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
                "last_sync": utc_time["lima"]
                }
        
        #guardamos en cache archivo .json
        with open("lists.json", "w", encoding='utf8') as outfile:
            # json.dump(body, outfile, ensure_ascii=False, indent=4)
            json.dump(body, outfile, ensure_ascii=False)
            returned_value = True #valida que se exporto el archivo

    except Exception as e:
        sessionx.rollback()
        print(f"An error ocurred: {e}")
        returned_value = False

    return returned_value


@price_route.get("/lastchanges", status_code=200)
# async def Get_Last_Price_List_Changes(last_sync: datetime = Query(..., description="Formato esperado: YYYY-MM-DDTHH:MM:SSZ (ISO8601)"), 
def Get_Last_Price_List_Changes(last_sync: datetime = Query(..., description="Formato esperado: YYYY-MM-DDTHH:MM:SSZ (ISO8601)"), 
                                      jwt_dependency: jwt_dependecy = None,
                                      sessionx:Session=Depends(get_db)
                                      ):
    returned_value = {}
    try:
        #QUITA 5 MINUTOS PARA REALIZAR LA CONSULTA
        formated_lastsync = normalize_last_sync(last_sync) #resta 5 minutos para traer todos los cambios

        #trae las los ultimos cambios desde la ultima fecha
        stmt = (
                select(Ware.c.code, Ware_Product.c.idProduct, Ware_Product.c.pvNew, Ware_Product.c.dsct)
                .join(Ware, Ware_Product.c.idWare == Ware.c.id)
                .filter(or_(Ware_Product.c.creationDate >= formated_lastsync, Ware_Product.c.editDate >= formated_lastsync))
                .order_by(Ware.c.code)
                )

        returned_value = sessionx.execute(stmt).mappings().all()
        returned_value = get_all_pricelist_format(data=returned_value) #obtiene todos los precios del almacen, esto falta migrar a otra tabla
        #HORA CONSULTA
        utc_time = Get_Time()

        #CONSULTA DATOS IMPUESTOS
        sell_taxes = Get_Taxes(type='s', sessionx=sessionx)


        if isinstance(returned_value, dict):
            returned_value.update({"last_sync": utc_time["lima"]})

            returned_value.update({"sell_taxes": sell_taxes})
        
    except Exception as e:
        sessionx.rollback()
        print(f"An error ocurred: {e}")
        returned_value = {}

    return returned_value