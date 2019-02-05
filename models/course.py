from datetime import datetime
from typing import List

from db import db

association_table = db.Table('association', db.Model.metadata,
                             db.Column('courses', db.Integer, db.ForeignKey('courses.id')),
                             db.Column('users', db.Integer, db.ForeignKey('users.id')))

week_list = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']


class CourseModel(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=False)
    users = db.relationship("UserModel", secondary=association_table)
    start_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(80), unique=False, nullable=False)
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)
    day_week = db.Column(db.Integer)
    slots = db.Column(db.Integer)

    @classmethod
    def find_by_id(cls, _id: int) -> "CourseModel":
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_name(cls, name: str) -> List["CourseModel"]:
        return cls.query.filter_by(name=name).all()

    @classmethod
    def find_all(cls) -> List["CourseModel"]:
        return cls.query.all()

    @classmethod
    def find_by_day(cls, day: int) -> List["CourseModel"]:
        return cls.query.filter_by(day_week=day).all()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

    def enroll_user(self, user) -> None:
        self.users.append(user)
        self.save_to_db()

    def disenroll_user(self, user) -> None:
        self.users.remove(user)
        self.save_to_db()

    def clear_users(self):
        self.users.clear()
        self.save_to_db()

    @classmethod
    def clear_all(cls, day=None, from_job=False):
        if day != 6:
            if from_job and day is not None:
                print('Clearing enrolled users in {}'.format(week_list[day].capitalize()))
            with db.app.app_context():
                if day is None:
                    for course in cls.find_all():
                        course.clear_users()
                else:
                    for course in cls.find_by_day(day):
                        course.clear_users()

