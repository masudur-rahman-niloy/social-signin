import base64
import decimal
import hashlib
import json
import os
import time
from datetime import datetime, date
from typing import List

import aws_encryption_sdk
import boto3
import pymysql
from aws_encryption_sdk.identifiers import CommitmentPolicy
from aws_lambda_powertools import Logger, Tracer, Metrics
from logging import INFO
from ksuid import ksuid
from model_dataclass.auth_model import UserModel

from os.path import join, exists, getmtime

# ========================== Aurora ==========================
from model_dataclass.constants import EMAIL_MEDIUM, INITIAL_ROLE

sm_client = boto3.client('secretsmanager')
db_secret = os.environ.get('AURORA_DB_SECRET', None)
host = os.environ.get('AURORA_CLUSTER_HOST', None)
s3 = boto3.client('s3')
database_name = None

connection = None
dict_connection = None

if db_secret:
    sm_response = sm_client.get_secret_value(SecretId=db_secret)
    secret = json.loads(sm_response['SecretString'])
    database_name = secret['dbname']
    connection = pymysql.connect(host=host, user=secret['username'], password=secret['password'],
                                 database=secret['dbname'], connect_timeout=5)
    dict_connection = pymysql.connect(
        host=host,
        user=secret['username'],
        password=secret['password'],
        database=secret['dbname'],
        connect_timeout=5,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    print(connection)

# ========================== Powertools ==========================
logger = Logger()
tracer = Tracer()
metrics = Metrics()

logger.setLevel(INFO)


def get_formatted_validation_error(e):
    errors = []
    for err in e.errors():
        errors.append(f"{err['loc'][0]}: {err['msg']}")

    return ','.join(errors)


def get_transaction_code_msg(cancellation_reasons, not_found_data):
    if len(cancellation_reasons) != len(not_found_data):
        raise Exception('Cancellation reasons do not match with code/message data')

    print('cancellation_reasons: ', cancellation_reasons)
    code, msg = "TRANSACTION_ERROR", "Transaction error!"
    for reason, code_msg_data in zip(cancellation_reasons, not_found_data):
        if reason['Code'] != 'None':
            code, msg = code_msg_data.get('code', code), code_msg_data.get('msg', reason.get('Message'))
            break

    return code, msg


# ========================== Global variables ==========================

DEFAULT_FRONTEND_BASE_URL = "https://localhost.com"  # it should be our admin panel url
AUTH0_BASE_URL = 'https://dev-oenomb77.us.auth0.com'

# ========================== boto3 clients & resources ==========================
sqs_client = boto3.client('sqs')
s3_client = boto3.client('s3')
ses_client = boto3.client('ses')
dynamodb_client = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')
cognito_idp_client = boto3.client('cognito-idp')
cognito_identity_client = boto3.client('cognito-identity')
kms_client = boto3.client('kms')
iam_client = boto3.client('iam')
pinpoint = boto3.client('pinpoint')
application_id = os.environ.get('APPLICATION_ID')
segment_id = os.environ.get('SEGMENT_ID')
# ========================== environment variables ==========================
sqs_queue_url = os.environ.get('SQS_URL', None)
pinpoint_queue_url = os.environ.get('PINPOINT_QUEUE_URL', None)
userpool_id = os.environ.get('USER_POOL_ID', None)
userpool_client_id = os.environ.get('USER_POOL_CLIENT_ID', None)
identity_pool_id = os.environ.get('IDENTITY_POOL_ID', None)
primary_table_name = os.environ.get('Primary_Table', None)
secondary_table_name = os.environ.get('SECONDARY_TABLE', None)
# custom_key_id = os.environ['CUSTOM_KEY_ID']
custom_key_arn = os.environ.get('CUSTOM_KEY_ARN', None)
region = os.environ.get('AWS_REGION', None)
stage_name = os.environ.get('STAGE_NAME', None)

if custom_key_arn:
    encryption_client = aws_encryption_sdk.EncryptionSDKClient(
        commitment_policy=CommitmentPolicy.FORBID_ENCRYPT_ALLOW_DECRYPT)
    kms_key_provider = aws_encryption_sdk.StrictAwsKmsMasterKeyProvider(key_ids=[
        custom_key_arn,
    ])


def decrypt_code(code):
    decrypted_plaintext, decryptor_header = encryption_client.decrypt(
        source=base64.b64decode(code),
        key_provider=kms_key_provider
    )
    return decrypted_plaintext.decode()


# ========================== SES email frontend site URL resolver ==========================
frontend_urls = {
    'dev': {
        'admin': "https://localhost.com/admin",
        'client': "https://localhost.com",
        'backend': "https://ylh8equg5d.execute-api.us-west-2.amazonaws.com/dev"
    },
    'qa': {
        'admin': "https://olsaadminqa.shadintech.com",
        'client': "https://olsaclientqa.shadintech.com",
        'backend': "https://olsaapi.shadintech.com/qa"
    },
    'stage': {
        'admin': "https://olsaadminstage.shadintech.com",
        'client': "https://olsaclientstage.shadintech.com",
        'backend': "https://olsaapi.shadintech.com/stage"
    }
}


def get_frontend_urls():
    print("stage_name", stage_name)
    return frontend_urls.get(stage_name, frontend_urls.get('qa'))


# ========================== SQS functions ==========================
def get_sqs_sms_msg(target="+8801709145454", sms_message="Test SMS sent using SQS"):
    return {
        'message_type': {
            'DataType': 'String',
            'StringValue': 'sms'
        },
        'target': {
            'DataType': 'String',
            'StringValue': target
        },
        'sms_message': {
            'DataType': 'String',
            'StringValue': sms_message
        },
    }


def get_sqs_email_msg(target="asadullahgalib13@gmail.com", email_type="custom", data={}):
    # email_type = template/custom
    if email_type == 'custom':
        email_subject = data.get('email_subject', 'Test Email')
        email_body_text = data.get('email_body_text', 'Test Email')
        email_body_html = data.get('email_body_html', 'Test Email')

        # if data.get('event', 'registration') == 'registration':
        #     body = """
        #         Welcome to CodersTrust app!
        #         """
        #     email_subject = "Welcome to CodersTrust app!"
        #     email_BodyText = body
        #     emailBodyHtml = body

        return {
            'message_type': {
                'DataType': 'String',
                'StringValue': 'email'
            },
            'target': {
                'DataType': 'String',
                'StringValue': target
            },
            'email_type': {
                'DataType': 'String',
                'StringValue': email_type
            },
            'email_subject': {
                'DataType': 'String',
                'StringValue': email_subject
            },
            'email_body_text': {
                'DataType': 'String',
                'StringValue': email_body_text
            },
            'email_body_html': {
                'DataType': 'String',
                'StringValue': email_body_html
            },
            # 'testVal': {
            #     'DataType': 'Number',
            #     'StringValue': body['age']
            # }
        }
    else:
        return {
            'message_type': {
                'DataType': 'String',
                'StringValue': 'email'
            },
            'target': {
                'DataType': 'String',
                'StringValue': target
            },
            'email_type': {
                'DataType': 'String',
                'StringValue': email_type
            },
            'template_name': {
                'DataType': 'String',
                'StringValue': data.get('template_name', 'User_Registration')
            },
            'template_data': {
                'DataType': 'String',
                'StringValue': json.dumps(data.get('template_data', {}))
            },
            # 'testVal': {
            #     'DataType': 'Number',
            #     'StringValue': body['age']
            # }
        }


def add_msg_to_sqs(msg_attr, queue_url=sqs_queue_url):
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        DelaySeconds=5,
        MessageAttributes=msg_attr,
        MessageBody=('sms/email sender')
    )
    return response


