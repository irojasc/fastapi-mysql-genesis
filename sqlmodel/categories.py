from sqlalchemy import (
    Table, Column, Integer, String, SmallInteger,
    ForeignKey, text
)
from config.db import meta, engine

Categories = Table( "Categories", 
                    meta, 
                    Column("id", Integer, primary_key=True, autoincrement=True),

                    Column(
                        "idParent",
                        Integer,
                        ForeignKey("Categories.id", ondelete="CASCADE"),
                        nullable=True
                    ),

                    Column("Name", String(100), nullable=False),

                    Column("Slug", String(100), nullable=False, unique=True),

                    Column(
                        "Level",
                        SmallInteger,
                        nullable=False,
                        server_default=text("1")
                    ),

                    Column("MetaTitle", String(255), nullable=True),
                    Column("MetaDesc", String(255), nullable=True),
                )
meta.create_all(bind=engine)