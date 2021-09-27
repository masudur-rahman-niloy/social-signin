from aws_lambda_powertools.utilities.parser import BaseModel
from model_dataclass.constants import *


class ProfileModel(BaseModel):
    PK: str = ""
    SK: str = ""
    user_id: str = ""

    def __post_init_post_parse__(self):
        self.PK = f"{USER_PREFIX}{self.user_id}"
        self.SK = f"{USER_SOCIAL_PREFIX}"
