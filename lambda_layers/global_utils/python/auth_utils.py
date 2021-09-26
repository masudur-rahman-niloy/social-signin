import time

from boto3.dynamodb.conditions import Attr
from global_utils import dynamodb_resource, dynamodb_client, primary_table_name, cognito_idp_client, userpool_id, \
    userpool_client_id, connection, get_hashed_value
from model_dataclass.auth_model import ConfirmationCodeModel, CodeValidityModel, HashedPasswordModel, SetPasswordModel, \
    UserModel, SignupModel, AdminSignupModel, ExistingEmailPhoneModel, SubscriptionModel, BlockUnblockUserModel, \
    UserStatModel
from model_dataclass.constants import EMAIL_MEDIUM, PHONE_MEDIUM, USER_PREFIX, EXISTING_EMAIL_PHONE, \
    COGNITO_USERNAME_ATTRIBUTE, COGNITO_USER_STATUS_ATTRIBUTE, AURORA_TABLE_NAMES, COGNITO_FILTER_RESOLVER, \
    DURATION_ALLOWED_EMAIL, DURATION_ALLOWED_PHONE, COGNITO_UNCONFIRMED_STATUS, INSTRUCTOR_ROLE, COGNITO_USER_ID_ATTRIBUTE, \
    INITIAL_ROLE


class UserMatchNotFound(Exception):
    pass


def is_confirmation_code_valid(code_item: ConfirmationCodeModel, parsed_body: CodeValidityModel or SetPasswordModel):
    current_time = int(time.time())
    created_at = int(str(code_item.createdAt))
    db_code = str(code_item.code)

    if db_code != parsed_body.confirmationCode:
        return False, "INVALID_CODE", "Invalid code provided"
    if parsed_body.medium == EMAIL_MEDIUM and (current_time - created_at) > DURATION_ALLOWED_EMAIL:
        return False, "CONFIRMATION_CODE_EXPIRED", "Confirmation code has expired"
    if parsed_body.medium == PHONE_MEDIUM and (current_time - created_at) > DURATION_ALLOWED_PHONE:
        return False, "CONFIRMATION_CODE_EXPIRED", "Confirmation code has expired"

    return True, "CODE_VALID", "Confirmation code is valid"


def get_bulk_signup_response(error=True, code="GENERIC", message="Error!", data={}):
    return {
        "error": error,
        "code": code,
        "message": message,
        "data": data
    }


def get_provider_from_username(username):
    if username.startswith('Facebook_'):
        return 'FACEBOOK'
    elif username.startswith('Google_'):
        return 'GOOGLE'
    elif username.startswith('Auth0_'):
        return 'AUTH0'

    return 'REGULAR'


def parse_cognito_user_dict(attributes):
    cognito_user = {}
    for item in attributes:
        cognito_user[item['Name']] = item['Value']
    return cognito_user


def get_email_phone(parsed_body):
    email_phone = {}
    if parsed_body.medium == EMAIL_MEDIUM:
        email_phone['email'] = parsed_body.emailOrPhone
        email_phone['phone'] = ""
    else:
        email_phone['phone'] = parsed_body.emailOrPhone
        email_phone['email'] = ""
    return email_phone


def get_username_from_medium(parsed_body):
    if parsed_body.medium == 'email':
        return get_username_from_email(parsed_body.emailOrPhone)
    else:
        return get_username_from_phone(parsed_body.emailOrPhone)


def get_username_from_email(email):
    # re.sub(r"@|(.com)", "", "asadullahgalib13@gmail.com")
    # this can be used to replace @ and .com
    # asadullahgalib13@gmail.com => asadullahgalib13gmail

    return email.replace('@', '')


def get_username_from_phone(phone):
    # prev version
    # phone.replace('+', '')

    return f"phone_{phone}"


def get_db_hash_item(userId):
    dummy_password_item: HashedPasswordModel = HashedPasswordModel(userId=userId)
    table = dynamodb_resource.Table(primary_table_name)
    db_response = table.get_item(
        Key={
            "PK": dummy_password_item.PK,
            "SK": dummy_password_item.SK,
        }
    )
    return db_response.get('Item')


