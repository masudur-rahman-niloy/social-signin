import json
import os

from pydantic import constr, root_validator
from model_dataclass.constants import VALID_ACTIONS
from pydantic.dataclasses import dataclass, Optional
from pydantic.json import pydantic_encoder

StageName = os.environ.get('StageName')



@dataclass
class PushNotificationTemplateModel:
    id: Optional
    template_name: constr(min_length=3, max_length=128)
    display_name: constr(min_length=3, max_length=128)
    body: constr(min_length=3)
    title: constr(min_length=3)
    action: str = 'OPEN_APP'

    @root_validator
    def check_action(cls, values):
        action = values.get('action')
        errors = []
        if action not in VALID_ACTIONS:
            errors.append(f"action must be one of the following "
                          f"{','.join(action for action in VALID_ACTIONS)}")
        if len(errors):
            raise ValueError(','.join(errors))
        return values

    def __post_init_post_parse__(self):
        self.template_name += f"_{StageName}"

    def as_json(self):
        return json.loads(json.dumps(self, indent=4, default=pydantic_encoder))

    def to_pinpoint_request(self):
        return {
            'Action': self.action,
            'Body': self.body,
            'Title': self.title,
        }
