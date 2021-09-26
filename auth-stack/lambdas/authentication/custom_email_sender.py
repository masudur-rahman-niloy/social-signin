from urllib import parse
from auth_utils import add_db_confirmation_item
from global_utils import add_msg_to_sqs, get_sqs_email_msg, decrypt_code, DEFAULT_FRONTEND_BASE_URL
from model_dataclass.auth_model import ConfirmationCodeModel
from model_dataclass.constants import EMAIL_MEDIUM, COGNITO_USER_ID_ATTRIBUTE

trigger_source_list = [
    "CustomEmailSender_SignUp",
    "CustomEmailSender_ResendCode",
    "CustomEmailSender_ForgotPassword",
    "CustomEmailSender_AdminCreateUser",
    "CustomEmailSender_VerifyUserAttribute"
]


def lambda_handler(event, context):
    try:        
        trigger = event["triggerSource"]
        if trigger in trigger_source_list:
            frontend_base_url = DEFAULT_FRONTEND_BASE_URL
            if event.get('request').get('clientMetadata') is not None:
                print('frontend_base_url available')
                frontend_base_url = event.get('request').get('clientMetadata').get('FRONTEND_BASE_URL', DEFAULT_FRONTEND_BASE_URL)

            if 'email' not in event['request']['userAttributes']:
                return event

            print('email available')
            email = event['request']['userAttributes']['email']
            custom_user_id = event['request']['userAttributes'].get(COGNITO_USER_ID_ATTRIBUTE)
            name = event['request']['userAttributes'].get('name', "Unknown")
            code = event['request']['code']
            print("name ",name)
            print("code ",code)
            decrypted_code = decrypt_code(code)
            print('decrypted code: ', decrypted_code)

            template_name = 'User_Registration'
            template_data = {}

            if trigger == "CustomEmailSender_ForgotPassword":
                link = f"{frontend_base_url}/reset-password/?email={email}&code={parse.quote(decrypted_code)}"
                template_name = 'forgot_password_template'  
                template_data['link'] = link
                print("CustomEmailSender_ForgotPassword : ", template_data)
            
            elif trigger == "CustomEmailSender_AdminCreateUser":
                link = f"{frontend_base_url}/signin/?type=admin_signup&username={email}&code={parse.quote(decrypted_code)}"
                template_name = 'admin_signup_template'
                template_data['name'] = name
                template_data['username'] = email
                template_data['code'] = decrypted_code
                template_data['link'] = link
                print("CustomEmailSender_AdminCreateUser : ", template_data)
            elif trigger == "CustomEmailSender_VerifyUserAttribute":
                link = f"{frontend_base_url}/signin/?type=verify_attribute&username={email}&code={parse.quote(decrypted_code)}"
                template_name = 'verify_attribute_template'
                template_data['name'] = name
                template_data['username'] = email
                template_data['code'] = decrypted_code
                template_data['link'] = link
                print("CustomEmailSender_VerifyUserAttribute : ", template_data)
                
            else:
                # link = f"{frontend_base_url}/profile?userid={user_id}&code={decrypted_code}&email={email}"
                link = f"{frontend_base_url}/confirm-signup/?email={email}&code={parse.quote(decrypted_code)}"
                template_name = 'regular_signup_template'
                template_data['name'] = name
                template_data['link'] = link
            
                print("else template_data: ", template_data)
            response = add_msg_to_sqs(get_sqs_email_msg(
                    target=email,
                    email_type='template',
                    data={
                        'template_name': template_name,
                        'template_data': template_data,
                    }
                )
            )
            print("sqs response: ", response)
            confirmation_item = ConfirmationCodeModel(userId=custom_user_id, code=decrypted_code, destination=email,
                                                      medium=EMAIL_MEDIUM)
            db_response = add_db_confirmation_item(confirmation_item)

            return event
        else:
            raise Exception('Invalid trigger source')
        
    except Exception as e:
        print("Failed")
        print(e)
        print("================")
        raise Exception(str(e))




