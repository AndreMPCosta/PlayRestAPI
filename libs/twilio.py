import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.rest.api.v2010.account.message import MessageInstance

from libs.strings import gettext

twilio_phone_number = ''


class TwilioException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Twilio:
    load_dotenv(".env", verbose=True)
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", None)
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", None)
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    @classmethod
    def send_sms(
            cls, number: str, body: str,
    ) -> MessageInstance:
        if cls.TWILIO_ACCOUNT_SID is None:
            raise TwilioException(gettext("twilio_failed_load_account_sid"))

        if cls.TWILIO_AUTH_TOKEN is None:
            raise TwilioException(gettext("twilio_failed_load_auth_token"))

        response: MessageInstance = cls.client.messages.create(
            from_=twilio_phone_number,
            body=body,
            to=number
        )
        if response.status != 'queued':
            raise TwilioException(gettext("twilio_error_send_sms"))
        return response

