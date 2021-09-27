from model_dataclass.notifications_model import SubscriptionModel
from global_utils import dynamodb_resource, primary_table_name

table = dynamodb_resource.Table(primary_table_name)


def get_notification_settings(payload: SubscriptionModel) -> SubscriptionModel:
	response = table.get_item(
		Key={
			'PK': payload.PK,
			'SK': payload.SK
		}
	)

	payload.__setattr__('receivePromotionalContent', False)
	payload.__setattr__('receiveAnnouncement', False)

	res = response.get('Item', payload)
	if type(res) is dict:
		return SubscriptionModel(**res)
	return res
