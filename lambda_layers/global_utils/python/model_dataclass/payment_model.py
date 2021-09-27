import json
import time
from copy import deepcopy
from datetime import datetime
from functools import reduce
from typing import List, Any, Optional

from aws_lambda_powertools.utilities.parser import root_validator, Field
from aws_lambda_powertools.utilities.parser.pydantic import constr
from ksuid import ksuid
from pydantic import BaseModel
from model_dataclass.constants import VALID_PAYMENT_REASONS, MEMBERSHIP_PREFIX, PAYMENT_REASON_PREFIX
from dynamodb_json import json_util as dynamodb_json

TRANSACTION_PREFIX = "#TRANSACTION#"

STATUS_LIST = ['incomplete', 'completed']  # 'deleted'
PAYMENT_GATEWAY_TYPE_LIST = ['paypal', 'bkash']
MAX_CART_COURSE = 5


class PaymentModel(BaseModel):
    email_or_phone: constr(min_length=3)
    payment_type: constr(min_length=3)  # gateway used bkash or paypal
    transaction_id: str = None
    payment_status: str = "incomplete"
    payment_amount: int = 0
    payment_date: str = None
    billing_email: constr(min_length=4)
    payment_reason: str = ""
    membership_type: str = ""
    batch: str
    # add paypal order & trans. id
    PK: str = ""
    SK: str = ""
    GSI1PK: str = ""
    GSI1SK: str = ""
    GSI2PK: str = ""
    GSI2SK: str = ""
    GSI3PK: str = ""
    GSI3SK: str = ""

    @root_validator
    def check_payment_status_type(cls, values):
        today = datetime.now()
        batch = values.get('batch')

        print("inside check_payment_status_type")
        payment_status = values.get('payment_status')
        payment_type = values.get('payment_type')
        payment_reason = values.get('payment_reason')
        membership_type = values.get('membership_type')
        payment_amount = values.get('payment_amount')

        if payment_amount > 0 is False:
            raise ValueError("Invalid payment amount")
        if membership_type == "lifetime_member":
            current_year = today.year
            batch = int(batch)
            year_diff = current_year - batch

            if year_diff < 10:
                raise ValueError(f"Life-time member should pass 10 years before applying for this membership")

        if payment_status not in STATUS_LIST:
            raise ValueError("Invalid payment status")
        if payment_type not in PAYMENT_GATEWAY_TYPE_LIST:
            raise ValueError("Invalid payment type")

        if payment_reason not in VALID_PAYMENT_REASONS:
            raise ValueError("Invalid payment reason")

        if membership_type not in MEMBERSHIP_PREFIX.keys():
            raise ValueError("Invalid membership type")
        return values

    # add sep validator for total price from discounted_price

    def __init__(self, **data: Any):
        super().__init__(**data)

        temp_datetime = self.SK
        if self.transaction_id is None:
            self.transaction_id = f"{ksuid()}"
            temp_datetime = str(int(time.time()))

        self.payment_date = self.payment_date if self.payment_date else datetime.now().strftime("%Y-%m-%d")
        self.PK = f"{TRANSACTION_PREFIX}{self.transaction_id}"
        self.SK = temp_datetime
        self.GSI1PK = f"{TRANSACTION_PREFIX}{self.email_or_phone}"
        self.GSI1SK = f"{PAYMENT_REASON_PREFIX}#{self.payment_reason}#{temp_datetime}"
        self.GSI2PK = f"{TRANSACTION_PREFIX}{self.payment_type}"
        self.GSI2SK = temp_datetime
        self.GSI3PK = f"{TRANSACTION_PREFIX}{self.payment_date}"
        self.GSI3SK = self.PK

    def to_dynamodb_client_format(self):
        return dynamodb_json.dumps(self.__dict__)

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print('attributes in sql insert: ', attributes)
        removed_attributes = ['__initialised__', 'PK', "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "GSI3PK", "GSI3SK", "batch"]
        for attribute in removed_attributes:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name} ({','.join([attr_name for attr_name in attributes.keys()])}) values ("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def update_status_statement(self, table_name):
        sql = f"UPDATE {table_name} SET payment_status='{self.payment_status}' WHERE transaction_id='{self.transaction_id}'"
        return sql


class SearchTransactionsParamsModel(BaseModel):
    email_or_phone: constr(min_length=3) = None
    payment_type: constr(min_length=3) = None
    transaction_id: str = None
    payment_status: str = None
    payment_date_start: str = None
    payment_date_end: str = None
    payment_reason: str = None
    membership_type: str = None
    batch: str = None


class SearchTransactionsModel(BaseModel):
    searchParams: SearchTransactionsParamsModel
    page: Optional[constr(min_length=1)] = 1
    limit: Optional[constr(min_length=1)] = 10


class PaymentGatewayModel(BaseModel):
    gateway_name: constr(min_length=3)
    configuration_key: constr(min_length=3)
    configuration_value: Any
    is_sandbox: bool = True
    sandbox_url: str = ""
    production_url: str = ""
    status: constr(min_length=3)
    created_at: str = None
    logo: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.created_at is None:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if type(self.configuration_value) != str:
            self.configuration_value = json.dumps(self.configuration_value)
        print('end of init')

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']

        sql = f"insert into {table_name}({','.join([f'`{attr_name}`' for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        final_sql = sql.rstrip(',') + ');'
        print('sql: ', final_sql)
        return final_sql
