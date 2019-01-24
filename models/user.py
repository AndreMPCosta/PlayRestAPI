from requests import Response
from flask import request, url_for
from twilio.rest.api.v2010.account.message import MessageInstance

from libs.strings import gettext
from libs.twilio import Twilio

from db import db
from libs.mailgun import Mailgun
from models.confirmation import ConfirmationModel


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    #username = db.Column(db.String(80), nullable=True, unique=True)
    password = db.Column(db.String(200), nullable=True)
    temporary_password = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    name = db.Column(db.String(80))
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(1))

    confirmation = db.relationship(
        "ConfirmationModel", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def most_recent_confirmation(self) -> "ConfirmationModel":
        # ordered by expiration time (in descending order)
        return self.confirmation.order_by(db.desc(ConfirmationModel.expire_at)).first()

    @classmethod
    def find_by_username(cls, username: str) -> "UserModel":
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email: str) -> "UserModel":
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_phone(cls, phone: str) -> "UserModel":
        return cls.query.filter_by(phone=phone).first()

    @classmethod
    def find_by_id(cls, _id: int) -> "UserModel":
        return cls.query.filter_by(id=_id).first()

    def send_confirmation_email(self) -> Response:
        # configure e-mail contents
        subject = "Registration Confirmation"
        link = request.url_root[:-1] + url_for(
            "confirmation", confirmation_id=self.most_recent_confirmation.id
        )
        # string[:-1] means copying from start (inclusive) to the last index (exclusive), a more detailed link below:
        # from `http://127.0.0.1:5000/` to `http://127.0.0.1:5000`, since the url_for() would also contain a `/`
        # https://stackoverflow.com/questions/509211/understanding-pythons-slice-notation
        text = f"Please click the link to confirm your registration: {link}"
        html = f"<html>Please click the link to confirm your registration: <a href={link}>link</a></html>"
        # send e-mail with MailGun
        return Mailgun.send_email([self.email], subject, text, html)

    def send_sms(self) -> MessageInstance:
        text = gettext("user_sms_text_code").format(str(self.most_recent_confirmation.code))
        return Twilio.send_sms(number="+351" + self.phone, body=text)

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
