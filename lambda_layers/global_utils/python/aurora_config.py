import pymysql
from global_utils import *

sm_client = boto3.client('secretsmanager')
db_secret = os.environ.get('AURORA_DB_SECRET', None)
host = os.environ.get('AURORA_CLUSTER_HOST', None)
database_name = None

connection = None
dict_connection = None

if db_secret:
    sm_response = sm_client.get_secret_value(SecretId=db_secret)
    secret = json.loads(sm_response['SecretString'])
    database_name = secret['dbname']
    connection = pymysql.connect(host=host, user=secret['username'], password=secret['password'],
                                 database=secret['dbname'], connect_timeout=5)
    dict_connection = pymysql.connect(
        host=host,
        user=secret['username'],
        password=secret['password'],
        database=secret['dbname'],
        connect_timeout=5,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    print(connection)


