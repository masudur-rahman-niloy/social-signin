import json


def lambda_handler(event, context):

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
        "body": json.dumps({
            "error": False,
            "code": 'GENERIC',
            "message": 'proxy test successful',
            "data": {}
        }),
    }
