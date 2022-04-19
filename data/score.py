import sqlalchemy
from data.db_session import SqlAlchemyBase


class Scores(SqlAlchemyBase):
    __tablename__ = "scores"

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    right = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    wrong = sqlalchemy.Column(sqlalchemy.Integer, default=0)
