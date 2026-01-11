# Модели базы данных для SQLAlchemy ORM
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, func, text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    surveys: Mapped[List['Survey']] = relationship('Survey', back_populates='user')
    votes: Mapped[List['Vote']] = relationship('Vote', back_populates='user')


class Survey(Base):
    __tablename__ = 'surveys'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_anonymous: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))

    user: Mapped[Optional['User']] = relationship('User', back_populates='surveys')
    options: Mapped[List['Option']] = relationship('Option', back_populates='survey', cascade="all, delete")
    votes: Mapped[List['Vote']] = relationship('Vote', back_populates='survey', cascade="all, delete")


class Option(Base):
    __tablename__ = 'options'

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    survey_id: Mapped[int] = mapped_column(ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False)

    survey: Mapped['Survey'] = relationship('Survey', back_populates='options')
    vote_options: Mapped[List['VoteOption']] = relationship('VoteOption', back_populates='option',
                                                            cascade="all, delete")


class Vote(Base):
    __tablename__ = 'votes'

    id: Mapped[int] = mapped_column(primary_key=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    voter_ip: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('survey_id', 'user_id', name='uq_survey_user'),
        UniqueConstraint('survey_id', 'voter_ip', name='uq_survey_voter_ip'),
    )

    survey: Mapped['Survey'] = relationship('Survey', back_populates='votes')
    user: Mapped[Optional['User']] = relationship('User', back_populates='votes')
    vote_options: Mapped[List['VoteOption']] = relationship('VoteOption', back_populates='vote', cascade="all, delete")


class VoteOption(Base):
    __tablename__ = 'vote_options'

    id: Mapped[int] = mapped_column(primary_key=True)
    vote_id: Mapped[int] = mapped_column(ForeignKey('votes.id', ondelete='CASCADE'), nullable=False)
    option_id: Mapped[int] = mapped_column(ForeignKey('options.id', ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('vote_id', 'option_id', name='uq_vote_option'),
    )

    vote: Mapped['Vote'] = relationship('Vote', back_populates='vote_options')
    option: Mapped['Option'] = relationship('Option', back_populates='vote_options')
