from auth_utils import parse_cognito_user_dict, get_provider_from_username, update_cognito_profile
from aws_lambda_powertools.utilities.parser import parse, ValidationError
from global_utils import logger, tracer, get_formatted_validation_error, dynamodb_resource, cognito_idp_client, \
    userpool_id, region, identity_pool_id, cognito_identity_client, get_response, de_coloned_error, \
    get_db_user
from model_dataclass.auth_model import SocialSigninModel
from model_dataclass.constants import COGNITO_USER_ID_ATTRIBUTE


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        parsed_body: SocialSigninModel = parse(event=event['body'], model=SocialSigninModel)
        account_id = event['requestContext']['accountId']

        user_response = cognito_idp_client.get_user(
            AccessToken=parsed_body.access_token
        )
        print('cognito response: ', user_response)
        cognito_user = parse_cognito_user_dict(user_response['UserAttributes'])
        print("cognito_user: ", cognito_user)

        login_param = f"cognito-idp.{region}.amazonaws.com/{userpool_id}"
        id_response = cognito_identity_client.get_id(
            AccountId=account_id,
            IdentityPoolId=identity_pool_id,
            Logins={
                login_param: parsed_body.id_token
            }
        )
        identity_id = id_response['IdentityId']
        print("Identity ID: ", identity_id)
        resp = cognito_identity_client.get_credentials_for_identity(
            IdentityId=identity_id,
            Logins={
                login_param: parsed_body.id_token
            },
        )
        print("resp", resp)

        dynamo_user = get_db_user(cognito_user.get(COGNITO_USER_ID_ATTRIBUTE))
        if dynamo_user is None:
            dynamo_user = {}

        # set cognito profile
        cognito_profile = ""
        try:
            cognito_profile = update_cognito_profile(cognito_user, identity_id)
        except Exception as e:
            print('error while updating cognito profile')
            print(e)


        token_response = {
            "myEmail": dynamo_user.get('email', ''),
            "myPhone": dynamo_user.get('phone', ''),
            "userId": cognito_user.get(COGNITO_USER_ID_ATTRIBUTE),
            "name": dynamo_user.get('name', ''),
            "profile": cognito_profile,
            "role": dynamo_user.get('role', '').split(','),
            "profile_picture": dynamo_user.get('profile_picture', ''),
            "idToken": parsed_body.id_token,
            "accessToken": parsed_body.access_token,
            "refreshToken": parsed_body.refresh_token,
            "expiresIn": parsed_body.expires_in,
            "tokenType": parsed_body.token_type,
            "accessKey": resp['Credentials']['AccessKeyId'],
            "secretKey": resp['Credentials']['SecretKey'],
            "sessionToken": resp['Credentials']['SessionToken'],
            "signinSource": get_provider_from_username(user_response.get("Username", "")),
        }

        return get_response(
            status=200,
            error=False,
            message="Sign in successful",
            data=token_response
        )
    except ValidationError as e:
        logger.warn(e)
        return get_response(
            status=400,
            error=True,
            code="VALIDATION_ERROR",
            message=get_formatted_validation_error(e),
        )
    except cognito_idp_client.exceptions.UserNotFoundException as e:
        print(e)
        return get_response(
            status=400,
            error=True,
            code="USER_NOT_FOUND",
            message="No user found with provided email/phone!",
        )
    except cognito_idp_client.exceptions.UserNotConfirmedException as e:
        print(e)
        return get_response(
            status=400,
            error=True,
            code="USER_NOT_CONFIRMED",
            message="User account not confirmed! Check email/sms for account confirmation code",
        )
    except cognito_idp_client.exceptions.TooManyRequestsException as e:
        print(e)
        return get_response(
            status=400,
            error=True,
            code="TOO_MANY_REQUESTS",
            message="Request limit exceeded! Please retry after a short while",
        )
    except cognito_idp_client.exceptions.NotAuthorizedException as e:
        print(e)
        return get_response(
            status=400,
            error=True,
            code="SIGNIN_NOT_AUTHORIZED",
            message="Incorrect username or password",
        )
    except Exception as e:
        # Send some context about this error to Lambda Logs
        # send specific message code, type
        # if unverified email/phone is used, returned error is 'User does not exist'
        print(e)

        if de_coloned_error(str(e)) == 'The ambiguous role mapping rules for':
            return get_response(
                status=400,
                error=True,
                code='SOCIAL_LOGIN_ROLE_BLOCKED',
                message='This account is blocked',
                data={
                    "signinSource": get_provider_from_username(user_response.get("Username", "")),
                },
            )

        error = str(e)
        if '::PREAUTHENTICATION::' in error:
            code_msg = error.split('::PREAUTHENTICATION::')[1]
            code = msg = code_msg
            if '::CODE::' in code_msg:
                code = code_msg.split('::CODE::')[0]
                msg = code_msg.split('::CODE::')[1]
            
            return get_response(
                status=400,
                error=True,
                code=code,
                message=msg,
            )
        return get_response(
            status=400,
            error=True,
            message=de_coloned_error(str(e)),
        )

