from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from typing import Optional
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
async def get_stock_by_publisher(jwt_dependency: jwt_dependecy,
                                Isbn: Optional[str] = "",
                                Title: Optional[str] = "",
                                Autor: Optional[str] = "",
                                Publisher: Optional[str] = "",
                                ):
    if not(jwt_dependency):
        raise HTTPException(
            status_code=498,
            detail='Invalid Access Token',
        )
    else:
        if bool(Isbn) or bool(Title) or bool(Autor) or bool(Publisher):
            if bool(Isbn):
                query = f"wp.idProduct as idProduct, pr.isbn, pr.title, pr.autor, pr.publisher, wr.code, wp.pvNew, wp.isEnabled as enabled, wp.qtyNew as stock from genesisDB.ware_product wp inner join genesisDB.product pr on wp.idProduct = pr.id inner join genesisDB.ware wr on wp.idWare = wr.id where pr.isbn like '%{Isbn.upper()}%' and pr.title like '%{Title.upper()}%' and pr.autor like '%{Autor.upper()}%' and pr.publisher like '%{Publisher.upper()}%' group by wp.idProduct , pr.isbn, pr.title, pr.publisher, wr.code, wp.pvNew, wp.isEnabled, wp.qtyNew order by wp.idProduct asc"
            else:
                query = f"wp.idProduct as idProduct, pr.isbn, pr.title, pr.autor, pr.publisher, wr.code, wp.pvNew, wp.isEnabled as enabled, wp.qtyNew as stock from genesisDB.ware_product wp inner join genesisDB.product pr on wp.idProduct = pr.id inner join genesisDB.ware wr on wp.idWare = wr.id where pr.title like '%{Title.upper()}%' and pr.autor like '%{Autor.upper()}%' and pr.publisher like '%{Publisher.upper()}%' group by wp.idProduct , pr.isbn, pr.title, pr.publisher, wr.code, wp.pvNew, wp.isEnabled, wp.qtyNew order by wp.idProduct asc"
            stock = con.execute(select(text(query)))
            data = stock.fetchall()
            print(data)
            result = []
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
       
            return JSONResponse(
            status_code=200,
            content={"result": result}
            )
        else:
            raise HTTPException(status_code=404, detail='Nothing to show you')

    # if jwt_dependency:
    #     return {
    #         "content": product_list
    #     }
    # else:
    #     raise HTTPException(status_code=401, detail='Authentication failed')

