import json
import time
from copy import deepcopy
from typing import Any
from aws_lambda_powertools.utilities.parser.pydantic import constr
from pydantic import BaseModel


class EmailTemplateModel(BaseModel):
    displayName: constr(min_length=3)
    templateName: constr(min_length=3)
    subject: constr(min_length=3)
    body: constr(min_length=3)
    text: constr(min_length=3)
    id: int = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        self.templateName = self.templateName.replace(" ", "_").lower()
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

