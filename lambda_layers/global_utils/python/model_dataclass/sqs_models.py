from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.parser.pydantic import constr


class SQSMessageModel(BaseModel):
    messageType: constr(min_length=3)
    target: constr(min_length=5)
    smsMessage: constr(min_length=3)
    emailType: constr(min_length=3)
    emailSubject: constr(min_length=3)
    emailBodyText: constr(min_length=3)
    emailBodyHtml: constr(min_length=3)
