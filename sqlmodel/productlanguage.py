from sqlalchemy import Table, Column, ForeignKey
from config.db import meta, engine
from sqlalchemy.dialects.mysql import SMALLINT, TINYINT

ProductLanguage = Table(
    "ProductLanguage",
    meta,
    Column(
        "idProduct",
        SMALLINT(unsigned=True),
        ForeignKey("product.id", ondelete="RESTRICT", onupdate="CASCADE"),
        primary_key=True,
        nullable=False
    ),

    Column(
        "idLanguage",
        TINYINT(unsigned=True),
        ForeignKey("language.id", ondelete="RESTRICT", onupdate="CASCADE"),
        primary_key=True,
        nullable=False
    ),
)

meta.create_all(bind=engine)