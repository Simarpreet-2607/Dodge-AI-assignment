"""
seed.py - Populate Neon DB with realistic sample data

Run with: python -m app.seed
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import random

from sqlalchemy import text
from app.database import AsyncSessionLocal, engine
from app.models import (
    Base, Customer, Product, Order, OrderItem,
    Delivery, Invoice, Payment,
    OrderStatus, DeliveryStatus, PaymentStatus
)


CUSTOMERS = [
    ("Arjun Sharma",    "arjun.sharma@email.com",   "+91-9812345678", "Mumbai"),
    ("Priya Gupta",     "priya.gupta@email.com",    "+91-9823456789", "Delhi"),
    ("Rahul Verma",     "rahul.verma@email.com",    "+91-9834567890", "Bangalore"),
    ("Sunita Patel",    "sunita.patel@email.com",   "+91-9845678901", "Hyderabad"),
    ("Amit Joshi",      "amit.joshi@email.com",     "+91-9856789012", "Chennai"),
    ("Kavya Reddy",     "kavya.reddy@email.com",    "+91-9867890123", "Pune"),
    ("Vikram Singh",    "vikram.singh@email.com",   "+91-9878901234", "Kolkata"),
    ("Neha Malhotra",   "neha.malhotra@email.com",  "+91-9889012345", "Jaipur"),
    ("Suresh Kumar",    "suresh.kumar@email.com",   "+91-9890123456", "Ahmedabad"),
    ("Deepika Iyer",    "deepika.iyer@email.com",   "+91-9801234567", "Surat"),
]

PRODUCTS = [
    ("Laptop Pro 15",        "Electronics",   Decimal("75000"), 50),
    ("Wireless Headphones",  "Electronics",   Decimal("3500"),  200),
    ("Smart Watch",          "Electronics",   Decimal("12000"), 80),
    ("Office Chair Ergonomic","Furniture",    Decimal("18000"), 30),
    ("Standing Desk",        "Furniture",     Decimal("25000"), 20),
    ("USB-C Hub 7-in-1",     "Accessories",   Decimal("2500"),  150),
    ("Mechanical Keyboard",  "Electronics",   Decimal("6500"),  100),
    ("4K Monitor 27\"",      "Electronics",   Decimal("32000"), 40),
    ("Webcam HD 1080p",      "Electronics",   Decimal("4200"),  90),
    ("Notebook Set (5pc)",   "Stationery",    Decimal("350"),   500),
    ("Whiteboard Markers",   "Stationery",    Decimal("180"),   800),
    ("Power Bank 20000mAh",  "Accessories",   Decimal("1800"),  300),
    ("Mouse Wireless",       "Electronics",   Decimal("1500"),  250),
    ("Desk Lamp LED",        "Furniture",     Decimal("2200"),  120),
    ("Cable Management Kit", "Accessories",   Decimal("750"),   400),
]

CARRIERS   = ["BlueDart", "Delhivery", "FedEx", "DTDC", "Ecom Express"]
PAY_METHODS = ["credit_card", "debit_card", "upi", "netbanking", "wallet"]


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ── Clear existing data ──────────────────────────────────────
        print("Clearing existing data...")
        for tbl in ["payments", "invoices", "deliveries", "order_items", "orders", "products", "customers"]:
            await db.execute(text(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE"))
        await db.commit()

        # ── Customers ────────────────────────────────────────────────
        print("Seeding customers...")
        customers = []
        for name, email, phone, city in CUSTOMERS:
            c = Customer(name=name, email=email, phone=phone, city=city)
            db.add(c)
            customers.append(c)
        await db.flush()

        # ── Products ─────────────────────────────────────────────────
        print("Seeding products...")
        products = []
        for name, category, price, stock in PRODUCTS:
            p = Product(name=name, category=category, price=price, stock=stock)
            db.add(p)
            products.append(p)
        await db.flush()

        # ── Orders + Items + Deliveries + Invoices + Payments ────────
        print("Seeding orders, deliveries, invoices, payments...")

        statuses = list(OrderStatus)
        delivery_statuses = list(DeliveryStatus)

        base_date = datetime(2024, 1, 1)

        for i in range(25):
            customer = random.choice(customers)
            order_date = base_date + timedelta(days=random.randint(0, 365))
            o_status = random.choice(statuses)

            order = Order(
                customer_id=customer.id,
                order_date=order_date,
                status=o_status,
                total_amount=Decimal("0"),
            )
            db.add(order)
            await db.flush()

            # 1–4 items per order
            total = Decimal("0")
            selected_products = random.sample(products, k=random.randint(1, 4))
            for prod in selected_products:
                qty = random.randint(1, 5)
                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=prod.price,
                )
                db.add(item)
                total += prod.price * qty

            order.total_amount = total
            await db.flush()

            # Delivery (90% of orders get a delivery)
            if random.random() < 0.90:
                d_status = (
                    DeliveryStatus.delivered if o_status == OrderStatus.delivered
                    else random.choice(delivery_statuses)
                )
                delivered_at = (
                    order_date + timedelta(days=random.randint(1, 7))
                    if d_status == DeliveryStatus.delivered else None
                )
                delivery = Delivery(
                    order_id=order.id,
                    status=d_status,
                    delivered_at=delivered_at,
                    carrier=random.choice(CARRIERS),
                    tracking_no=f"TRK{random.randint(100000, 999999)}",
                )
                db.add(delivery)
                await db.flush()

                # Invoice (80% of deliveries get invoiced)
                if random.random() < 0.80:
                    inv_amount = total * Decimal("1.18")  # GST 18%
                    invoice = Invoice(
                        delivery_id=delivery.id,
                        amount=round(inv_amount, 2),
                        issued_at=order_date + timedelta(days=random.randint(1, 3)),
                        due_date=order_date + timedelta(days=30),
                    )
                    db.add(invoice)
                    await db.flush()

                    # Payment (85% of invoices get a payment)
                    if random.random() < 0.85:
                        p_status = random.choice([
                            PaymentStatus.paid, PaymentStatus.paid,
                            PaymentStatus.paid, PaymentStatus.pending,
                            PaymentStatus.failed
                        ])
                        payment = Payment(
                            invoice_id=invoice.id,
                            amount=invoice.amount,
                            status=p_status,
                            method=random.choice(PAY_METHODS),
                            paid_at=(
                                invoice.issued_at + timedelta(days=random.randint(0, 15))
                                if p_status == PaymentStatus.paid else None
                            ),
                        )
                        db.add(payment)

        await db.commit()
        print("Seeding complete!")
        print(f"   Customers: {len(customers)}")
        print(f"   Products : {len(products)}")
        print(f"   Orders   : 25")


if __name__ == "__main__":
    asyncio.run(seed())
