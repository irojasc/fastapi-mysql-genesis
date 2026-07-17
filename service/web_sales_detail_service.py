from sqlalchemy import select
import json

from sqlmodel.checkoutattempts import CheckoutAttempts
from sqlmodel.product import Product
from sqlmodel.ware_product import Ware_Product
from sqlmodel.ubigeo import Ubigeo
from sqlmodel.ware import Ware
from service.order_flow_config import pasos_aprobacion


class WebSaleDetailService:

    def __init__(self, session):
        self.session = session

    def _obtener_pedido(self, docnum):
        stmt = (
        select(
            CheckoutAttempts.c.DocNum,
            CheckoutAttempts.c.ShipType,
            CheckoutAttempts.c.ShippingPayload,
            CheckoutAttempts.c.BillingPayload,
            CheckoutAttempts.c.CartPayload,
            CheckoutAttempts.c.ShippingAmount,
            CheckoutAttempts.c.StepOrder,
            Ware.c.id.label("idWare"),
            Ware.c.code.label("codeWare"),
            CheckoutAttempts.c.PreparingBy.label("preparadoPor"),
            CheckoutAttempts.c.HandedOverBy.label("entregadoPor")
        )
        .join(Ware, CheckoutAttempts.c.idWare == Ware.c.id, isouter=True)
        .where(
            CheckoutAttempts.c.DocNum == docnum
        )
        .limit(1)
        )

        pedido = self.session.execute(stmt).mappings().first()

        if pedido is None:
            return None
        
        return dict(pedido)

    def _obtener_productos(self, ids_productos):
        if not ids_productos:
            return {}

        stmt = (
            select(
                Product.c.id,
                Product.c.isbn,
                Product.c.title,
                Product.c.publisher
            )
            .where(
                Product.c.id.in_(ids_productos)
            )
        )

        resultado = self.session.execute(stmt).mappings().all()

        return {

            fila["id"]: dict(fila)

            for fila in resultado

        }


    def _obtener_stock(self, ids_productos, ware_id):
        if not ids_productos:
            return {}

        stmt = (
            select(
                Ware_Product.c.idProduct,
                Ware_Product.c.qtyNew
            )
            .where(
                Ware_Product.c.idWare == ware_id,
                Ware_Product.c.idProduct.in_(ids_productos)
            )
        )

        resultado = self.session.execute(stmt).mappings().all()

        return {

            # fila["idProduct"]: str(fila["qtyNew"])
            fila["idProduct"]: fila["qtyNew"] #cantidad stock retorna como int

            for fila in resultado

        }

    def _obtener_direccion_delivery(self,
    dep,
    prov,
    dist):
        stmt = (
        select(
            Ubigeo.c.dep_name,
            Ubigeo.c.pro_name,
            Ubigeo.c.dis_name
        )
        .where(
            Ubigeo.c.dep_id == dep,
            Ubigeo.c.pro_id == prov,
            Ubigeo.c.dis_id == dist
        )
        .limit(1)
        )

        fila = self.session.execute(stmt).mappings().first()

        if fila is None:

            return {
                "dep":"",
                "prov":"",
                "dist":""
            }

        return dict(fila)

    
    def _obtener_direccion_pickup(self, ware_id):
        stmt = (
        select(
            Ware.c.address
        )
        .where(
            Ware.c.id == ware_id
        )
        .limit(1)
        )

        fila = self.session.execute(stmt).mappings().first()

        if fila is None:

            return ""

        return fila["address"] or ""

    def _armar_respuesta(self,
        pedido,
        productos,
        stocks = None,
        ubicacion = None,
        ware_address = None
        ):
        
        shipping = pedido["ShippingPayload"] or {}
        billing = pedido["BillingPayload"] or {}
        cart = pedido["CartPayload"] or []
        
        if isinstance(shipping, str):
            shipping = json.loads(shipping)

        if isinstance(billing, str):
            billing = json.loads(billing)

        if isinstance(cart, str):
            cart = json.loads(cart)

        
        is_fact = bool(
           billing.get("isFactura", False)
        )

        respuesta = {

                "nroPedido": str(pedido["DocNum"]),

                "shipType": str(pedido["ShipType"]),

                "docType": str(
                    shipping.get("tipoDocumento","")
                ),

                "nroDoc": str(
                    shipping.get("documento","")
                ),

                "name": str(
                    shipping.get("nombre","")
                ),

                "lastName": str(
                    shipping.get("apellido","")
                ),

                "email": str(
                    shipping.get("email","")
                ),

                "phoneCode": str(
                    shipping.get("prefijo","")
                ),

                "phoneNumber": str(
                    shipping.get("telefono","")
                ),

                "address":"",

                "shipPrice":"0.00",

                "isFact":is_fact,

                "detail":[]
            }
        
        if pedido["ShipType"] == "DELIVERY":

            respuesta["dep"] = ubicacion["dep_name"]

            respuesta["prov"] = ubicacion["pro_name"]

            respuesta["dist"] = ubicacion["dis_name"]

            respuesta["address"] = str(
                shipping.get("address","")
            )

            respuesta["dic_ref"] = str(
                shipping.get("references","")
            )

            respuesta["shipPrice"] = "{:.2f}".format(
                float(pedido["ShippingAmount"] or 0)
            )
        
        else:

            respuesta["address"] = ware_address

            respuesta["shipPrice"] = "0.00"


        if is_fact:
            respuesta["rs"] = str(
                billing.get("razonSocial","")
            )

            respuesta["ruc"] = str(
                billing.get("ruc","")
            )
        

        respuesta["usuario"] = {
            "preparadoPor": pedido.get("preparadoPor", ""),
            "entregadoPor": pedido.get("entregadoPor", "")
        }

        respuesta["curOperacion"] = pedido.get("StepOrder", "")

        respuesta["almacen"] = {
            "idWare": pedido.get("idWare", ""),
            "codeWare": pedido.get("codeWare", "")
        }

        #datos importantes para el frontend
        ShipxType = pedido["ShipType"]
        StepxOrder = pedido.get("StepOrder", "")
        respuesta["cur_operation"] = {
                "btn_name": pasos_aprobacion.get(ShipxType, {}).get(str(StepxOrder), {}).get("btn_txt", ""),
                "btn_color": pasos_aprobacion.get(ShipxType, {}).get(str(StepxOrder), {}).get("btn_color", ""),
                "accion": pasos_aprobacion.get(ShipxType, {}).get(str(StepxOrder), {}).get("accion", ""),
                "isFinal": pasos_aprobacion.get(ShipxType, {}).get(str(StepxOrder), {}).get("isFinal", True),
            }


        for item in cart:
            id_producto = item["id"]

            producto = productos.get(
                id_producto,
                {}
            )
            stock = stocks.get(
                id_producto,
                "0"
            )

            respuesta["detail"].append({

            "id":str(id_producto),

            "isbn":str(
                producto.get("isbn","")
            ),

            "title":str(
                producto.get("title","")
            ),

            "publisher":str(
                producto.get("publisher","")
            ),

            "pvp":str(
                item.get("pvp","0.00")
            ),

            "dto":str(
                item.get("discountPercent","0.00")
            ),

            "pvf":str(
                item.get("finalPrice","0.00")
            ),

            # "qty":str(
            #     item.get("quantity","0")
            # ),

            "qty":int( #cambiamos a entero
                item.get("quantity","0")
            ),

            # "stock":str(stock)
            "stock":int(stock) #cambiamos a entero

        })

        return respuesta


    def get_detail(self,
        docnum: int,
        ware_id: int
        ):
        
        # 1. Obtener pedido
        pedido = self._obtener_pedido(docnum)

        if pedido is None:
            return None

        # 2. Obtener el carrito
        cart = pedido.get("CartPayload") or []

        if isinstance(cart, str):
            cart = json.loads(cart)

        # 3. Obtener ids de productos
        ids_productos = [
            item["id"]
            for item in cart
        ]


        # 4. Obtener información de productos
        productos = self._obtener_productos(
            ids_productos
        )


        #Si no existe el idWare asignado, entonces tomara el que llega
        AssignedIdWare = pedido.get("idWare", None)
        if AssignedIdWare is None:
            AssignedIdWare = ware_id

        # # 5. Obtener stock
        stocks = self._obtener_stock(
            ids_productos=ids_productos,
            ware_id=AssignedIdWare
        )

        # # 6. Obtener ubicación
        shipping = pedido.get("ShippingPayload") or {}

        if isinstance(shipping, str):
            shipping = json.loads(shipping)

        ubicacion = {}

        ware_address = ""

        if pedido["ShipType"] == "DELIVERY":

            ubicacion = self._obtener_direccion_delivery(
                shipping.get("department"),
                shipping.get("province"),
                shipping.get("district")
            )

        else:
            ware_address = self._obtener_direccion_pickup(
                ware_id
            )


        # # 7. Armar respuesta
        respuesta =  self._armar_respuesta(
            pedido=pedido,
            stocks=stocks,
            productos=productos,
            ubicacion=ubicacion,
            ware_address=ware_address
        )
        
    
        return respuesta
    