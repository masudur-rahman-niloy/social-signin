import time
from copy import deepcopy
from enum import Enum
from typing import Union, Optional

from ksuid import ksuid
from pydantic import BaseModel, Field, EmailStr, PositiveInt, validator
from pydantic.types import constr

from model_dataclass.model_utils import get_dynamodb_type_value
from model_dataclass.constants import (
    SHOP_PREFIX,
    SHOP_GENERAL_INFO_PREFIX,
    SHOP_BUSINESS_INFO_PREFIX,

)


# from model_utils import get_dynamodb_type_value
# from constants import (
#     SHOP_PREFIX,
#     SHOP_GENERAL_INFO_PREFIX,
# )


class AccountTypeEnum(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class ShopSizeEnum(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    BIG = "big"


class LegalFormNameEnum(str, Enum):
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    CORPORATION = "corporation"
    LLC = "llc"


class ShopStatusEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    UNDER_PREVIEW = "under_preview"


class ShopFloorEnum(str, Enum):
    pass


class ContactTypeEnum(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"


class ContactInfoModel(BaseModel):
    contact_type: ContactTypeEnum = ContactTypeEnum.PERSONAL
    email: Optional[EmailStr]
    phone: str = ""


class ShopCategoryTypeEnum(str, Enum):
    GROCERY = "grocery"


class IdTypeEnum(str, Enum):
    NID = "national_id"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    TIN = "taxpayers_identification_number"


class NidModel(BaseModel):
    id_type: IdTypeEnum = IdTypeEnum.NID
    nid_code: str
    photo_front_page_s3key: str
    photo_back_page_s3key: str


class BankInfoModel(BaseModel):
    account_title: constr(to_lower=True, strip_whitespace=True)
    account_number: constr(strip_whitespace=True)
    bank_name: constr(to_lower=True, strip_whitespace=True)
    branch_name: constr(to_lower=True, strip_whitespace=True)
    routing_number: constr(strip_whitespace=True)
    bank_check_s3key: constr(strip_whitespace=True)


class AddressModel(BaseModel):
    # house_number: str = ""
    # street_number: str = ""
    address_str: str = ""
    postal_code: str
    city: str
    division: str
    country: str


class WareHouseModel(BaseModel):
    address: AddressModel
    contact_info: ContactInfoModel


class ReturnAddressModel(WareHouseModel):
    pass


class ShopGeneralInfo(BaseModel):
    owner_id: str
    # shop_id: str = Field(default_factory=lambda: str(ksuid()))
    shop_id: str = None
    shop_name: str
    shop_size: ShopSizeEnum = ShopSizeEnum.SMALL
    shop_on_floor: str
    shop_category: ShopCategoryTypeEnum = ShopCategoryTypeEnum.GROCERY
    created_at: int = None
    PK: str = ""
    SK: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(self.__class__.__name__, self)

        if self.shop_id is None:
            print(self.__class__.__name__, "shop_id is None")
            self.shop_id = str(ksuid())
            self.created_at = int(time.time())
        self.PK = f"{SHOP_PREFIX}#{self.shop_id}"
        self.SK = f"{SHOP_PREFIX}#{SHOP_GENERAL_INFO_PREFIX}#{self.shop_id}"
        print(self.__class__.__name__, "END of INIT")
        print(self.__class__.__name__, self)

    @validator('owner_id')
    def check_owner_id_is_not_empty(cls, value):
        if len(value) <= 0:
            raise ValueError(f"{value} cannot be empty")

        return value

    @validator('shop_name')
    def check_shop_name_is_not_empty(cls, value):
        if len(value) <= 0:
            raise ValueError(f"{value} cannot be empty")

        return value

    # def get_pk_sk(self):
    #     return dict(
    #         PK=f"{SHOP_PREFIX}#{self.shop_id}",
    #         SK=f"{SHOP_GENERAL_INFO_PREFIX}#{self.shop_id}",
    #     )

    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        print('attributes in dynamodb json: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item


class ShopBusinessInfo(BaseModel):
    owner_id: str
    shop_id: str
    nid_code: str
    address: AddressModel
    PK: str = ""
    SK: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(self.__class__.__name__, self)
        self.created_at = int(time.time())
        self.PK = f"{SHOP_PREFIX}#{self.shop_id}"
        self.SK = f"{SHOP_PREFIX}#{SHOP_GENERAL_INFO_PREFIX}#{self.shop_id}"
        print(self.__class__.__name__, "END of INIT")
        print(self.__class__.__name__, self)

    @validator('owner_id')
    def check_owner_id_is_not_empty(cls, value):
        if len(value) <= 0:
            raise ValueError(f"owner_id : {value} cannot be empty")
        return value

    @validator('nid_code')
    def check_nid_code_is_not_empty(cls, value):
        if len(value) <= 0:
            raise ValueError(f"owner_id : {value} cannot be empty")
        return value

    @validator('shop_id')
    def check_shop_name_is_not_empty(cls, value):
        if len(value) <= 0:
            raise ValueError(f"owner_id : {value} cannot be empty")
        return value

    # def get_pk_sk(self):
    #     return dict(
    #         PK=f"{SHOP_PREFIX}#{self.shop_id}",
    #         SK=f"{SHOP_GENERAL_INFO_PREFIX}#{self.shop_id}",
    #     )

    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        print('attributes in dynamodb json: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item


class ShopModel(BaseModel):
    owner_id: str
    shop_id: str
    unique_product_count: PositiveInt = 1  # 1, positive, 1 > 0, temp solution
    shop_size: ShopSizeEnum
    legal_name: str
    legal_form_name: LegalFormNameEnum
    official_doc_s3key: str
    logo_s3key: str
    status: ShopStatusEnum
    on_floor: Union[str, ShopFloorEnum]
    agreement_doc_s3key: str
    shop_address: AddressModel
    contact_info: ContactInfoModel
    category: ShopCategoryTypeEnum = ShopCategoryTypeEnum.GROCERY
    business_registration_number: str
    nid: NidModel
    bank_info: BankInfoModel
    warehouse_address: Union[str, WareHouseModel] = ""  # Optional, mandatory?
    return_address: Union[str, ReturnAddressModel] = ""  # Optional,mandatory?
    agree_with_terms: bool
