from typing import List
from decimal import Decimal
from enum import Enum


def get_dynamodb_type_value(value):
    val_type = type(value)
    print(f"{value}: {val_type}")
    if isinstance(value, str) or isinstance(value, Enum):
        return {"S": value}
    elif isinstance(value, bool):
        return {"BOOL": value}
    elif isinstance(value, int) or isinstance(value, float) or isinstance(value, Decimal):
        return {"N": str(value)}
    elif isinstance(value, list) or isinstance(value, List):
        return {"L": [get_dynamodb_type_value(v) for v in value]}
    elif isinstance(value, dict):
        temp_dict = dict()
        for k, v in value.items():
            temp_dict[k] = get_dynamodb_type_value(v)
        return {"M": temp_dict}
    else:
        print("Dynamodb type not supported ", value)
        raise Exception("Dynamodb type not supported")
