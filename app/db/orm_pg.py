# Настройка SQLAlchemy ORM для работы с PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.config import DATABASE_CONFIG

# Безопасное извлечение данных по ключам
DB_NAME = DATABASE_CONFIG.get('dbname')
DB_USER = DATABASE_CONFIG.get('user')
DB_PASSWORD = DATABASE_CONFIG.get('password')
DB_HOST = DATABASE_CONFIG.get('host')
DB_PORT = DATABASE_CONFIG.get('port')

# Формируем строку подключения
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
