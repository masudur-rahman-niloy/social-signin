import re
from typing import Type, Any

from pydantic import BaseModel

regex_bd_mobile = re.compile(
    r"^(?:\+88|01)?(?:\d{11}|\d{13})$"
)


class BdMobileNumber(BaseModel):

    @classmethod
    def __get_validators__(cls) -> 'BdMobileNumber':
        yield cls.validate

    @classmethod
    def validate(cls: Type['BdMobileNumber'], value: Any) -> 'BdMobileNumber':
        if not isinstance(value, str):
            raise TypeError("string required")

        m = regex_bd_mobile.match(value)
        # print(m)
        if not m:
            raise ValueError("invalid mobile number format")

        # print("value", m.group())
        return value
