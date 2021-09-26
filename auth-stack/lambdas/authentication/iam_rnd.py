import json
import os

import boto3

# import requests

cognito_idp_client = boto3.client('cognito-idp')
iam_client = boto3.client('iam')

def lambda_handler(event, context):
    try:
        cognito_userpool_id = os.environ['USER_POOL_ID']
        cognito_client_id = os.environ['USER_POOL_CLIENT_ID']
        body = json.loads(event["body"])

        list_policy_response = iam_client.list_policy_versions(
            PolicyArn=body['policyArn'],
        )

        # defaultVersion = ''
        # policy_versions = []
        # for policy in list_policy_response['Versions']:
        #     policy_versions.append({
        #         "versionId": policy['VersionId'],
        #         "document": policy['Document'],
        #         "isDefaultVersion": policy['IsDefaultVersion']
        #     })
        
        if len(list_policy_response['Versions']) > 4:
            delete_version_response = iam_client.delete_policy_version(
                PolicyArn=body['policyArn'],
                VersionId=list_policy_response['Versions'][-1]['VersionId']
            )

        updated_permission_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "execute-api:Invoke"
                    ],
                    # "Resource": "*",
                    "Resource": [
                        "arn:aws:execute-api:us-west-2:534678543881:lfln9vsxqf/*/GET/admin-hello",
                        "arn:aws:execute-api:us-west-2:534678543881:lfln9vsxqf/*/GET/user-hello",
                        "*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": "*"
                }
            ]
        }
        update_policy_response = iam_client.create_policy_version(
            PolicyArn=body['policyArn'],
            PolicyDocument=json.dumps(updated_permission_policy),
            SetAsDefault=True
        )


        # permission_policy = {
        #     "Version": "2012-10-17",
        #     "Statement": [
        #         {
        #             "Effect": "Allow",
        #             "Action": [
        #                 "execute-api:Invoke"
        #             ],
        #             # "Resource": "*",
        #             "Resource": [
        #                 "arn:aws:execute-api:us-west-2:534678543881:lfln9vsxqf/*/GET/admin-hello"
        #             ]
        #         },
        #         {
        #             "Effect": "Allow",
        #             "Action": "lambda:InvokeFunction",
        #             "Resource": "*"
        #         }
        #     ]
        # }
        # policy_response = iam_client.create_policy(
        #     PolicyName="PRGM_Custom_Test_Policy",
        #     PolicyDocument=json.dumps(permission_policy),
        #     Description="programmatically created test policy",
        # )

        # role_trust_policy = {
        #     "Version": "2012-10-17",
        #     "Statement": [
        #         {
        #             "Effect": "Allow",
        #             "Principal": {
        #                 "Federated": "cognito-identity.amazonaws.com"
        #         },
        #             "Action": "sts:AssumeRoleWithWebIdentity",
        #             "Condition": {
        #                     "StringEquals": {
        #                     "cognito-identity.amazonaws.com:aud": "us-west-2:e56a30a1-9536-4d74-bf34-280ade955ec2"
        #                 },
        #                     "ForAnyValue:StringLike": {
        #                     "cognito-identity.amazonaws.com:amr": "authenticated"
        #                 }
        #             }
        #         }
        #     ]
        # }
        
        # role_response = iam_client.create_role(
        #     RoleName = "PRGM_Custom_Test_Role",
        #     AssumeRolePolicyDocument = json.dumps(role_trust_policy)
        # )
        # response = iam_client.attach_role_policy(
        #     RoleName='PRGM_Custom_Test_Role', PolicyArn=policy_response['Policy']['Arn'])
        
        
        # try:
        #     list_group_response = cognito_idp_client.list_groups(
        #         UserPoolId=cognito_userpool_id,
        #     )

        #     group_names = [group['GroupName'] for group in list_group_response['Groups']]
        #     if body["group"] not in group_names:
        #         create_group_response = cognito_idp_client.create_group(
        #             GroupName=body["group"],
        #             UserPoolId=cognito_userpool_id,
        #             RoleArn=role_response["Role"]["Arn"],
        #         )

        #     add_user_response = cognito_idp_client.admin_add_user_to_group(
        #         GroupName=body["group"],
        #         UserPoolId=cognito_userpool_id,
        #         Username=body["email"]
        #     )
        # except Exception as ex:
        #     print(ex)

        
        # print("role response: ", role_response)

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
                "message": "Updated policy version",
                # "data": {
                #     # "policyResponse": {
                #     #     "policyId": policy_response["Policy"]["PolicyId"],
                #     #     "policyName": policy_response["Policy"]["PolicyName"],
                #     #     "arn": policy_response["Policy"]["Arn"]
                #     # },
                #     # "roleResponse": {
                #     #     "roleId": role_response["Role"]["RoleId"],
                #     #     "roleName": role_response["Role"]["RoleName"],
                #     #     "arn": role_response["Role"]["Arn"]
                #     # },
                #     # "cognitoResponse": "Added user into group"
                # }
            }),
        }
    except Exception as e:
        # Send some context about this error to Lambda Logs
        print(e)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin":  "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps({
                "error": True,
                "message": "Failed to update policy!",
                "data": str(e)
            }),
        }
