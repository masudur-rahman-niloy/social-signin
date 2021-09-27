from pydantic import constr, conint, BaseModel


class AccessManagementModel(BaseModel):
	access_id: int = 0
	module_id: int = 0
	module_name: constr(min_length=1)
	group_id: conint()
	add_status: bool = True
	update_status: bool = True
	delete_status: bool = True
	list_status: bool = True
