from sqlalchemy import Table, Column, text
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary, DECIMAL
from config.db import meta, engine

Product = Table("product", meta, 
                Column("id", Integer, nullable=False, unique=True, primary_key=True), 
                Column("idItem", Integer, nullable=True), 
                Column("isbn", String(15), nullable=True), 
                Column("title", String(90), nullable=False), 
                Column("autor", String(45), nullable=False), 
                Column("publisher", String(90), nullable=False),
                Column("content", String(800), default=None), 
                Column("dateOut", Date, default=None), 
                Column("idLanguage", Integer, default=None),
                Column("pages", Integer, default=None),
                Column("weight", Integer, default=None),
                Column("cover", _Binary, default=None),
                Column("width", Integer, default=None),
                Column("height", Integer, default=None),
                Column("creationDate", Date, nullable=False),
                Column("editDate", Date, nullable=False),
                Column("large", Integer, default=None),
                Column("wholesale", _Binary, default=None),
                Column("antique", _Binary, default=None),
                Column("isDelete", _Binary, default=None),
                Column("atWebProm", _Binary, default=None),
                Column("InvntItem", String(1), nullable=False, default=None), # es articulo inventariable?
                Column("SellItem", String(1), nullable=False, default=None), # es articulo venta?
                Column("BuyItem", String(1), nullable=False, default=None), # es articulo compra?
                Column("InvntryUom", String(3), nullable=False, default=None), #unidad de inventario (Aplica para venta/compra)
                Column("LastPurPrc", DECIMAL(8, 2), nullable=False, server_default=text("0.0")), #ultimo precio de compra
                Column("AvgPrice", DECIMAL(8, 2), nullable=False, server_default=text("0.0")), #precio promedio
                Column("CardCode", String(15), default=None), #proveedor por defecto
                Column("VatBuy", String(8), default=None), #impuesto compra
                Column("VatSell", String(2), default=None), #impuesto venta
                )
meta.create_all(bind=engine)
