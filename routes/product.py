from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from typing import Optional
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from sqlmodel.product import Product
from functions.product import get_all_publishers

product_route = APIRouter(
    prefix = '/product',
    tags=['Product']
)

def get_isbn_isExists(isbn):
    return f"pr.isbn like '%{isbn.upper()}%' and " if bool(isbn) else " "


@product_route.get("/", status_code=200)
async def get_all_products(jwt_dependency: jwt_dependecy):
    if jwt_dependency:
        return {
            "content": []
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

