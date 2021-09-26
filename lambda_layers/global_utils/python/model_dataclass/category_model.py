from pydantic import constr, conint, BaseModel


class CategoryModel(BaseModel):
	cat_id: int = 0
	cat_name: constr(min_length=1)
	status: bool
	parent_catid: conint() = None
	is_featured: bool = False