def get_reuse_db_limit_item():
    table = dynamodb_resource.Table(primary_table_name)
    db_response = table.get_item(
        Key={
            "PK": "SETTINGS",
            "SK": "REUSE#PASSWORD#LIMIT",
        }
    )
    return db_response.get('Item')


def update_password_item(user_id, new_passwords):
    transaction_items = []
    password_model: HashedPasswordModel = HashedPasswordModel(userId=user_id,
                                                              passwords=new_passwords)
    print('password_item: ', password_model.as_dynamodb_json())
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': password_model.as_dynamodb_json()
        }
    })

    response = dynamodb_client.transact_write_items(
        TransactItems=transaction_items
    )
    return response


def email_phone_exists(parsed_body: SignupModel or AdminSignupModel) -> bool:
    response = dynamodb_client.get_item(
        TableName=primary_table_name,
        Key={
            "PK": {"S": EXISTING_EMAIL_PHONE},
            "SK": {"S": f"{parsed_body.emailOrPhone}"},
        }
    )

    return "Item" in response


def add_db_confirmation_item(confirmation_item):
    table = dynamodb_resource.Table(primary_table_name)
    response = table.put_item(Item=confirmation_item.dict())
    return response


def get_cognito_user_by_email_phone(find_text="", medium=EMAIL_MEDIUM, user_pool_id=userpool_id):
    filter_str = f"{COGNITO_FILTER_RESOLVER.get(medium)}=\"{find_text}\""
    print("filter_str: ", filter_str)
    cognito_response = cognito_idp_client.list_users(
        UserPoolId=user_pool_id,
        # Limit=0,  # limit=1 to get single user does not work
        Filter=filter_str
    )
    print("cognito_response: ", cognito_response)

    if len(cognito_response.get("Users", [])) == 0:
        raise UserMatchNotFound('No user found with provided email/phone!')

    if len(cognito_response.get("Users", [])) != 1:
        raise Exception(f"Invalid {medium} provided!")

    response_user = cognito_response.get("Users")[0]
    print('response_user: ', response_user)
    cognito_user = parse_cognito_user_dict(response_user['Attributes'])
    cognito_user[COGNITO_USERNAME_ATTRIBUTE] = response_user.get('Username')
    cognito_user[COGNITO_USER_STATUS_ATTRIBUTE] = response_user.get('UserStatus')
    print("cognito user: ", cognito_user)
    return cognito_user


def get_confirmation_code(userId):
    dummy_confirmation_item = ConfirmationCodeModel(userId=userId, code="123456", destination="test@test.com",
                                                    medium='email')
    table = dynamodb_resource.Table(primary_table_name)
    db_response = table.get_item(
        Key={
            "PK": dummy_confirmation_item.PK,
            "SK": dummy_confirmation_item.SK,
        }
    )
    return db_response.get("Item")


def confirm_signup(username, confirmationCode):
    confirmation_response = cognito_idp_client.confirm_sign_up(
        ClientId=userpool_client_id,
        Username=username,
        ConfirmationCode=confirmationCode
    )
    return confirmation_response


def add_user_to_group(username, user_role, user_pool_id=userpool_id):
    add_user_group_response = cognito_idp_client.admin_add_user_to_group(
        GroupName=user_role,
        UserPoolId=user_pool_id,
        Username=username
    )
    return add_user_group_response


