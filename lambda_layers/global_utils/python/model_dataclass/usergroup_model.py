from pydantic import constr, BaseModel, conint, root_validator


class UserGroupModel(BaseModel):
	role_name: constr(min_length=1)
	group_name: constr(min_length=1)
	description: constr(min_length=1)
	precedence: conint(ge=0)
	status: bool = True

	group_id: conint(ge=0) = 0
	iam_role: constr() = None

	@root_validator
	def validate_iam_role(cls, values):
		group_id = values.get('group_id')
		iam_role = values.get('iam_role', '')

		if group_id != 0 and iam_role == '':
			raise ValueError('invalid value for iam_role')

		return values
