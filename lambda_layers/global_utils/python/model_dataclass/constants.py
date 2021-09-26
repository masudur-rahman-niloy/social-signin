PASSWORD_REUSE_COUNT = 3
DURATION_ALLOWED_EMAIL = 15 * 60  # 15 mins
DURATION_ALLOWED_PHONE = 5 * 60  # 5 mins
IMAGE_BUCKET = "https://olsa-public-directory.s3.us-west-2.amazonaws.com"
SEARCH_USER_MATCHING_PARAMS = ["name", "email", "phone"]
SEARCH_USER_EQUAL_MATCHING_PARAMS = ["membership", "schoolHouse", "batch", "batchCode", "role"]
VIEW_MANAGEMENT_ROLES = ['public', 'onlyme', 'member']
ALLOWED_REGISTRATION_MEDIUM = ['phone', 'email', 'username']
ALLOWED_ROLE_FOR_REGISTRATION = ['student', 'member', 'admin', 'visitor', 'family', 'collegiate_lt', 'asc_ofc_staff',
                                 'teacher', 'lifetime_member', 'general_member']
# STUDENT_INSTRUCTOR_ROLE_FOR_REGISTRATION = ['student', 'member']
# ALLOWED_INSTRUCTOR_STATUS = ['approve', 'reject']
CLIENT_ROLE_FOR_REGISTRATION = ['student', 'member']
ALLOWED_STATUS = ['approve', 'reject']
VALID_CHANNELS = ['GCM', 'EMAIL', 'TEXT_MESSAGE']

# ============= SHOP=================
SHOP_PREFIX = "shop"
SHOP_GENERAL_INFO_PREFIX = "general_info"
SHOP_BUSINESS_INFO_PREFIX = "business_info"

# ============= SHOP=================

USER_PREFIX = "USER#"
STAT_PREFIX = "STAT"
USER_SOCIAL_PREFIX = "USER_SOCIAL_LINKS"
FORCE_PASSWORD_CHALLENGE_NAME = 'NEW_PASSWORD_REQUIRED'
EMAIL_MEDIUM = 'email'
PHONE_MEDIUM = 'phone'
USERNAME_MEDIUM = 'username'
COGNITO_NAME_ATTRIBUTE = 'name'
COGNITO_ROLE_ATTRIBUTE = 'custom:role'
COGNITO_EMAIL_ATTRIBUTE = 'email'
COGNITO_PHONE_ATTRIBUTE = 'phone_number'
COGNITO_USERNAME_ATTRIBUTE = 'username'
COGNITO_USER_STATUS_ATTRIBUTE = 'user_status'
COGNITO_USER_ID_ATTRIBUTE = 'custom:customUserId'
COGNITO_BATCH_ID_ATTRIBUTE = 'custom:batchCode'
COGNITO_FIRST_NAME_ATTRIBUTE = 'custom:firstName'
COGNITO_LAST_NAME_ATTRIBUTE = 'custom:lastName'
COGNITO_SCHOOL_BATCH_ATTRIBUTE = 'custom:batch'
COGNITO_SCHOOL_HOUSE_ATTRIBUTE = 'custom:schoolHouse'
COGNITO_MEMBERSHIP_ATTRIBUTE = 'custom:membership'
COGNITO_SIGNUP_MEDIUM_ATTRIBUTE = 'custom:signupMedium'
COGNITO_UNCONFIRMED_STATUS = 'UNCONFIRMED'
COGNITO_EXTERNAL_SIGNUP_MEDIUM_VALUE = 'external'
REGULAR_SIGNIN_SOURCE = 'REGULAR'
MEMBERSHIP_PREFIX = {"general_member": "GM", "lifetime_member": "LM", "admin": "AD", "student": "S", "visitor": "V",
                     "family": "F", "collegiate_lt": "C", "asc_ofc_staff": "A", "teacher": "T"}
