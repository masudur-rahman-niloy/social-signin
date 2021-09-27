import json
import time
from copy import deepcopy
from typing import List, Optional, Any
import datetime

from aws_lambda_powertools.utilities.parser import validator, \
    root_validator, Field
from aws_lambda_powertools.utilities.parser.pydantic import constr
from ksuid import ksuid
from model_dataclass.constants import *
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder

from model_dataclass.model_utils import get_dynamodb_type_value


class UserModel(BaseModel):
    userType: str = ""
    batchCode: str = ""
    firstName: str = ""
    lastName: str = ""
    schoolHouse: str = ""
    batch: str = ""
    membership: str = ""
    introducerId: str = ""
    name: constr(min_length=3)
    signupRole: constr(min_length=3)
    role: constr(min_length=3)
    signupMedium: constr(min_length=3)
    createdAt: int = None
    updatedAt: int = None
    isDeleted: bool = False
    isAdminApprovalPending: bool = True
    adminApprovalApprovedBy: str = ""
    isIntroducerApprovalPending: bool = True
    introducerApprovalApprovedBy: str = ""
    isUserBlocked: bool = False  
    isActivated: bool = False
    userStatus: str = "pending"
    emailVerified: bool = False
    phoneVerified: bool = False
    receivePromotionalEmail: bool = False
    recoveryEmail: str = ""
    profile_picture: constr(max_length=255) = ""
    visibility: str = ""
    email: str = ""
    phone: str = ""
    PK: str = ""
    SK: str = ""    
    userId: str = None  # cognito customUserId
    isPaymentReceived: bool = False

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.userId is None:
            print('inside userId None')
            self.userId = str(ksuid())
            self.createdAt = int(time.time())
            self.updatedAt = int(time.time())
            self.signupRole = self.role
            self.role = self.role if self.role == ADMIN_ROLE else INITIAL_ROLE

        self.PK = f"{USER_PREFIX}{self.userId}"
        self.SK = f"{USER_PREFIX}{self.userId}"
        print('end of init')

    @validator('signupMedium')
    def check_signup_medium(cls, signupMedium):
        print('inside check_signup_medium')
        if signupMedium not in ALLOWED_REGISTRATION_MEDIUM:
            print('inside check_signup_medium error')
            raise ValueError("Medium must be either 'phone' or 'email'")
        return signupMedium

    @validator('role')
    def check_role(cls, role):
        print('inside check_role')
        if role not in ALLOWED_ROLE_FOR_REGISTRATION:
            print('inside check_role error')
            raise ValueError(f"Role must be one of the following: {','.join(ALLOWED_ROLE_FOR_REGISTRATION)}")
        return role

    @root_validator
    def check_email_phone_based_on_medium(cls, values):
        print('inside check_email_phone_based_on_medium')
        medium = values.get('medium')
        email = values.get('email')
        phone = values.get('phone')

        if medium == EMAIL_MEDIUM and email == "":
            raise ValueError(f"{EMAIL_MEDIUM.capitalize()} cannot be empty")
        if medium == PHONE_MEDIUM and phone == "":
            raise ValueError(f"{PHONE_MEDIUM.capitalize()} cannot be empty")

        print('returning values')
        return values

    def as_aurora_admin_created_user(self):
        if self.role == INSTRUCTOR_ROLE:
            self.role = STUDENT_INSTRUCTOR_ROLE


    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        print('attributes in dynamodb json: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            if val is not None:
                item[attr_name] = get_dynamodb_type_value(val)
        return item

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        if 'PK' in attributes:
            del attributes['PK']
        if 'SK' in attributes:
            del attributes['SK']
        if 'visibility' in attributes:
            del attributes['visibility']

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'
    
    def as_sql_update(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        if 'PK' in attributes:
            del attributes['PK']
        if 'SK' in attributes:
            del attributes['SK']
        if 'visibility' in attributes:
            del attributes['visibility']

        sql = f"update {table_name} set "
        for key in attributes:
            if key != 'userId' and attributes[key] is not None: 
                sql += f"{key} = "
                if isinstance(attributes[key], str):
                    sql += f"'{attributes[key]}', "
                else:
                    sql += f"{attributes[key]}, "
            
        sql = sql[:-2] #As main sql has extra space and one comma, we have to deduct those.
        userId = attributes['userId']
        sql += f" where userId = '{userId}' ;"
        # sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        # for attr_name, val in attributes.items():
        #     sql += f"'{val}'" if type(val) == str else str(val)
        #     sql += ","
        print("sql ",sql)
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


class ExistingEmailPhoneModel(BaseModel):
    emailOrPhone: constr(min_length=3)
    medium: constr(min_length=3)
    userId: constr(min_length=3)
    PK: str = ""
    SK: str = ""
    createdAt: int = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.createdAt is None:
            self.createdAt = int(time.time())
        self.PK = EXISTING_EMAIL_PHONE
        self.SK = f"{self.emailOrPhone}"

    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item


class HashedPasswordModel(BaseModel):
    userId: constr(min_length=3)
    passwords: List[str] = Field(default_factory=list)
    createdAt: int = None
    PK: str = ""
    SK: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.createdAt is None:
            self.createdAt = int(time.time())
        self.PK = f"{USER_PREFIX}{self.userId}"
        self.SK = HASHED_PASSWORD

    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item


class ConfirmationCodeModel(BaseModel):
    userId: constr(min_length=3)
    code: constr(min_length=6, max_length=6)
    medium: constr(min_length=3)
    destination: constr(min_length=3)
    createdAt: int = None
    PK: str = ""
    SK: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.createdAt is None:
            self.createdAt = int(time.time())
        self.PK = CONFIRMATION_CODE
        self.SK = f"{USER_PREFIX}{self.userId}"

    @validator('medium')
    def check_medium(cls, medium):
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            raise ValueError(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        return medium

    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item


class UserRegisterModel1(BaseModel):  
    userId: str
    userType: str 
    firstName: str 
    lastName: str = ""
    name: str = None
    schoolHouse: str = ""
    batch: str
    batchCode: str = ""
    profile_picture: str
    email: Optional[str]
    phone: Optional[str]
    name: str
    password: constr(min_length=6)
    role: str
    medium: str
    receivePromotionalEmail: bool = False
    introducerId: str = ""
    membership: str
    updatedAt: int = None
    emailOrPhone: str
    isPaymentReceived: bool = False

    def __init__(self, **data: Any):
        super().__init__(**data)
        print('self', self)
        if self.name is None:
            print('inside userId None')
            self.name = f"{self.firstName} {self.lastName}"
            self.updatedAt = int(time.time())


    @root_validator
    def check_membership_acceptance_and_payment(cls, values):        
        today = datetime.datetime.now()
        membership = values.get('membership')
        batch = values.get('batch')
        isPaymentReceived = values.get('isPaymentReceived')
        userType = values.get('userType')
        errors = []
        if not batch.isdigit():
            errors.append("Invalid batch input!")        
        
        if membership == "lifetime_member" and userType == "new_user":
            current_year = today.year
            batch = int(batch)
            year_diff = current_year - batch

            if year_diff < 10:
                errors.append(f"Life-time member should pass 10 years before applying for this membership")
        
        if (membership == "lifetime_member" or membership == "general_member") and isPaymentReceived == False and userType == "new_user":
            errors.append("Payment Required!")
        
        if len(errors):
            raise ValueError(','.join(errors))

        return values          

class UserRegisterModel(BaseModel):   
    firstName: str
    lastName: Optional[constr(min_length=3)]
    schoolHouse: str
    batch: str
    profile_picture: str = ""
    email: Optional[str]
    phone: Optional[str]
    name: str
    password: constr(min_length=6)
    role: str
    medium: str
    receivePromotionalEmail: bool = False
    emailOrPhone: str
    introducerId: str
    membership: str

    @root_validator
    def check_role_medium(cls, values):
        medium = values.get('medium')
        role = values.get('role')
        errors = []
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            errors.append(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        if role not in CLIENT_ROLE_FOR_REGISTRATION:
            errors.append(f"Role must be one of the following: {','.join(CLIENT_ROLE_FOR_REGISTRATION)}")
        if len(errors):
            raise ValueError(','.join(errors))
        return values

class SignupModel(BaseModel):   
    firstName: str = ""
    lastName: str = ""  
    name: str = ""
    password: constr(min_length=6)
    medium: str
    email: str = ""
    phone: str = ""
    emailOrPhone: str
    role: str

    @root_validator
    def check_role_medium(cls, values):
        medium = values.get('medium')
        role = values.get('role')
        errors = []
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            errors.append(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        if role not in CLIENT_ROLE_FOR_REGISTRATION:
            errors.append(f"Role must be one of the following: {','.join(CLIENT_ROLE_FOR_REGISTRATION)}")
        if len(errors):
            raise ValueError(','.join(errors))
        return values


class EmailPhoneMediumModel(BaseModel):
    emailOrPhone: constr(min_length=3)
    medium: str = ""

    @root_validator
    def check_medium(cls, values):
        medium = values.get('medium')
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            raise ValueError(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        return values


class CodeValidityModel(BaseModel):
    emailOrPhone: constr(min_length=3)
    medium: str = ""
    confirmationCode: constr(min_length=6, max_length=6)

    @root_validator
    def check_medium(cls, values):
        medium = values.get('medium')
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            raise ValueError(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        return values


class RequestUserApprovalModel(BaseModel):
    userId: constr(min_length=3)


class SigninModel(BaseModel):
    emailOrPhone: constr(min_length=3)
    medium: constr(min_length=3)
    password: constr(min_length=6)

    @root_validator
    def check_medium(cls, values):
        medium = values.get('medium')
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            raise ValueError(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        return values


class SocialSigninModel(BaseModel):
    id_token: constr(min_length=3)
    access_token: constr(min_length=3)
    refresh_token: constr(min_length=3)
    expires_in: constr(min_length=3)
    token_type: constr(min_length=3)


class ConfirmUserModel(BaseModel):
    userId: constr(min_length=3)
    status: str = ""
    reason: str = ""
    approvalUserType: str
    isAdminApprovalPending: bool = True
    adminApprovalApprovedBy: str = ""
    isIntroducerApprovalPending: bool = True
    introducerApprovalApprovedBy: str = ""

    @root_validator
    def check_status(cls, values):
        status = values.get('status')
        reason = values.get('reason')
        approvalUserType = values.get('approvalUserType')
        adminApprovalApprovedBy = values.get('adminApprovalApprovedBy')
        introducerApprovalApprovedBy = values.get('introducerApprovalApprovedBy')

        if status not in ALLOWED_STATUS:
            raise ValueError(f"Status must be one of the following: {','.join(ALLOWED_STATUS)}")
        if status == REJECT_STATUS and reason == "":
            raise ValueError("Must provide reason when rejecting user approval")
        if approvalUserType == approvalUserTypeAdmin and adminApprovalApprovedBy == "":
            raise ValueError("Admin user not provided")
        if approvalUserType == approvalUserTypeIntroducer and introducerApprovalApprovedBy == "":
            raise ValueError("Introducer user not provided")
        return values


class SetPasswordModel(BaseModel):
    emailOrPhone: constr(min_length=3)
    medium: str = ""
    newPassword: constr(min_length=6)
    confirmationCode: constr(min_length=6, max_length=6)

    @root_validator
    def check_medium(cls, values):
        medium = values.get('medium')
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            raise ValueError(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        return values


class RecoveryEmailModel(BaseModel):
    userId: constr(min_length=3)
    recoveryEmail: constr(min_length=3)


class PrimaryEmailModel(BaseModel):
    email: constr(min_length=3)
    access_token: constr(min_length=3)
    userId: constr(min_length=3)


class UserProfileModel(BaseModel):
    name: constr(min_length=3)
    language: constr(min_length=2)
    currency: constr(min_length=2)
    profile_title: constr(min_length=3)
    current_employment: constr(min_length=3)

    portfolio_link: str = ""
    bio: str = ""


class UserProfilePictureModel(BaseModel):
    profile_picture: constr(max_length=255) = ""


class BlockUnblockUserModel(BaseModel):
    role: constr(min_length=3)
    isBlocked: bool
    reason: str = ""

    @root_validator
    def check_reason(cls, values):
        is_blocked = values.get('isBlocked')
        reason = values.get('reason')
        if is_blocked and reason == "":
            raise ValueError("Must provide reason when blocking user")
        return values


class AdminSignupModel(BaseModel):
    name: constr(min_length=3)
    emailOrPhone: constr(min_length=3)
    role: str = ""
    medium: str = ""
    receivePromotionalEmail: bool = False

    @root_validator
    def check_role_medium(cls, values):
        medium = values.get('medium')
        role = values.get('role')
        errors = []
        if medium not in [EMAIL_MEDIUM]:
            errors.append(f"Medium must be {EMAIL_MEDIUM} for admin signup")
        if role in CLIENT_ROLE_FOR_REGISTRATION:
            errors.append(f"Role cannot be any of the following: {','.join(CLIENT_ROLE_FOR_REGISTRATION)}")
        if len(errors):
            raise ValueError(','.join(errors))
        return values


class AdminFirstSigninModel(BaseModel):
    email: constr(min_length=3)
    password: constr(min_length=6)


class ForcePasswordModel(BaseModel):
    username: constr(min_length=5)
    newPassword: constr(min_length=6)
    session: constr(min_length=3)
    challengeName: str = ""

    @root_validator
    def check_challenge_name(cls, values):
        challengeName = values.get('challengeName')
        if challengeName != FORCE_PASSWORD_CHALLENGE_NAME:
            raise ValueError(f"challengeName must be '{FORCE_PASSWORD_CHALLENGE_NAME}'")
        return values


class SearchParamsModel(BaseModel):
    name: constr(min_length=3) = None
    email: constr(min_length=3) = None
    phone: constr(min_length=3) = None
    role: constr(min_length=3) = None
    isDeleted: bool = None
    isUserBlocked: bool = None
    isActivated: bool = None
    emailVerified: bool = None
    phoneVerified: bool = None
    membership: str = None
    schoolHouse: str = None
    batch: str = None
    batchCode: str = None
    isAdminApprovalPending: bool = None
    isIntroducerApprovalPending: bool = None


class SearchUserModel(BaseModel):
    searchParams: SearchParamsModel
    page: Optional[constr(min_length=1)]
    limit: Optional[constr(min_length=1)]


class LogoutModel(BaseModel):
    accessToken: constr(min_length=3)


class VerifyAccountModel(BaseModel):
    username: constr(min_length=3)


class VerifyUserAttributeModel(BaseModel):
    confirmationCode: constr(min_length=6)
    medium: constr(min_length=1)
    access_token: constr(min_length=3)
    user_id: constr(min_length=3)

    @root_validator
    def check_medium(cls, values):
        medium = values.get('medium')
        if medium not in ALLOWED_REGISTRATION_MEDIUM:
            raise ValueError(f"Medium must be one of the following: {','.join(ALLOWED_REGISTRATION_MEDIUM)}")
        return values


class ResendUserAttributeTokenModel(BaseModel):
    access_token: constr(min_length=3)


class ChangeUserPasswordModel(BaseModel):
    password: constr(min_length=6)
    repeat_password: constr(min_length=6)
    old_password: constr(min_length=6)
    access_token: constr(min_length=3)
    user_id: constr(min_length=3)

    @root_validator()
    def validate_item(cls, values):
        # check password and repeat_password
        if values.get('password') != values.get('repeat_password'):
            raise ValueError('Password and repeat_password must be same')
        return values


class RefreshTokenModel(BaseModel):
    refresh_token: constr(min_length=3)


class BulkSignupModel():
    def __init__(self, name, emailOrPhone, medium, role):
        self.name = name
        self.emailOrPhone = emailOrPhone
        self.medium = medium
        self.role = role

    def to_dictionary(self):
        return {
            "name": self.name,
            "emailOrPhone": self.emailOrPhone,
            "medium": self.medium,
            "role": self.role,
        }

    def __str__(self):
        return f"{self.name} - {self.emailOrPhone} - {self.medium} - {self.role}"


# ====================== Notification ======================

def get_user_notification_pk_sk(user_id, subscription_address):
    return dict(
        PK=f"{USER_PREFIX}{user_id}",
        SK=f"{SUBSCRIPTION_PREFIX}{subscription_address}",
    )


@dataclass
class SubscriptionModel:
    user_id: str = ""
    receivePromotionalContent: bool = True
    receiveAnnouncement: bool = True

    PK: str = ""
    SK: str = ""

    def __post_init_post_parse__(self):
        pksk = get_user_notification_pk_sk(self.user_id, '')
        self.PK = pksk.get('PK')
        self.SK = f"{SUBSCRIPTION_CONFIGURATION_PREFIX}"

    def to_dynamodb_client_format(self):
        item = {
            "PK": {'S': self.PK},
            "SK": {'S': self.SK},
            "user_id": {'S': self.user_id},
            "receivePromotionalContent": {'BOOL': self.receivePromotionalContent},
            "receiveAnnouncement": {'BOOL': self.receiveAnnouncement},
        }
        return item

    def as_json(self):
        return json.loads(json.dumps(self, indent=4, default=pydantic_encoder))


@dataclass
class SubscriptionRegistrationModel:
    channel_type: constr(min_length=3)
    endpoint_address: constr(min_length=4)

    user_id: str = ""
    PK: str = ""
    SK: str = ""

    @root_validator
    def check_role_medium(cls, values):
        channel_type = values.get('channel_type')
        errors = []
        if channel_type not in VALID_CHANNELS:
            errors.append(f"channel_type must be one of the following "
                          f"{','.join(VALID_CHANNELS)}")
        if len(errors):
            raise ValueError(','.join(errors))
        return values

    def __post_init_post_parse__(self):
        pksk = get_user_notification_pk_sk(self.user_id, self.endpoint_address)
        self.PK = pksk.get('PK')
        self.SK = pksk.get('SK')

    def as_json(self):
        return json.loads(json.dumps(self, indent=4, default=pydantic_encoder))


@dataclass
class SetProfileVisibilityModel:
    user_id: constr(min_length=3)
    email: str = None
    phone: str = None
    current_employment: str = None
    portfolio_link: str = None
    bio: str = None
    PK: str = ""
    SK: str = ""

    @root_validator
    def check_at_least_one(cls, values):
        email = values.get('email')
        phone = values.get('phone')
        current_employment = values.get('current_employment')
        portfolio_link = values.get('portfolio_link')
        bio = values.get('bio')
        if (email is not None and email not in VIEW_MANAGEMENT_ROLES) \
                or (phone is not None and phone not in VIEW_MANAGEMENT_ROLES) \
                or (current_employment is not None and current_employment not in VIEW_MANAGEMENT_ROLES) \
                or (portfolio_link is not None and portfolio_link not in VIEW_MANAGEMENT_ROLES) \
                or (bio is not None and bio not in VIEW_MANAGEMENT_ROLES):
            raise ValueError("Invalid view-role provided")

        return values

    def __post_init_post_parse__(self):
        self.PK = f"{USER_PREFIX}{self.user_id}"
        self.SK = f"{USER_PREFIX}{self.user_id}"

    def to_dynamodb_client_format(self):
        item = {}
        attributes = deepcopy(vars(self))
        print('attributes: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item


class UserStatModel(BaseModel):
    user_id: constr(min_length=3)
    total_sold_amount: float = 0.0
    total_sold_unit_count: int = 0
    rating: float = 0.0
    PK: str = ""
    SK: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.PK = f"{USER_PREFIX}{self.user_id}"
        self.SK = f"{USER_PREFIX}{STAT_PREFIX}"

    def as_dynamodb_json(self):
        item = {}
        attributes = deepcopy(vars(self))
        print('attributes in dynamodb json: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']
        for attr_name, val in attributes.items():
            item[attr_name] = get_dynamodb_type_value(val)
        return item

class BatchWiseIdModel(BaseModel):
    batch: constr(min_length=4)
    batchWiseId: int = 0

    def as_sql_insert(self, table_name):
        attributes = deepcopy(vars(self))
        print(attributes)
        print('attributes in sql insert: ', attributes)
        if '__initialised__' in attributes:
            del attributes['__initialised__']

        sql = f"insert into {table_name}({','.join([attr_name for attr_name in attributes.keys()])}) values("
        for attr_name, val in attributes.items():
            sql += f"'{val}'" if type(val) == str else str(val)
            sql += ","

        return sql.rstrip(',') + ');'


    