# ========================== Generic response ==========================
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        # should float be used? rounding, precision issues
        # return float(obj)
        return str(obj)
    if isinstance(obj, date):
        return str(obj)
    raise TypeError


def get_hashed_value(password):
    # not yet production ready
    return str(hashlib.sha224(password.encode('utf-8')).hexdigest())


def get_response(status=400, error=True, code="GENERIC", message="NA", data={}, headers={}):
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    final_headers = {**default_headers, **headers}
    return {
        "statusCode": status,
        "headers": final_headers,
        "body": json.dumps({
            "error": error,
            "code": code,
            "message": message,
            "data": data
        }, default=decimal_default),
    }


def de_coloned_error(error):
    if ":" in error:
        error = error.split(":")[1].strip()
    return error


# ========================== Help & support ==========================
# following util function can be moved to the stack utils
def get_support_cancellation_code_msg(cancellation_reasons, not_found_data):
    code, msg = "TRANSACTION_ERROR", "Transaction error!"
    if cancellation_reasons[0]['Code'] != 'None':
        code, msg = not_found_data['code'], not_found_data['msg']
    elif cancellation_reasons[1]['Code'] != 'None':
        msg = cancellation_reasons[1].get('Message', "NA")

    return code, msg


def create_support_ticket(user_id, body):
    support_id = str(ksuid())
    created_at = int(time.time())
    transaction_items = []

    transaction_items.append({
        'ConditionCheck': {
            'TableName': primary_table_name,
            'Key': {
                "PK": {'S': f"#USER#{user_id}"},
                "SK": {'S': f"#USER#{user_id}"},
            },
            "ConditionExpression": "attribute_exists(PK)",
        }
    })

    support_item = {
        "PK": {'S': f"#USER#{user_id}"},
        "SK": {'S': f"#SUPPORT#{support_id}"},
        "support_id": {'S': support_id},
        "topic": {'S': body.get('topic', "NA")},
        "created_at": {'N': f"{created_at}"},
        "assigned_to": {'S': body.get('assignedTo', "NA")},
        "status": {'S': body.get('status', "NA")},
        "GSI1PK": {'S': f"#STATUS#{body.get('status', 'NA')}"},
        "GSI1SK": {'S': f"#CREATED_AT#{created_at}"},
        "GSI2PK": {'S': f"#ASSIGNED_TO#{body.get('assignedTo', 'NA')}"},
        "GSI2SK": {'S': f"#UPDATED_AT#{body.get('status', 'NA')}#{created_at}"},
    }
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': support_item
        }
    })

    response = dynamodb_client.transact_write_items(
        TransactItems=transaction_items
    )
    return response


