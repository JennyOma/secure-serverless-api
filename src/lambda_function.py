
import base64
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    user_id = claims.get("sub")
    if not user_id:
        return response(401, {"error": "Authentication required"})

    route = event.get("routeKey", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")

    try:
        if route == "POST /requests" or (method == "POST" and path == "/requests"):
            raw_body = event.get("body") or "{}"

            if event.get("isBase64Encoded"):
                try:
                    raw_body = base64.b64decode(raw_body, validate=True).decode("utf-8")
                except (ValueError, UnicodeDecodeError):
                    return response(400, {"error": "Invalid request body"})

            try:
                body = json.loads(raw_body)
            except (json.JSONDecodeError, TypeError):
                return response(400, {"error": "Invalid JSON body"})

            if not isinstance(body, dict):
                return response(400, {"error": "JSON body must be an object"})

            client_name = body.get("clientName")
            description = body.get("description")

            if not isinstance(client_name, str) or not client_name.strip():
                return response(400, {"error": "clientName is required"})

            if not isinstance(description, str) or not description.strip():
                return response(400, {"error": "description is required"})

            request_id = str(uuid.uuid4())

            item = {
                "userId": request_id,
                "ownerId": user_id,
                "clientName": client_name.strip(),
                "description": description.strip(),
                "status": "PENDING",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }

            table.put_item(Item=item)

            return response(201, {
                "message": "Client request created",
                "requestId": request_id,
                "status": "PENDING",
            })

        if route == "GET /requests/{requestId}" or (
            method == "GET" and path.startswith("/requests/")
        ):
            request_id = (event.get("pathParameters") or {}).get("requestId")

            if not request_id and path.startswith("/requests/"):
                request_id = path.removeprefix("/requests/")

            if not request_id:
                return response(400, {"error": "requestId is required"})

            result = table.get_item(Key={"userId": request_id})
            item = result.get("Item")

            if not item or item.get("ownerId") != user_id:
                return response(404, {"error": "Request not found"})

            return response(200, {
                "requestId": item["userId"],
                "clientName": item["clientName"],
                "description": item["description"],
                "status": item["status"],
                "createdAt": item["createdAt"],
            })

        return response(404, {"error": "Route not found"})

    except ClientError:
        return response(500, {"error": "Unable to process request"})