def add_dynamo_user(user_model: UserModel, parsed_body: SignupModel or AdminSignupModel, is_admin_created=False):
    if is_admin_created:
        user_model.as_aurora_admin_created_user()

    transaction_items = []
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': user_model.as_dynamodb_json()
        }
    })

    existing_email_phone_item: ExistingEmailPhoneModel = ExistingEmailPhoneModel(emailOrPhone=parsed_body.emailOrPhone,
                                                                                 medium=parsed_body.medium,
                                                                                 **user_model.dict())

    print('existing_email_phone_item: ', existing_email_phone_item.as_dynamodb_json())
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': existing_email_phone_item.as_dynamodb_json()
        }
    })

    # add hashed password only for regular signup where password is available
    if not is_admin_created:
        password_item: HashedPasswordModel = HashedPasswordModel(userId=user_model.userId,
                                                                 passwords=[get_hashed_value(parsed_body.password)])
        print('password_item: ', password_item.as_dynamodb_json())
        transaction_items.append({
            'Put': {
                'TableName': primary_table_name,
                'Item': password_item.as_dynamodb_json()
            }
        })

    subscription: SubscriptionModel = SubscriptionModel(user_id=user_model.userId,
                                                        receivePromotionalContent=user_model.receivePromotionalEmail)

    print('subscription: ', subscription.to_dynamodb_client_format())
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': subscription.to_dynamodb_client_format()
        }
    })

    user_stat_model: UserStatModel = UserStatModel(user_id=user_model.userId)
    print('user_stat_model: ', user_stat_model.as_dynamodb_json())
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': user_stat_model.as_dynamodb_json()
        }
    })

    response = dynamodb_client.transact_write_items(
        TransactItems=transaction_items
    )
    return response


def is_role_blocked(user):
    roles = [item.strip() for item in user['role'].split(',')]
    blocked_count = 0
    for role in roles:
        role_blocked = f"is{role.title()}Blocked"
        if user.get(role_blocked):
            blocked_count += 1
    return len(roles) == blocked_count


def is_user_blocked(user, user_status):
    print('check user blocked--->>>', user)
    # should users be allowed to signin if role is mentor but not yet approved?
    if user_status == COGNITO_UNCONFIRMED_STATUS:
        return True, 'USER_NOT_CONFIRMED::CODE::User account not confirmed! Check email/sms for account confirmation code'
    if user['isDeleted']:
        return True, 'ACCOUNT_DELETED::CODE::Accont has been deleted'
    if is_role_blocked(user):
        return True, 'ACCOUNT_BLOCKED::CODE::Account is blocked'
    # if user['role'] == 'mentor' and not user['isMentorApproved']:
    #     return True, 'MENTOR_APPROVAL_PENDING::CODE::Pending mentor role approval'

    return False, ''


def get_find_text_from_user_item(user_item):
    return user_item.get(user_item.get("signupMedium"))


def is_already_changed(user_item: dict, parsed_body: BlockUnblockUserModel):
    return user_item.get(f"is{parsed_body.role.capitalize()}Blocked", False) == parsed_body.isBlocked


def update_cognito_profile(cognito_user, identity_id):
    if 'profile' not in cognito_user or cognito_user.get('profile', '') == '':
        print('profile not available, setting...')
        response = cognito_idp_client.admin_update_user_attributes(
            UserPoolId=userpool_id,
            Username=cognito_user.get('username'),
            UserAttributes=[
                {
                    'Name': 'profile',
                    'Value': identity_id
                },
            ],
        )
        print('update profile response: ', response)

        dummy_user_model: UserModel = UserModel(userId=cognito_user.get(COGNITO_USER_ID_ATTRIBUTE), name='test',
                                                signupRole=INITIAL_ROLE, role=INITIAL_ROLE, signupMedium=EMAIL_MEDIUM)
        table = dynamodb_resource.Table(primary_table_name)
        db_response = table.update_item(
            Key={
                "PK": dummy_user_model.PK,
                "SK": dummy_user_model.SK,
            },
            ConditionExpression=Attr('PK').exists() & Attr('SK').exists(),
            UpdateExpression="SET profile = :cognitoProfile",
            ExpressionAttributeValues={
                ":cognitoProfile": identity_id
            },
        )
        print('update profile db_response: ', db_response)

        return identity_id
    else:
        print('profile already present: ', cognito_user.get('profile'))
        return cognito_user.get('profile')








