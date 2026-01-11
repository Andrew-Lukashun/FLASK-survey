from app.db.raw_data_provider import RawDataProvider
from app.db.orm_data_provider import OrmDataProvider

class LogicProvider:
    def __init__(self, provider='raw'):
        self.data_provider = RawDataProvider() if provider == 'raw' else OrmDataProvider()

    def create_user(self, **kwargs):
        if not kwargs.get('user_name') or len(kwargs.get('user_name')) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return self.data_provider.create_user(**kwargs)

    def get_user(self, user_name):
        return self.data_provider.get_user(user_name)
