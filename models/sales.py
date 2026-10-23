from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db import Base # Ajusta la importación a tu Base de SQLAlchemy

class SalesHeader(Base):
    __tablename__ = "sales_header"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_code = Column(String(10), nullable=False)
    payment_method = Column(String(10), nullable=False)
    observations = Column(Text, nullable=True)

    wants_receipt = Column(Boolean, default=False)
    doc_type = Column(String(10), nullable=True)
    doc_number = Column(String(20), nullable=True)
    customer_name = Column(String(200), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    customer_email = Column(String(150), nullable=True)

    total_titles = Column(Integer, nullable=False)
    total_items = Column(Integer, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con el detalle
    details = relationship("SalesDetail", back_populates="header", cascade="all, delete-orphan")


class SalesDetail(Base):
    __tablename__ = "sales_detail"

    id = Column(Integer, primary_key=True, index=True)
    sales_header_id = Column(Integer, ForeignKey("sales_header.id"), nullable=False)
    product_id = Column(Integer, nullable=False)
    product_cod = Column(String(10), nullable=False)
    isbn = Column(String(20), nullable=True)
    title = Column(String(250), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    header = relationship("SalesHeader", back_populates="details")