def create_ticket_details(user_id, support_id, body):
    created_at = int(time.time())
    transaction_items = []

    # transaction_items.append({
    #     'ConditionCheck': {
    #         'TableName': primary_table_name,
    #         'Key': {
    #             "PK": {'S': f"#USER#{user_id}"},
    #             "SK": {'S': f"#SUPPORT#{support_id}"},
    #         },
    #         "ConditionExpression": "attribute_exists(PK)",
    #     }
    # })

    details_item = {
        "PK": {'S': f"#SUPPORT#{support_id}"},
        "SK": {'S': f"{created_at}"},
        "support_id": {'S': support_id},
        "message": {'S': body.get('message', 'NA')},
        "created_at": {'N': f"{created_at}"},
        "created_by": {'S': user_id},
        "status": {'S': body.get('status', 'NA')},
    }
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': details_item
        }
    })

    transaction_items.append({
        'Update': {
            'TableName': primary_table_name,
            'Key': {
                "PK": {'S': f"#USER#{user_id}"},
                "SK": {'S': f"#SUPPORT#{support_id}"},
            },
            "ConditionExpression": "attribute_exists(PK)",
            "UpdateExpression": "SET #ticket_status = :tckt_Status, GSI1PK = :tckt_Status, GSI2SK = :updated_at",
            "ExpressionAttributeNames": {
                "#ticket_status": "status"
            },
            "ExpressionAttributeValues": {
                ":tckt_Status": {'S': f"#STATUS#{body.get('status', 'NA')}"},
                ":updated_at": {'S': f"#UPDATED_AT#{body.get('status', 'NA')}#{created_at}"},
            }
        }
    })

    response = dynamodb_client.transact_write_items(
        TransactItems=transaction_items
    )
    return response


def create_support_ticket_details(user_id, body):
    support_id = str(ksuid())
    created_at = int(time.time())
    transaction_items = []

    dummy_user_model: UserModel = UserModel(userId=user_id, name='test',
                                            signupRole=INITIAL_ROLE, role=INITIAL_ROLE, signupMedium=EMAIL_MEDIUM)

    transaction_items.append({
        'ConditionCheck': {
            'TableName': primary_table_name,
            'Key': {
                "PK": {'S': dummy_user_model.PK},
                "SK": {'S': dummy_user_model.SK},
            },
            "ConditionExpression": "attribute_exists(PK)",
        }
    })

    support_item = {
        "PK": {'S': f"#USER#{user_id}"},
        "SK": {'S': f"#SUPPORT#{support_id}"},
        "support_id": {'S': support_id},
        "topic": {'S': body.get('topic', "NA")},
        "created_at": {'N': f"{created_at}"},
        "assigned_to": {'S': body.get('assignedTo', "NA")},
        "status": {'S': body.get('status', "NA")},
        "GSI1PK": {'S': f"#STATUS#{body.get('status', 'NA')}"},
        "GSI1SK": {'S': f"#CREATED_AT#{created_at}"},
        "GSI2PK": {'S': f"#ASSIGNED_TO#{body.get('assignedTo', 'NA')}"},
        "GSI2SK": {'S': f"#UPDATED_AT#{body.get('status', 'NA')}#{created_at}"},
    }
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': support_item
        }
    })

    details_item = {
        "PK": {'S': f"#SUPPORT#{support_id}"},
        "SK": {'S': f"{created_at}"},
        "support_id": {'S': support_id},
        "message": {'S': body.get('message', 'NA')},
        "created_at": {'N': f"{created_at}"},
        "created_by": {'S': user_id},
        "status": {'S': body.get('status', 'NA')},
    }
    transaction_items.append({
        'Put': {
            'TableName': primary_table_name,
            'Item': details_item
        }
    })

    response = dynamodb_client.transact_write_items(
        TransactItems=transaction_items
    )
    return support_id


