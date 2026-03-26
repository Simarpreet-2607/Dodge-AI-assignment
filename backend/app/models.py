"""
models.py - SQLAlchemy ORM models for all database entities
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, ForeignKey,
    Enum as SAEnum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    shipped   = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class DeliveryStatus(str, enum.Enum):
    pending    = "pending"
    in_transit = "in_transit"
    delivered  = "delivered"
    failed     = "failed"

class PaymentStatus(str, enum.Enum):
    pending  = "pending"
    paid     = "paid"
    failed   = "failed"
    refunded = "refunded"


# ── Models ─────────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False)
    phone      = Column(String(20))
    city       = Column(String(80))
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String(150), nullable=False)
    category = Column(String(80))
    price    = Column(Numeric(10, 2), nullable=False)
    stock    = Column(Integer, default=0)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id           = Column(Integer, primary_key=True, index=True)
    customer_id  = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date   = Column(DateTime, server_default=func.now())
    status       = Column(SAEnum(OrderStatus), default=OrderStatus.pending)
    total_amount = Column(Numeric(12, 2), default=0)
    notes        = Column(Text)

    customer    = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    delivery    = relationship("Delivery", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order   = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class Delivery(Base):
    __tablename__ = "deliveries"

    id           = Column(Integer, primary_key=True, index=True)
    order_id     = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    status       = Column(SAEnum(DeliveryStatus), default=DeliveryStatus.pending)
    delivered_at = Column(DateTime, nullable=True)
    carrier      = Column(String(80))
    tracking_no  = Column(String(100))

    order   = relationship("Order", back_populates="delivery")
    invoice = relationship("Invoice", back_populates="delivery", uselist=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id          = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False, unique=True)
    amount      = Column(Numeric(12, 2), nullable=False)
    issued_at   = Column(DateTime, server_default=func.now())
    due_date    = Column(DateTime, nullable=True)

    delivery = relationship("Delivery", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")


class Payment(Base):
    __tablename__ = "payments"

    id         = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount     = Column(Numeric(12, 2), nullable=False)
    status     = Column(SAEnum(PaymentStatus), default=PaymentStatus.pending)
    method     = Column(String(50))  # card, upi, netbanking, etc.
    paid_at    = Column(DateTime, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
