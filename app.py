import logging
import os
import sys
from datetime import datetime

from flask_apscheduler import APScheduler
from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from marshmallow import ValidationError
from flask_uploads import configure_uploads, patch_request_class
from dotenv import load_dotenv

from db import db
from ma import ma
from blacklist import BLACKLIST
from resources.course import Course, CourseList, GetEnrolledUsers, EnrollUser, DisenrollUser
from resources.user import UserRegister, UserLogin, User, TokenRefresh, UserLogout, UserChangePassword
from resources.item import Item, ItemList
from resources.store import Store, StoreList
from resources.confirmation import Confirmation, ConfirmationByUser, ConfirmationByCode
from resources.image import ImageUpload
from models.course import CourseModel
from libs.image_helper import IMAGE_SET
import atexit


app = Flask(__name__)
if 'DYNO' in os.environ:
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.ERROR)
load_dotenv(".env", verbose=True)
app.config.from_object("default_config")  # load default configs from default_config.py
app.config.from_envvar(
    "APPLICATION_SETTINGS"
)  # override with config.py (APPLICATION_SETTINGS points to config.py)
patch_request_class(app, 10 * 1024 * 1024)
configure_uploads(app, IMAGE_SET)

api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


jwt = JWTManager(app)


# This method will check if a token is blacklisted, and will be called automatically when blacklist is enabled
@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    return decrypted_token["jti"] in BLACKLIST


api.add_resource(Store, "/store/<string:name>")
api.add_resource(StoreList, "/stores")
api.add_resource(Item, "/item/<string:name>")
api.add_resource(ItemList, "/items")
api.add_resource(UserRegister, "/register")
api.add_resource(User, "/user/<int:user_id>")
api.add_resource(UserLogin, "/login")
api.add_resource(UserChangePassword, "/change_password/<int:user_id>")
api.add_resource(TokenRefresh, "/refresh")
api.add_resource(UserLogout, "/logout")
api.add_resource(Confirmation, "/user_confirm/<string:confirmation_id>")
api.add_resource(ConfirmationByUser, "/confirmation/user/<int:user_id>")
api.add_resource(ConfirmationByCode, "/confirmation_code/user/<int:user_id>")
api.add_resource(ImageUpload, "/upload/image")
api.add_resource(Course, "/course/<int:course_id>", "/course/<string:name>")
api.add_resource(CourseList, "/courses")
api.add_resource(EnrollUser, "/enroll/")
api.add_resource(DisenrollUser, "/disenroll/")
api.add_resource(GetEnrolledUsers, "/enrolled_users/<int:course_id>")


# Config scheduling of Jobs
class Config(object):
    JOBS = [
        {
            'id': 'clear_courses',
            'func': CourseModel.clear_all,
            'args': (datetime.today().weekday(), True),
            'trigger': 'cron',
            'hour': 23,
            'minute': 00
        }
    ]

    SCHEDULER_API_ENABLED = True


if __name__ == "__main__":
    db.init_app(app)
    db.app = app
    ma.init_app(app)
    app.config.from_object(Config())
    # Jobs
    cron = APScheduler()
    cron.init_app(app)
    # Explicitly kick off the background thread
    cron.start()

    # Shutdown your cron thread if the web process is stopped
    atexit.register(lambda: cron.shutdown(wait=False))
    # Start Flask APP
    app.run(port=5000, host='0.0.0.0')

