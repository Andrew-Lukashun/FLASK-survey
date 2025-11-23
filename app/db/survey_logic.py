# Логика опросов с поддержкой raw и ORM провайдеров
from app.db.raw_data_provider import RawDataProvider
from app.db.orm_data_provider import OrmDataProvider

class LogicProvider:
    def __init__(self, provider='raw'):
        self.data_provider = RawDataProvider() if provider == 'raw' else OrmDataProvider()

    def create_survey(self, **kwargs):
        return self.data_provider.create_survey(**kwargs)

    def get_all_surveys(self):
        return self.data_provider.get_all_surveys()

    def get_survey(self, survey_id):
        return self.data_provider.get_survey(survey_id)

    def get_survey_options(self, survey_id):
        return self.data_provider.get_survey_options(survey_id)

    def add_option(self, survey_id, description):
        return self.data_provider.add_option(survey_id, description)

    def delete_survey(self, survey_id):
        return self.data_provider.delete_survey(survey_id)

    def check_vote(self, survey_id, user_id=None, voter_ip=None):
        return self.data_provider.check_vote(survey_id, user_id, voter_ip)

    def submit_vote(self, survey_id, option_id, user_id=None, voter_ip=None):
        return self.data_provider.submit_vote(survey_id, option_id, user_id, voter_ip)

    def get_survey_results(self, survey_id):
        return self.data_provider.get_survey_results(survey_id)

    def get_survey_title(self, survey_id):
        return self.data_provider.get_survey_title(survey_id)
