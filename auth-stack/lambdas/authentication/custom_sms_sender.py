from auth_utils import add_db_confirmation_item
from global_utils import decrypt_code, add_msg_to_sqs, get_sqs_sms_msg
from model_dataclass.auth_model import ConfirmationCodeModel
from model_dataclass.constants import PHONE_MEDIUM, APP_NAME, COGNITO_USER_ID_ATTRIBUTE

trigger_source_list = [
    "CustomSMSSender_SignUp",
    "CustomSMSSender_ResendCode",
    "CustomSMSSender_ForgotPassword",
    "CustomSMSSender_AdminCreateUser",
    "CustomSMSSender_VerifyUserAttribute"
]


def lambda_handler(event, context):
    print('event', event)
    trigger = event["triggerSource"]

    try:
        if trigger in trigger_source_list:
            user_id = event["request"]["userAttributes"][COGNITO_USER_ID_ATTRIBUTE]
            to = event["request"]["userAttributes"]["phone_number"]
            code = event["request"]['code']
            decrypted_code = decrypt_code(code)
            print('decrypted code: ', decrypted_code)

            msg = f'CodersTrust Code - {decrypted_code}'
            if trigger == "CustomSMSSender_SignUp" or trigger == "CustomSMSSender_ResendCode":
                msg = f'{APP_NAME} signup confirmation code - {decrypted_code}'
            elif trigger == "CustomSMSSender_ForgotPassword":
                msg = f'{APP_NAME} code to reset password - {decrypted_code}'
            elif trigger == "CustomSMSSender_AdminCreateUser":
                msg = f'{APP_NAME} temp password. Your phone number is your username and password is {decrypted_code}'
            elif trigger == "CustomSMSSender_VerifyUserAttribute":
                msg = f'{APP_NAME} verification code - {decrypted_code}'

            response = add_msg_to_sqs(get_sqs_sms_msg(
                target=to,
                sms_message=msg,
            )
            )

            confirmation_item = ConfirmationCodeModel(userId=user_id, code=decrypted_code, destination=to,
                                                      medium=PHONE_MEDIUM)
            db_response = add_db_confirmation_item(confirmation_item)

            return event

        else:
            raise Exception('Invalid trigger source')

    except Exception as e:
        print(e)
        raise Exception('Failed to send SMS using custom provider')


