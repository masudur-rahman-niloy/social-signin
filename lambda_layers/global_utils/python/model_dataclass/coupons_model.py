from datetime import datetime

from model_dataclass.constants import COUPON_PREFIX, AVAILABLE_DISCOUNT_TYPES, DATE_FORMAT
from pydantic import constr, root_validator, conint
from pydantic.dataclasses import dataclass
from pydantic.error_wrappers import ValidationError as PydanticValidationError


@dataclass
class CouponsModel:
	PK: str = ''
	SK: str = ''
	coupon_code: constr(min_length=5) = ''
	status: bool = True
	discount_type: constr() = ''
	discount_amount: conint() = ''
	applicable_from: constr() = ''
	applicable_to: constr() = ''
	minimum_limit: conint() = 0
	maximum_amount: conint() = 0

	@root_validator
	def check_values(cls, values):
		print(values)

		minimum_limit = values.get('minimum_limit')
		if minimum_limit < 0:
			raise PydanticValidationError(f"Minimum limit can not be negative")

		# check maximum amount
		maximum_amount = values.get('maximum_amount')
		if maximum_amount < 0:
			raise PydanticValidationError(f"Maximum amount can not be negative")

		# check discount_type
		discount_type = values.get('discount_type')
		if discount_type not in AVAILABLE_DISCOUNT_TYPES:
			raise PydanticValidationError(f"Invalid discount type")

		# check discount amount
		discount_amount = values.get('discount_amount')
		if discount_amount < 0:
			raise PydanticValidationError(f"Discount amount can not be negative")

		if discount_type == 'percent' and discount_amount > 100:
			raise PydanticValidationError(f"Invalid discount amount for selected discount type")

		# check applicable from and to
		applicable_from = values.get('applicable_from')
		applicable_to = values.get('applicable_to')

		applicable_from_dt = datetime.strptime(applicable_from, DATE_FORMAT).date()
		applicable_to_dt = datetime.strptime(applicable_to, DATE_FORMAT).date()
		time_now = datetime.now().date()  # TODO Check timezone

		if applicable_from_dt > applicable_to_dt:
			raise PydanticValidationError(f"Start time cannot be greater then end time")
		if time_now > applicable_from_dt:
			raise PydanticValidationError(f"Start time cannot be in the past")

		if time_now > applicable_to_dt:
			raise PydanticValidationError(f"End time cannot be in the past")

		return values

	def __post_init_post_parse__(self):
		self.PK = COUPON_PREFIX
		self.SK = self.coupon_code

	def to_dynamodb_client_format(self):
		item = {
			"PK": {'S': self.PK},
			"SK": {'S': self.SK},
			"coupon_code": {'S': self.coupon_code},
			"status": {'BOOL': self.status},
			"discount_type": {'S': self.discount_type},
			"discount_amount": {'N': self.discount_amount.__str__()},
			"applicable_from": {'S': self.applicable_from},
			"applicable_to": {'S': self.applicable_to},
			"minimum_limit": {'N': self.minimum_limit.__str__()},
			"maximum_amount": {'N': str(self.maximum_amount)},
		}
		return item
