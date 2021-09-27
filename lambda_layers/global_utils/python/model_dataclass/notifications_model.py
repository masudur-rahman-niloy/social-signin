import json

from aws_lambda_powertools.utilities.parser import root_validator
from aws_lambda_powertools.utilities.parser.pydantic import constr
from model_dataclass.constants import USER_PREFIX, SUBSCRIPTION_PREFIX, SUBSCRIPTION_CONFIGURATION_PREFIX, \
    VALID_CHANNELS
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder


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
                          f"{','.join(channel for channel in VALID_CHANNELS)}")
        if len(errors):
            raise ValueError(','.join(errors))
        return values

    def __post_init_post_parse__(self):
        pksk = get_user_notification_pk_sk(self.user_id, self.endpoint_address)
        self.PK = pksk.get('PK')
        self.SK = pksk.get('SK')

    def as_json(self):
        return json.loads(json.dumps(self, indent=4, default=pydantic_encoder))
