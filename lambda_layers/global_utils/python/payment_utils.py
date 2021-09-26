import json
from typing import List

import backoff
from boto3.dynamodb.conditions import Key
from global_utils import \
    dynamodb_resource, primary_table_name, dict_connection, logger, PaymentNotCompletedException, \
    PaymentFailedException, secondary_table_name

from model_dataclass.payment_model import PaymentModel, TRANSACTION_PREFIX
from model_dataclass.constants import PAYMENT_PROCESSING_COMPLETED, PAYMENT_PROCESSING_FAILED, PAYMENT_REASON_PREFIX
from pydantic import parse_obj_as

table_name = 'payments'


def get_db_course(course):
    table = dynamodb_resource.Table(primary_table_name)
    db_response = table.get_item(
        Key={
            "PK": course.PK,
            "SK": course.SK,
        }
    )
    return db_response.get('Item')


def get_payment_item(transaction_id):
    table = dynamodb_resource.Table(secondary_table_name)
    db_response = table.query(
        KeyConditionExpression="PK = :transactionId",
        ExpressionAttributeValues={
            ":transactionId": f"{TRANSACTION_PREFIX}{transaction_id}",
        },
    )
    print('db response: ', db_response)
    items_len = len(db_response['Items'])
    if items_len == 0 or items_len > 1:
        raise Exception("Invalid transaction id")

    payment_item = PaymentModel(**db_response['Items'][0])
    return payment_item


def get_payment_item_by_email_or_phone(email_or_phone, payment_reason=None) -> List[PaymentModel]:
    if payment_reason is None:
        key_condition_expression = Key('GSI1PK').eq(f"{TRANSACTION_PREFIX}{email_or_phone}")
    else:
        key_condition_expression = Key('GSI1PK').eq(f"{TRANSACTION_PREFIX}{email_or_phone}") & \
                                   Key('GSI1SK').begins_with(f"{PAYMENT_REASON_PREFIX}#{payment_reason}")
    table = dynamodb_resource.Table(secondary_table_name)
    db_response = table.query(
        IndexName='GSI1Search',
        KeyConditionExpression=key_condition_expression
    )
    print('db response: ', db_response)
    items = db_response.get('Items', [])
    if len(items) == 0:
        raise Exception("No payment items were found")
    return parse_obj_as(List[PaymentModel], items)


def update_payment_status(transaction_id, sk, status):
    table = dynamodb_resource.Table(secondary_table_name)
    key = dict(
        PK=f"{TRANSACTION_PREFIX}{transaction_id}",
        SK=sk,
    )
    db_response = table.update_item(
        Key=key,
        UpdateExpression='set payment_status=:payment_status',
        ExpressionAttributeValues={
            ":payment_status": status
        },
    )
    print("update_payment_status", db_response)
    return db_response


def get_payment_gw_info(gw_name):
    with dict_connection.cursor() as cursor:
        sql = f"SELECT * FROM {table_name} WHERE gateway_name=%s"
        cursor.execute(sql, gw_name)
        result = cursor.fetchone()
        print(result)
        configuration_value = result.get('configuration_value')
        if type(configuration_value) is str:
            configuration_value = json.loads(configuration_value)
        return {
            'id': result.get('id'),
            'gateway_name': result.get('gateway_name'),
            'logo': result.get('logo'),
            'configuration_key': result.get('configuration_key'),
            'configuration_value': configuration_value,
            'is_sandbox': result.get('is_sandbox'),
            'sandbox_url': result.get('sandbox_url'),
            'production_url': result.get('production_url'),
            'status': result.get('status')
        }


def get_credentials_from_config(payment_gateway):
    credentials = {}
    for config in payment_gateway.get('configuration_value'):
        credentials[config['key']] = config['value']

    if payment_gateway.get('is_sandbox'):
        return {
            'client_id': credentials.get('sandbox_client_id'),
            'client_secret': credentials.get('sandbox_client_secret'),
        }
    else:
        return {
            'client_id': credentials.get('production_client_id'),
            'client_secret': credentials.get('production_client_secret'),
        }


@backoff.on_exception(backoff.expo, PaymentNotCompletedException, max_time=20)
def check_payment_completed(transaction_id):
    logger.info("Checking payment status")
    payment_item: PaymentModel = get_payment_item(transaction_id)
    if payment_item.payment_status == PAYMENT_PROCESSING_FAILED:
        raise PaymentFailedException('Failed to process payment')
    elif payment_item.payment_status != PAYMENT_PROCESSING_COMPLETED:
        raise PaymentNotCompletedException('Payment Not completed')