MEMBERSHIP_TITLES = {
    "general_member": "General Member",
    "lifetime_member": "Life Time Member",
    "admin": "Admin",
    "student": "Student",
    "visitor": "Visitors",
    "family": "Family",
    "collegiate_lt": "Collegiate Laboratorian",
    "asc_ofc_staff": "Associate (office staff)",
    "teacher": "Teacher"
}
MEMBERSHIP_FEES = {"general_member": 1200, "lifetime_member": 15000, "others": 0}
approvalUserTypeAdmin = "admin"
approvalUserTypeIntroducer = "introducer"
APP_NAME = "OLsA"
APPROVE_STATUS = 'approve'
REJECT_STATUS = 'reject'
INITIAL_ROLE = 'member'
INSTRUCTOR_ROLE = 'member'
ADMIN_ROLE = 'admin'
STUDENT_INSTRUCTOR_ROLE = 'member, student'
SUBSCRIPTION_PREFIX = "SUBSCRIPTION#"
SUBSCRIPTION_CONFIGURATION_PREFIX = "SUBSCRIPTION_CONFIGURATION"
EXISTING_EMAIL_PHONE = 'EXISTING#EMAIL#PHONE'
HASHED_PASSWORD = 'HASHED#PASSWORD'
CONFIRMATION_CODE = 'CONFIRMATION#CODE'
COUPON_PREFIX = "COUPON_CODE#"
AVAILABLE_DISCOUNT_TYPES = ['fixed', 'percent']
DATE_FORMAT = '%Y-%m-%d'
VALID_ACTIONS = ['OPEN_APP', 'DEEP_LINK', 'URL']

VALID_PAYMENT_SUBSCRIPTION_FEE = 'subscription_fee'
VALID_PAYMENT_REASONS = [VALID_PAYMENT_SUBSCRIPTION_FEE]

SEARCH_TRANSACTIONS_EQUAL_MATCHING_PARAMS = ["email_or_phone", "payment_reason", "membership_type", "transaction_id",
                                             "payment_status", "batch"]
SEARCH_TRANSACTIONS_GTE_MATCHING_PARAMS = ["payment_date_start"]
SEARCH_TRANSACTIONS_LTE_MATCHING_PARAMS = ["payment_date_end"]
SEARCH_TRANSACTIONS_FIELD_MAPPING = {
    "payment_date_start": "payment_date",
    "payment_date_end": "payment_date"
}

PAYMENT_REASON_PREFIX = 'payment_reason'

PAYMENT_PROCESSING_FAILED = 'processing_failed'
PAYMENT_PROCESSING_COMPLETED = 'completed'

SSLCOMMERZ_VALID_STATUS = 'VALID'
SSLCOMMERZ_FAILED_STATUS = 'FAILED'
SSLCOMMERZ_CANCELLED_STATUS = 'CANCELLED'
SSLCOMMERZ_UNATTEMPTED_STATUS = 'UNATTEMPTED'
SSLCOMMERZ_EXPIRED_STATUS = 'EXPIRED'

AURORA_TABLE_NAMES = {
    "USER": "user",
    "CURRENCY": "currency",
    "EMAIL_TEMPLATE": "email_templates",
    "MODULE": "module",
    "COGNITO_GROUP": "cognitogroup",
    "ACCESS_MANAGEMENT": "accessmanagement",
    "PAYMENT": "payments",
    "BATCH_WISE_ID": "batch_wise_id",
    "MIGRATED_USER": "migrated_user",
    "TRANSACTIONS": "transactions"
}

SEARCH_ATTRIBUTES_MAPPING = {
    "country": {
        "table": "countries",
        "field": "country"
    },
    "city": {
        "table": "cities",
        "field": "city",
        "parent": "country"
    },
    "state_thana": {
        "table": "stateThanas",
        "field": "stateThana",
        "parent": "city"
    },

    "division": {
        "table": "divisions",
        "field": "division"
    },
    "zilla": {
        "table": "zillas",
        "field": "zilla",
        "parent": "division"
    },
    "upazilla": {
        "table": "upazillas",
        "field": "upazilla",
        "parent": "zilla"
    },
    "thana": {
        "table": "thanas",
        "field": "thana",
        "parent": "upazilla"
    },
    "ward": {
        "table": "wards",
        "field": "ward",
        "parent": "thana"
    },

    "company": {
        "table": "companies",
        "field": "company"
    },
    "profession": {
        "table": "professions",
        "field": "profession"
    },
    "designation": {
        "table": "designations",
        "field": "designation"
    },
    "department": {
        "table": "departments",
        "field": "department"
    },
    "institute": {
        "table": "institutes",
        "field": "institute"
    },
    "degree": {
        "table": "degrees",
        "field": "degree"
    },
}

COGNITO_FILTER_RESOLVER = {
    EMAIL_MEDIUM: EMAIL_MEDIUM,
    PHONE_MEDIUM: COGNITO_PHONE_ATTRIBUTE,
    USERNAME_MEDIUM: COGNITO_USERNAME_ATTRIBUTE
}
