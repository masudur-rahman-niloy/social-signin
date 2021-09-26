import json
import time
from copy import deepcopy
from typing import List, Optional, Any
from aws_lambda_powertools.utilities.parser import validator, root_validator, Field
from aws_lambda_powertools.utilities.parser.pydantic import constr
from pydantic import BaseModel


class CurrencyModel(BaseModel):
    country: constr(min_length=2)
    currency_name: constr(min_length=2)
    symbol: constr(min_length=1, max_length=2)
    conversion_rate: float = 0.0
    status: bool = False
    id: int = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        self.conversion_rate = round(self.conversion_rate, 2)
        print('end of init')

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        if 'id' in attributes:
            del attributes['id']

        sql = f"insert into {table_name}({','.join([f'`{attr_name}`' for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        final_sql = sql.rstrip(',') + ');'
        print('sql: ', final_sql)
        return final_sql

