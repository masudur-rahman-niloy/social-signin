from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.parser.pydantic import constr


class SupportTicketModel(BaseModel):
    topic: constr(min_length=3)
    assignedTo: constr(min_length=3)
    status: constr(min_length=3)
    message: constr(min_length=3)


class SupportTicketUpdateModel(BaseModel):
    assignedTo: constr(min_length=3)


class TicketDetailsModel(BaseModel):
    message: constr(min_length=3)
    status: str = 'pending'
    # pending, customer_action_required, admin_action_required, closed, reopen
    # from client (student/mentor), default is admin_action_required
