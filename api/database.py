import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


# DATABASE_URL = (
#     "postgresql://{username}:{password}@{host}:{port}/{database_name}".format(
#         username=os.getenv("POSTGRES_USER"),
#         password=os.getenv("POSTGRES_PASSWORD"),
#         host=os.getenv("POSTGRES_HOST"),
#         port=os.getenv("POSTGRES_PORT"),
#         database_name=os.getenv("POSTGRES_DB"),
#     )
# )


# Database URL for SQLite
DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    return db
