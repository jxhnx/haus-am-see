from faker import Faker
import random
from datetime import datetime as dt
from datetime import timezone
from models import Customer, Product, Order, OrderItem, Payment
from database import SessionLocal
import logging
import time

logger = logging.getLogger(__name__)
fake = Faker()


def create_customer(db) -> Customer:
    customer = Customer(
        full_name=random.choice(
            [
                fake.name(),
                f"{fake.first_name()} {fake.last_name()[0]}.",
                f"{fake.first_name()} {fake.last_name()} {fake.last_name()}",
            ]
        ),
        email=f"{fake.user_name()}.{random.randint(1000, 999999)}@{fake.free_email_domain()}",
        address=fake.street_address(),
        city=fake.city(),
        country=fake.country(),
        created_at=fake.date_time_this_year(),
    )
    db.add(customer)
    return customer


def create_product(db) -> Product:
    product = Product(
        name=fake.word(),
        category=random.choice(
            ["electronics", "books", "toys", "clothing", "kitchen", "sports"]
        ),
        price=round(random.uniform(5.0, 300.0), 2),
        stock_quantity=random.randint(0, 100),
        created_at=fake.date_time_this_year(),
    )
    db.add(product)
    return product


def create_order(db, customer_id: int) -> Order:
    order = Order(
        customer_id=customer_id,
        status=random.choice(["pending", "shipped", "delivered", "cancelled"]),
        total=0,
        created_at=dt.now(timezone.utc),
    )
    db.add(order)
    return order


def create_order_items(db, order_id: int, products: list[Product]) -> float:
    total = 0
    for product in products:
        quantity = random.randint(1, 5)
        item = OrderItem(
            order_id=order_id,
            product_id=product.id,
            quantity=quantity,
            price_at_purchase=product.price,
        )
        db.add(item)
        total += quantity * product.price
    return round(total, 2)


def create_payment(db, order_id: int, amount: float):
    status = random.choices(["paid", "pending", "failed"], weights=[0.75, 0.15, 0.1])[0]
    payment = Payment(
        order_id=order_id,
        payment_method=random.choice(["credit_card", "paypal", "bank_transfer"]),
        paid_at=dt.now(timezone.utc) if status == "paid" else None,
        amount=amount,
        status=status,
    )
    db.add(payment)


def seed_initial_data(count: int, batch_size: int = 1000):
    db = SessionLocal()
    created = 0
    start = time.perf_counter()

    logger.info(f"Seeding started: count={count}, batch_size={batch_size}")

    while created < count:
        batch_remaining = min(batch_size, count - created)

        customers = [create_customer(db) for _ in range(batch_remaining // 2)]
        products = [create_product(db) for _ in range(batch_remaining)]
        db.flush()

        for _ in range(batch_remaining):
            customer = random.choice(customers)
            selected_products = random.sample(products, k=random.randint(1, 4))

            order = create_order(db, customer.id)
            db.flush()

            total = create_order_items(db, order.id, selected_products)
            order.total = total

            create_payment(db, order.id, total)

        db.commit()

        created += batch_remaining
        logger.info(f"Seeded {created}/{count} records")

    duration = round(time.perf_counter() - start, 2)
    logger.info(f"Seeding completed in {duration} seconds")
    db.close()


def seed_single_record():
    db = SessionLocal()

    customer = create_customer(db)
    product_count = random.randint(1, 4)
    products = [create_product(db) for _ in range(product_count)]
    db.commit()

    order = create_order(db, customer.id)
    db.commit()

    total = create_order_items(db, order.id, products)
    order.total = total
    db.commit()

    create_payment(db, order.id, total)
    db.commit()

    db.close()
