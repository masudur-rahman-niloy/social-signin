from global_utils import get_db_user
from model_dataclass.constants import COGNITO_USER_ID_ATTRIBUTE
from auth_utils import is_user_blocked


def lambda_handler(event, context):
    print(event)
    
    try:
        user_id = event['request']['userAttributes'].get(COGNITO_USER_ID_ATTRIBUTE)
        user_status = event['request']['userAttributes']['cognito:user_status']

        user_item = get_db_user(user_id)
        print('user_item: ', user_item)
        
        if user_status == "EXTERNAL_PROVIDER":
            print('inside external provider')
            if user_item is not None:
                return event
            else:
                raise Exception("Account does not exist for social signin. Please try regular login.")

        else:
            print('inside NON external provider')
            if user_item is not None:

                blocked, msg = is_user_blocked(user_item, user_status)
                if blocked:
                    raise Exception(msg)
                return event
            else:
                raise Exception("USER_NOT_FOUND::CODE::No user found with provided email/phone!")
    
    except Exception as error:
        raise Exception(f"::PREAUTHENTICATION::{str(error)}")


