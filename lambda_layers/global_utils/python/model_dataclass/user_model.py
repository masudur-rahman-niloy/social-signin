import json
import time
from copy import deepcopy
from typing import List, Optional, Any
from datetime import datetime

from aws_lambda_powertools.utilities.parser import validator, \
    root_validator, Field
from aws_lambda_powertools.utilities.parser.pydantic import constr, conint
from ksuid import ksuid
from model_dataclass.constants import *
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder

from model_dataclass.model_utils import get_dynamodb_type_value

class BatchWiseUserIntroducerSearchParams(BaseModel):
    batch: constr(min_length=4)
    userType: constr(min_length=3)
    membership: str = ""


class MigratedNewUserModel(BaseModel): 
    userId: str  
    firstName: str
    lastName: Optional[str]
    membership: str
    batch: str 
    batchCode: str


class UserPersonalInfoModel(BaseModel): 
    userId: str  
    firstName: str
    lastName: str
    middleName: str = ""
    batch: str = "" 
    batchCode: str = ""  # edit er option thakbe na
    membership: str
    dateOfBirth: str = ""
    startDate:str = ""
    endDate:str = ""
    sscGroup: str
    schoolHouse: str = "" #teacher der jonne eta lage na
    bloodGroup: str = ""
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        skip_attributes = ['__initialised__', 'PK', 'SK', 'batch', 'batchCode', 'method']
        for attr in skip_attributes:
            if attr in attributes:
                del attributes[attr]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        sql += f" where userId = '{userId}' ;"
        # sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        # for attr_name, val in attributes.items():
        #     sql += f"'{val}'" if type(val) == str else str(val)
        #     sql += ","
        print("sql ", sql)
        return sql

    def as_dynamo_update(self):
        attributes = deepcopy(vars(self))
        expression_attribute_values = {}
        expression_attribute_names = {}
        update_expression = "set "
        for key in attributes:
            if key != 'userId' and attributes[key] is not None:
                expression_attribute_names[f"#{key}"] = f"{key}"
                expression_attribute_values[f":{key}"] = f"{attributes[key]}"
                update_expression += f"#{key}=:{key},"

        update_expression = update_expression.rstrip(',')
        update_param = dict(
            Key={
                "PK": f"{USER_PREFIX}{self.userId}",
                "SK": f"{USER_PREFIX}{self.userId}",
            },
            ConditionExpression="attribute_exists(PK)",
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )
        return update_param


