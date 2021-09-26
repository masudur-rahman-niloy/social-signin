from auth_utils import get_cognito_user_by_email_phone, UserMatchNotFound
from model_dataclass.constants import EMAIL_MEDIUM


def lambda_handler(event, context):
    print(event)
    if event.get('triggerSource', '') == "PreSignUp_ExternalProvider":
        try:
            cognito_userpool_id = event["userPoolId"]

            # for some FB accounts, email wont be available
            # only accepting email for now, exception case FB phone signup
            if 'email' in event['request']['userAttributes']:
                email = event['request']['userAttributes']['email']
            else:
                raise Exception("::PRESIGNUP::Could not create user, no email provided. If you try from facebook please give permission to access your email.")

            result = get_cognito_user_by_email_phone(find_text=email, medium=EMAIL_MEDIUM, user_pool_id=cognito_userpool_id)
            print("result: ",result)
            raise Exception("::PRESIGNUP::User already exists")

        except UserMatchNotFound as match_not_found:
            print(match_not_found)
            return event
        except Exception as e:
            print(e)
            raise e

    return event

