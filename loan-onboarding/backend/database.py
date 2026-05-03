import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL_PG = "postgresql://postgres:Sakshi%40998799@db.zzhasosufixuxcsxvwsg.supabase.co:5432/postgres"
DATABASE_URL_LITE = "sqlite:///./loan_wizard.db"

try:
    engine = create_engine(DATABASE_URL_PG, pool_pre_ping=True)
    engine.connect() # Test connection
    print("Connected to Supabase PostgreSQL.")
except Exception as e:
    print(f"Supabase connection failed ({e}). Falling back to SQLite.")
    engine = create_engine(DATABASE_URL_LITE, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
