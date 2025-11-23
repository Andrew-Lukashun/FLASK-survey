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

    @staticmethod
    def check_vote(survey_id, user_id=None, voter_ip=None):
        with get_session() as session:
            if user_id:
                stmt = select(Vote).where(
                    and_(Vote.survey_id == survey_id, Vote.user_id == user_id)
                )
            else:
                stmt = select(Vote).where(
                    and_(Vote.survey_id == survey_id, Vote.voter_ip == voter_ip)
                )
            vote = session.execute(stmt).scalar_one_or_none()
            return vote is not None

    @staticmethod
    def submit_vote(survey_id, option_id, user_id=None, voter_ip=None):
        with get_session() as session:
            vote = Vote(survey_id=survey_id, user_id=user_id, voter_ip=voter_ip)
            session.add(vote)
            session.commit()
            session.refresh(vote)

            vote_option = VoteOption(vote_id=vote.id, option_id=option_id)
            session.add(vote_option)
            session.commit()

    @staticmethod
    def get_survey_results(survey_id):
        with get_session() as session:
            stmt = select(
                Option.description,
                func.count(VoteOption.id).label('vote_count')
            ).select_from(Option).outerjoin(
                VoteOption, Option.id == VoteOption.option_id
            ).where(
                Option.survey_id == survey_id
            ).group_by(
                Option.id, Option.description
            ).order_by(
                func.count(VoteOption.id).desc()
            )
            results = session.execute(stmt).all()
            return [(result[0], result[1]) for result in results]

    @staticmethod
    def get_survey_title(survey_id):
        with get_session() as session:
            stmt = select(Survey.title).where(Survey.id == survey_id)
            result = session.execute(stmt).scalar_one_or_none()
            return result
