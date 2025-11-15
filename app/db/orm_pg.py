# Настройка SQLAlchemy ORM для работы с PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.config import DATABASE_CONFIG

DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT = DATABASE_CONFIG.values()
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
