# pylint: disable=unused-argument
import json


def handle(event, context):
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status ": "Lambda works!"})}
