import os

class Config:
    # Secret key (override in Kubernetes)
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")

    # Database credentials via environment variables
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
    DB_HOST = os.getenv("DB_HOST", "mysql-db")
    DB_NAME = os.getenv("DB_NAME", "expense_db")

    # SQLAlchemy database URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )
