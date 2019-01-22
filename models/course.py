from typing import List

from db import db

association_table = db.Table('association', db.Model.metadata,
                             db.Column('courses', db.Integer, db.ForeignKey('courses.id')),
                             db.Column('users', db.Integer, db.ForeignKey('users.id')))


class CourseModel(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=False)
    users = db.relationship("UserModel", secondary=association_table)
    start_time = db.Column(db.DateTime)

    @classmethod
    def find_by_id(cls, _id: int) -> "CourseModel":
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_name(cls, name: str) -> List["CourseModel"]:
        return cls.query.filter_by(name=name).all()

    @classmethod
    def find_all(cls) -> List["CourseModel"]:
        print(cls.query.all())
        return cls.query.all()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

    def register_user(self, user) -> None:
        self.users.append(user)
        self.save_to_db()
