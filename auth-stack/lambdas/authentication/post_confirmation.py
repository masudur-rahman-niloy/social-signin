from auth_utils import email_phone_exists, add_user_to_group, add_dynamo_user
from global_utils import connection, cognito_idp_client
from model_dataclass.auth_model import SignupModel, UserModel
from model_dataclass.constants import INITIAL_ROLE, EMAIL_MEDIUM, COGNITO_EXTERNAL_SIGNUP_MEDIUM_VALUE, \
    COGNITO_SIGNUP_MEDIUM_ATTRIBUTE, COGNITO_USER_ID_ATTRIBUTE


def lambda_handler(event, context):
    print(event)

    try:
        user_status = event['request']['userAttributes']['cognito:user_status']
        if user_status == "EXTERNAL_PROVIDER":
            print("event['request']['userAttributes']: ",event['request']['userAttributes'])
            username = event["userName"]
            name = event['request']['userAttributes']['name']
            cognito_userpool_id = event["userPoolId"]

            email = event['request']['userAttributes']['email']
            dummy_signup_model: SignupModel = SignupModel(name='test', email= email, emailOrPhone=email, password='Abcde123', role=INITIAL_ROLE, medium=EMAIL_MEDIUM)
            print("post confirmation: ",dummy_signup_model)
            if email_phone_exists(dummy_signup_model):
                raise Exception("Account with this email already exists")
            dummy_user_model: UserModel = UserModel(name=name, signupRole=INITIAL_ROLE, role=INITIAL_ROLE,
                                                    signupMedium=EMAIL_MEDIUM, email=email, emailVerified=True,
                                                    receivePromotionalEmail=True)
            cognito_response = add_user_to_group(username, INITIAL_ROLE, user_pool_id=cognito_userpool_id)
            print("cognito_response in post confirmation ",cognito_response)
            verify_response = admin_update_attributes(cognito_userpool_id, username, dummy_user_model)

            dynamo_response = add_dynamo_user(dummy_user_model, dummy_signup_model, is_admin_created=True)
            print("dynamo_response ",dynamo_response)

        return event
    
    except Exception as error:
        print(error)
        raise Exception(f"::POSTCONFIRMATION::{str(error)}")


def admin_update_attributes(cognito_userpool_id, username, user_model: UserModel):
    verify_response = cognito_idp_client.admin_update_user_attributes(
        UserPoolId=cognito_userpool_id,
        Username=username,
        UserAttributes=[
            {
                'Name': 'email',
                'Value': user_model.email
            },
            {
                'Name': 'email_verified',
                'Value': 'true'
            },
            {
                'Name': COGNITO_SIGNUP_MEDIUM_ATTRIBUTE,
                'Value': COGNITO_EXTERNAL_SIGNUP_MEDIUM_VALUE
            },
            {
                'Name': COGNITO_USER_ID_ATTRIBUTE,
                'Value': user_model.userId,
            },
        ],
    )
    print("verify_response in postconfirmation page: ",verify_response)
    return verify_response