def get_db_user(user_id):
    """
    Returns user item
    """
    dummy_user_model: UserModel = UserModel(userId=user_id, name='test',
                                            signupRole=INITIAL_ROLE, role=INITIAL_ROLE, signupMedium=EMAIL_MEDIUM)
    table = dynamodb_resource.Table(primary_table_name)
    print("dummy_user_model.PK: ", dummy_user_model.PK)
    db_response = table.get_item(
        Key={
            "PK": dummy_user_model.PK,
            "SK": dummy_user_model.SK,
        }
    )
    print("get_db_user: ", db_response)
    return db_response.get('Item')


def get_db_item(pk, sk, table_name=primary_table_name):
    table = dynamodb_resource.Table(table_name)
    db_response = table.get_item(
        Key={
            "PK": pk,
            "SK": sk,
        }
    )
    return db_response.get('Item')


def query_db_item(pk=None, sk=None, sk_begins_with=True, table_name=primary_table_name):
    if pk is None:
        raise Exception("Invalid query parameter")

    table = dynamodb_resource.Table(table_name)
    if sk is not None:
        condition_expression = f"PK = :itemId{' AND begins_with(SK, :sk_value)' if sk_begins_with else ' AND SK = :sk_value'}"
        attr_values = {
            ":itemId": pk,
            ":sk_value": sk,
        }
    else:
        condition_expression = "PK = :itemId"
        attr_values = {
            ":itemId": pk,
        }
    db_response = table.query(
        KeyConditionExpression=condition_expression,
        ExpressionAttributeValues=attr_values,
    )
    return db_response.get('Items', [])


def simple_read(condition, table):
    dict_connection.begin()
    result = {}
    if condition:
        with dict_connection.cursor() as cur:
            sql = f"Select * from {table} where {condition}"
            print("sql: ", sql)
            cur.execute(sql)
            signle_result = cur.fetchone()
            print("signle_result: ", signle_result)

            if signle_result is not None:
                result = signle_result
                print("result ", result)
    return result


def simple_read_multiple(condition, table):
    dict_connection.begin()
    result = {}
    if condition:
        with dict_connection.cursor() as cur:
            sql = f"Select * from {table} where {condition}"
            print("sql: ", sql)
            cur.execute(sql)
            multiple_result = cur.fetchall()

            print("multiple_result: ", multiple_result)
            if multiple_result is not None:
                result = multiple_result
                print("result ", result)
    return result


def read_all_data(table, query_condition=""):
    dict_connection.begin()
    result = {}

    with dict_connection.cursor() as cur:
        sql = f"Select * from {table} {query_condition}"
        print("sql: ", sql)
        cur.execute(sql)
        multiple_result = cur.fetchall()

        print("multiple_result: ", multiple_result)
        if multiple_result is not None:
            result = multiple_result
            print("result ", result)
    return result


# ==========================  ==========================

# ==========================  ==========================

# ==========================  ==========================

# Custom exceptions


class PaymentNotCompletedException(Exception):
    pass


class PaymentFailedException(Exception):
    pass


def update_pinpoint_endpoint(**parsed_body):
    try:
        response = pinpoint.update_endpoint(
            ApplicationId=application_id,
            EndpointId=parsed_body.get('endpoint_address'),
            EndpointRequest={
                'Address': parsed_body.get('endpoint_address'),
                'ChannelType': parsed_body.get('channel_type'),
                'Attributes': {
                    'role': [
                        str(parsed_body.get('role'))
                    ]
                },
                'User': {
                    'UserId': parsed_body.get('user_id')
                }
            }
        )
        print('update endpoint response', response)

    except Exception as e:
        print(e)

