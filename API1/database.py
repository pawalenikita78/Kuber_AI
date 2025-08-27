# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Provide a full SQLAlchemy connection URL in env var DATABASE_URL
# Example: mysql+pymysql://user:password@host:3306/gold_db
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:12345niki@127.0.0.1:3306/gold_investments")

# Use pool_pre_ping to avoid stale connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
