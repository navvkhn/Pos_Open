from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from db import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    username = Column(String)
    password = Column(String)
    role = Column(String)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer)
    name = Column(String)
    price = Column(Float)
    category = Column(String)
    available = Column(Boolean, default=True)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer)
    table_no = Column(String)
    total = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer)
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)

class Discount(Base):
    __tablename__ = "discounts"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer)
    code = Column(String)
    type = Column(String)
    value = Column(Float)
    active = Column(Boolean, default=True)
