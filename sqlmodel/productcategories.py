from sqlalchemy import (
    Table, Column, Integer, Boolean,
    ForeignKey, text
)
from config.db import meta, engine

ProductCategories = Table(
    "ProductCategories",
    meta,

    Column(
        "idProduct",
        Integer,
        primary_key=True,
        nullable=False
    ),
    Column(
        "idCategory",
        Integer,
        ForeignKey("Categories.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),

    Column(
        "isMain",
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0")
    )
)

meta.create_all(bind=engine)