class UserContactModel(BaseModel): 
    userId: str  
    contactId: str = ""
    email: str = ""
    mobile: str
    phone: str = ""
    sequenceId: int
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['contactId', '__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))

        if attributes['contactId'] == '':
            raise ValueError("Contact id is needed")

        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and key != 'contactId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        contactId = attributes['contactId']
        sql += f" where contactId = '{contactId}';"
        print("sql ", sql)
        return sql


class Country(BaseModel):
    id: int # for edit
    country: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (country) values('{self.country}') on duplicate KEY UPDATE country='{self.country}';"


class City(BaseModel):
    id: int # for edit
    country: str
    city: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (country, city) values('{self.country}', '{self.city}') on duplicate KEY UPDATE city='{self.city}';"


class StateThana(BaseModel):
    id: int # for edit
    country: str
    city: str
    stateThana: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (country, city, stateThana) values('{self.country}', '{self.city}', '{self.stateThana}') on duplicate KEY UPDATE stateThana='{self.stateThana}';"


class Division(BaseModel):
    id: int # for edit
    division: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (division) values('{self.division}') on duplicate KEY UPDATE division='{self.division}';"


class Zilla(BaseModel):
    id: int  # for edit
    division: str
    zilla: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (division, zilla) values('{self.division}', '{self.zilla}') on duplicate KEY UPDATE zilla='{self.zilla}';"


class Upazilla(BaseModel):
    id: int  # for edit
    zilla: str
    upazilla: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (zilla, upazilla) values('{self.zilla}', '{self.upazilla}') on duplicate KEY UPDATE upazilla='{self.upazilla}';"


class Thana(BaseModel):
    id: int  # for edit
    upazilla: str
    thana: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (upazilla, thana) values('{self.upazilla}', '{self.thana}') on duplicate KEY UPDATE thana='{self.thana}';"


class Ward(BaseModel):
    id: int # for edit
    thana: str
    ward: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (thana, ward) values('{self.thana}', '{self.ward}') on duplicate KEY UPDATE ward='{self.ward}';"


class Company(BaseModel):
    id: int # for edit
    company: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (company) values('{self.company}') on duplicate KEY UPDATE company='{self.company}';"


class Profession(BaseModel):
    id: int # for edit
    profession: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (profession) values('{self.profession}') on duplicate KEY UPDATE profession='{self.profession}';"


class Designation(BaseModel):
    id: int # for edit
    designation: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (designation) values('{self.designation}') on duplicate KEY UPDATE designation='{self.designation}';"


class Department(BaseModel):
    id: int # for edit
    department: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (department) values('{self.department}') on duplicate KEY UPDATE department='{self.department}';"


class Institute(BaseModel):
    id: int # for edit
    institute: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (institute) values('{self.institute}') on duplicate KEY UPDATE institute='{self.institute}';"


class Degree(BaseModel):
    id: int # for edit
    degree: str

    def add_or_update_sql(self, table_name):
        return f"insert into {table_name} (degree) values('{self.degree}') on duplicate KEY UPDATE degree='{self.degree}';"


class UserAddressModel(BaseModel): 
    userId: str 
    addressId: str # this is for user's edit id
    title: str
    country: str
    city: str = ""
    stateThana: str = ""
    postCode: str = ""
    address1: str
    address2: str = ""

    locality: str = ""
    division: str = ""
    zilla: str = ""
    upazilla: str = ""
    thana: str = ""
    ward: str = ""

    sequenceId: int
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['addressId', '__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))

        if attributes['addressId'] == '':
            raise ValueError("Address id is needed")

        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and key != 'addressId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        addressId = attributes['addressId']
        sql += f" where addressId = '{addressId}';"
        print("sql ", sql)
        return sql


class UserExperienceModel(BaseModel): 
    userId: str  
    experienceId: str = "" # this is for user's edit id
    company: str
    designation: str
    department: str = ""
    profession: str = ""
    professional_summary: str = ""
    startDate: str
    endDate: str = ""
    sequenceId: int
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())


    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['experienceId', '__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))

        if attributes['experienceId'] == '':
            raise ValueError("Experience id is needed")

        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and key != 'experienceId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        experienceId = attributes['experienceId']
        sql += f" where experienceId = '{experienceId}';"
        print("sql ", sql)
        return sql


class UserEducationModel(BaseModel): 
    userId: str  
    educationId: str = "" # this is for user's edit id
    institute: str
    degree: str
    specialaization: str = "" 
    topic: str = ""
    eduAchievement: str = ""
    currActivities: str = ""
    startDate:str 
    endDate:str = ""
    sequenceId: int
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['educationId', '__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))

        if attributes['educationId'] == '':
            raise ValueError("Education id is needed")

        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and key != 'educationId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        educationId = attributes['educationId']
        sql += f" where educationId = '{educationId}';"
        print("sql ", sql)
        return sql

    
class UserVoluntaryModel(BaseModel): 
    userId: str  
    voluntaryActId: str = "" # this is for user's edit id
    volOrganiaztion: str
    volDesignation: str
    volDescription: str = ""
    startDate:str
    endDate:str = "" 
    sequenceId: int  
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['voluntaryActId', '__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))

        if attributes['voluntaryActId'] == '':
            raise ValueError("Voluntary id is needed")

        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and key != 'voluntaryActId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        voluntaryActId = attributes['voluntaryActId']
        sql += f" where voluntaryActId = '{voluntaryActId}';"
        print("sql ", sql)
        return sql


class UserChildModel(BaseModel): 
    userId: str  
    childId: str = "" # this is for user's edit id
    childName: str
    sex: str
    dateOfBirth: Optional[str]
    sequenceId: int
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

class UserSpouseModel(BaseModel): 
    userId: str  
    spouseId: str = "" # this is for user's edit id
    spouseName: str
    profession: str = ""
    company: str = ""
    designation: str = "" # profession r designation er moddhe diff ki?
    department: str #profession; etar upor depend kre onno field gulo mandatory dependent
    visibility: str = ""
    sequenceId: int 
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())
    #todo need to add constructor
    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['spouseId', '__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'

    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))

        if attributes['spouseId'] == '':
            raise ValueError("Spouse id is needed")

        print(attributes)
        print('attributes in sql insert: ', attributes)
        attributes_to_remove = ['__initialised__', 'PK', 'SK', 'method']
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and key != 'spouseId' and attributes[key] is not None:
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "

        sql = sql[:-2]  # As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        spouseId = attributes['spouseId']
        sql += f" where spouseId = '{spouseId}';"
        print("sql ", sql)
        return sql


class UserFamilyModel(BaseModel): 
    userId: str 
    familyId: str = "" # this is for user's edit id
    fatherName: str
    motherName: str
    relationshipStatus: str
    sequenceId: int
    visibility: str = ""
    createdAt: int = 1630215436
    updatedAt: int = 1630215436
    method: str = "add"

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.method == "add":
            self.createdAt = int(time.time())
        else:
            self.updatedAt = int(time.time())

class ProfileSearchModel(BaseModel):
    batch: str = None
    batchCode: str = None 
    bloodGroup: str = None
    membership: str = None
    relationshipStatus: str = None
    designation: str = None
    #department: Optional[str]
    #profession: Optional[str]
    institute: str = None 
    degree: str = None
    company: str = None
    country: str = None
    division: str = None
    zilla: str = None
    upazilla: str = None
    thana: str = None
    city: str = None
    stateThana: str = None

class SearchProfileModel(BaseModel):
    searchParams: ProfileSearchModel
    searchSection: str
    page: Optional[constr(min_length=1)]
    limit: Optional[constr(min_length=1)]