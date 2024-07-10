from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from utils.validate_jwt import jwt_dependecy
from config.db import con

product_route = APIRouter(
    prefix = '/product',
    tags=['Product']
)

product_list = [{"id": 1, "title": "candado"}, {"id": 2, "title": "tranca"}]

@product_route.get("/", status_code=200)
async def get_products(jwt_dependency: jwt_dependecy):
    if jwt_dependency:
        return {
            "content": product_list
        }
    else:
        raise HTTPException(status_code=401, detail='Authentication failed')

@product_route.get("/stock", status_code=200)
async def get_stock_by_publisher(jwt_dependency: jwt_dependecy, Publisher: str = None):
    query = "wp.idProduct as idProduct, pr.isbn, pr.title, pr.publisher, sum(wp.qtyNew) as stock from genesisDB.ware_product wp inner join genesisDB.product pr on wp.idProduct = pr.id where pr.publisher = \"{}\" group by  wp.idProduct , pr.isbn, pr.title, pr.publisher order by wp.idProduct asc;".format(Publisher.upper())
    if not(jwt_dependency):
        raise HTTPException(
            status_code=498,
            detail='Invalid Access Token',
        )
    else:
        stock = con.execute(select(text(query)))
        data = stock.fetchall()
        if bool(len(data)):
            result  = list(map(lambda x: {"id": x[0], "isbn": x[1], "title": x[2], "publisher": x[3], "stock": int(x[4])}, data))
        else:
            result = []
        return JSONResponse(
            status_code=200,
            content={"result": result}
            )
    # if jwt_dependency:
    #     return {
    #         "content": product_list
    #     }
    # else:
    #     raise HTTPException(status_code=401, detail='Authentication failed')

