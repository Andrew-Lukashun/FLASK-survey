# ORM провайдер данных для работы с базой через SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select, func, and_
from app.db.orm_pg import get_session
from app.db.models import User, Survey, Option, Vote, VoteOption

class OrmDataProvider:
    @staticmethod
    def create_survey(**kwargs):
        with get_session() as session:
            survey = Survey(**kwargs)
            session.add(survey)
            session.commit()
            session.refresh(survey)
            return {'id': survey.id}

    @staticmethod
    def get_all_surveys():
        with get_session() as session:
            stmt = select(Survey)
            surveys = session.execute(stmt).scalars().all()
            return [(s.id, s.title, s.description, s.created_by, s.created_at, s.is_anonymous) for s in surveys]

    @staticmethod
    def get_survey(survey_id):
        with get_session() as session:
            stmt = select(Survey).where(Survey.id == survey_id)
            survey = session.execute(stmt).scalar_one_or_none()
            if survey:
                return (survey.id, survey.title, survey.description, survey.created_by, survey.created_at, survey.is_anonymous, getattr(survey.user, 'user_name', None))
            return None

    @staticmethod
    def get_survey_options(survey_id):
        with get_session() as session:
            stmt = select(Option).where(Option.survey_id == survey_id)
            options = session.execute(stmt).scalars().all()
            return [(o.id, o.description) for o in options]

    @staticmethod
    def add_option(survey_id, description):
        with get_session() as session:
            option = Option(survey_id=survey_id, description=description)
            session.add(option)
            session.commit()

    @staticmethod
    def delete_survey(survey_id):
        with get_session() as session:
            stmt = select(Survey).where(Survey.id == survey_id)
            survey = session.execute(stmt).scalar_one_or_none()
            if survey:
                session.delete(survey)
                session.commit()

    @staticmethod
    def create_user(**kwargs):
        with get_session() as session:
            user = User(user_name=kwargs['user_name'], password=generate_password_hash(kwargs['password']))
            session.add(user)
            session.commit()

    @staticmethod
    def get_user(user_name):
        with get_session() as session:
            stmt = select(User).where(User.user_name == user_name)
            user = session.execute(stmt).scalar_one_or_none()
            if user:
                return {'id': user.id, 'user_name': user.user_name, 'password': user.password}
            return None
        