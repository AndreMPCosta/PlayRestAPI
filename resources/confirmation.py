from flask import render_template, make_response, request
from flask_restful import Resource
import traceback
from time import time

from libs.twilio import TwilioException
from models.confirmation import ConfirmationModel
from schemas.confirmation import ConfirmationSchema
from models.user import UserModel
from libs.mailgun import MailGunException
from libs.strings import gettext

confirmation_schema = ConfirmationSchema()


class Confirmation(Resource):
    # returns the confirmation page
    @classmethod
    def get(cls, confirmation_id: str):
        confirmation = ConfirmationModel.find_by_id(confirmation_id)
        if not confirmation:
            return {"message": gettext("confirmation_not_found")}, 404

        if confirmation.expired:
            return {"message": gettext("confirmation_link_expired")}, 400

        if confirmation.confirmed:
            return {"message": gettext("confirmation_already_confirmed")}, 400

        if confirmation.user.temporary_password:
            confirmation.user.password = confirmation.user.temporary_password
        confirmation.user.save_to_db()
        confirmation.confirmed = True
        confirmation.save_to_db()

        headers = {"Content-Type": "text/html"}
        return make_response(
            render_template("confirmation_page.html", email=confirmation.user.email),
            200,
            headers,
        )


class ConfirmationByUser(Resource):
    @classmethod
    def get(cls, user_id: int):
        """
        This endpoint is used for testing and viewing Confirmation models and should not be exposed to public.
        """
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404
        return (
            {
                "current_time": int(time()),
                # we filter the result by expiration time in descending order for convenience
                "confirmation": [
                    confirmation_schema.dump(each)
                    for each in user.confirmation.order_by(ConfirmationModel.expire_at)
                ],
            },
            200,
        )

    @classmethod
    def post(cls, user_id: int):
        """
        This endpoint resend the confirmation email with a new confirmation model. It will force the current
        confirmation model to expire so that there is only one valid link at once.
        """
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404

        try:
            # find the most current confirmation for the user
            confirmation = user.most_recent_confirmation  # using property decorator
            if confirmation:
                if confirmation.confirmed:
                    return {"message": gettext("confirmation_already_confirmed")}, 400
                confirmation.force_to_expire()

            new_confirmation = ConfirmationModel(user_id)  # create a new confirmation
            new_confirmation.save_to_db()
            # Does `user` object know the new confirmation by now? Yes.
            # An excellent example where lazy='dynamic' comes into use.
            user.send_confirmation_email()  # re-send the confirmation email
            user.send_sms()
            return {"message": gettext("confirmation_resend_successful")}, 201
        except MailGunException as e:
            return {"message": str(e)}, 500
        except TwilioException as e:
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            return {"message": gettext("confirmation_resend_fail")}, 500


class ConfirmationByCode(Resource):
    @classmethod
    def post(cls, user_id: int):
        """
        This endpoint is used for testing and viewing Confirmation models and should not be exposed to public.
        """
        user = UserModel.find_by_id(user_id)
        confirmation = user.most_recent_confirmation
        code = request.get_json()['code']
        if not user:
            return {"message": gettext("user_not_found")}, 404
        if not confirmation:
            return {"message": gettext("confirmation_not_found")}, 404
        if confirmation.expired:
            return {"message": gettext("confirmation_code_expired")}, 400
        if confirmation.code != code:
            return{"message": gettext("user_invalid_code")}, 401
        if confirmation.confirmed:
            return {"message": gettext("confirmation_already_confirmed")}, 400

        if user.temporary_password:
            user.password = user.temporary_password
        user.save_to_db()
        confirmation.confirmed = True
        confirmation.save_to_db()
        return {"message": gettext("confirmation_successful")}, 200
