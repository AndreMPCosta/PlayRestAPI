from flask_restful import Resource
from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
)
import traceback

from libs.twilio import TwilioException
from models.user import UserModel
from schemas.user import UserSchema
from models.confirmation import ConfirmationModel
from blacklist import BLACKLIST
from libs.mailgun import MailGunException
from libs.strings import gettext
from utils.password_manager import encrypt_password, check_encrypted_password

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        if 'password' in user_json:
            user_json['password'] = encrypt_password(user_json['password'])
        user = user_schema.load(user_json, instance=UserModel())

        # if UserModel.find_by_username(user.username):
        #     return {"message": gettext("user_username_exists")}, 400
        if UserModel.find_by_id(user.id):
            return {"message": gettext("user_id_exists")}, 400

        if UserModel.find_by_email(user.email):
            return {"message": gettext("user_email_exists")}, 400

        if UserModel.find_by_phone(user.phone) and user.phone:
            return {"message": gettext("user_phone_exists")}, 400

        try:
            user.save_to_db()
            confirmation = ConfirmationModel(user.id)
            confirmation.save_to_db()
            user.send_confirmation_email()
            if user.phone:
                user.send_sms()
            return {"message": gettext("user_registered")}, 201
        except MailGunException as e:
            user.delete_from_db()  # rollback
            return {"message": str(e)}, 500
        except TwilioException as e:
            user.delete_from_db()  # rollback
            return {"message": str(e)}, 500
        except:  # failed to save user to db
            traceback.print_exc()
            user.delete_from_db()  # rollback
            return {"message": gettext("user_error_creating")}, 500

    @classmethod
    def put(cls):
        user_json = request.get_json()
        user = UserModel.find_by_id(user_json['user_id'])
        if not user:
            return {"message": gettext("user_not_found")}, 404
        if user.password:
            return {"message": gettext("user_id_exists")}, 400
        user.temporary_password = encrypt_password(user_json['temporary_password'])
        try:
            user.save_to_db()
            #print(user.most_recent_confirmation)
            if not user.most_recent_confirmation:
                confirmation = ConfirmationModel(user.id)
                confirmation.save_to_db()
                user.send_confirmation_email()
                user.send_sms()
            elif user.most_recent_confirmation.expired:
                confirmation = ConfirmationModel(user.id)
                confirmation.save_to_db()
                user.send_confirmation_email()
                user.send_sms()
            elif not user.most_recent_confirmation.expired:
                return {"message": gettext("confirmation_already_sent")}, 409
            return {"message": gettext("user_registered")}, 201
        except MailGunException as e:
            user.delete_from_db()  # rollback
            return {"message": str(e)}, 500
        except TwilioException as e:
            user.delete_from_db()  # rollback
            return {"message": str(e)}, 500
        except:  # failed to save user to db
            traceback.print_exc()
            return {"message": gettext("user_error_creating")}, 500


class User(Resource):
    @classmethod
    @jwt_required
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404

        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404

        user.delete_from_db()
        return {"message": gettext("user_deleted")}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json, instance=UserModel(), partial=('email', 'phone', 'name',))

        user = UserModel.find_by_id(user_data.id)
        if not user.password:
            return {"message": gettext("user_not_registered").format(user.email)}, 400

        if user and check_encrypted_password(user_data.password, user.password):
            confirmation = user.most_recent_confirmation
            if confirmation and confirmation.confirmed:
                access_token = create_access_token(user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return (
                    {"access_token": access_token, "refresh_token": refresh_token},
                    200,
                )
            return {"message": gettext("user_not_confirmed").format(user.email)}, 400

        return {"message": gettext("user_invalid_credentials")}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_raw_jwt()["jti"]  # jti is "JWT ID", a unique identifier for a JWT.
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        return {"message": gettext("user_logged_out").format(user_id)}, 200


class UserChangePassword(Resource):
    @classmethod
    @jwt_required
    def post(cls, user_id: int):
        user_json = request.get_json()
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404
        user.password = encrypt_password(user_json['password'])
        try:
            user.save_to_db()
        except:  # failed to save user to db
            traceback.print_exc()
            return {"message": gettext("user_error_password")}, 500
        return {"message": gettext("user_password_success").format(user_id)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200
