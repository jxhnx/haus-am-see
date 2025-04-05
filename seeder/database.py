from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

STOREFRONT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@postgres_source:5432/storefront",
)
engine = create_engine(STOREFRONT_DB_URL)
SessionLocal = sessionmaker(bind=engine)
