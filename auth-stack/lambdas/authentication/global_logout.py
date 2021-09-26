from aws_lambda_powertools.utilities.parser import parse, ValidationError
from global_utils import logger, tracer, get_formatted_validation_error, cognito_idp_client, \
    get_response, de_coloned_error
from model_dataclass.auth_model import LogoutModel

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        parsed_body: LogoutModel = parse(event=event['body'], model=LogoutModel)
        db_response = cognito_signout_user(parsed_body.accessToken)
        return get_response(
            status=200,
            error=False,
            code="USER_LOGGED_OUT",
            message="Logged out",
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
    except Exception as e:
        print(e)
        return get_response(
            status=400,
            error=True,
            message=de_coloned_error(str(e)),
        )


def cognito_signout_user(access_token):
    signout_user_response = cognito_idp_client.global_sign_out(
        AccessToken=access_token
    )
    return signout_user_response
