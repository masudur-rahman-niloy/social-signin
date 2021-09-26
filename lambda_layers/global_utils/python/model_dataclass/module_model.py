import json
import time
from copy import deepcopy
from typing import List, Optional, Any
from aws_lambda_powertools.utilities.parser import validator, root_validator, Field
from aws_lambda_powertools.utilities.parser.pydantic import constr
from pydantic import BaseModel


class ModuleModel(BaseModel):
    module_name: constr(min_length=3)
    add_api: constr(min_length=3)
    update_api: constr(min_length=3)
    delete_api: constr(min_length=3)
    list_api: constr(min_length=3)
    status: constr(min_length=3)
    module_id: int = None

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        if 'module_id' in attributes:
            del attributes['module_id']

        sql = f"insert into {table_name}({','.join([f'`{attr_name}`' for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        final_sql = sql.rstrip(',') + ');'
        print('sql: ', final_sql)
        return final_sql

