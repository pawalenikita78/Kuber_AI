import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import time

# Load .env file (works in both local dev and Docker)
load_dotenv()

# Build connection string from environment variables
DB_USER = os.getenv("DB_USER", "gold_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345niki")
DB_HOST = os.getenv("DB_HOST", "db")  # "db" for Docker, "localhost" for local
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "gold_investments")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pooling and retry logic
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    pool_size=10,
    max_overflow=20,
    connect_args={"connect_timeout": 10}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional: Function to check database connection
def check_db_connection():
    """Check if database connection is successful"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Optional: Wait for database to be ready (for Docker startup)
def wait_for_db(max_retries=30, retry_delay=2):
    """Wait for database to become available"""
    for attempt in range(max_retries):
        if check_db_connection():
            print("✅ Database connection successful!")
            return True
        print(f"⏳ Attempt {attempt + 1}/{max_retries}: Waiting for database...")
        time.sleep(retry_delay)
    print("❌ Database connection failed after multiple attempts")
    return False