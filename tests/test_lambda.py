import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

LAMBDA_FILE = Path(__file__).resolve().parents[1] / "src" / "lambda_function.py"


class TestClientRequestsLambda(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.env_patch = patch.dict(os.environ, {"TABLE_NAME": "TestClientRequests"})
		cls.env_patch.start()

		cls.boto_patch = patch("boto3.resource")
		mock_resource = cls.boto_patch.start()
		cls.mock_table = MagicMock()
		mock_resource.return_value.Table.return_value = cls.mock_table

		spec = importlib.util.spec_from_file_location("client_requests_lambda", LAMBDA_FILE)
		cls.app = importlib.util.module_from_spec(spec)
		sys.modules[spec.name] = cls.app
		spec.loader.exec_module(cls.app)

	@classmethod
	def tearDownClass(cls):
		cls.boto_patch.stop()
		cls.env_patch.stop()

	def setUp(self):
		self.mock_table.reset_mock()
		self.mock_table.get_item.return_value = {}

	def event(self, route, user_id="user-123", body=None, request_id=None):
		method, _ = route.split(" ", 1)
		event = {
			"routeKey": route,
			"requestContext": {
				"authorizer": {"jwt": {"claims": {"sub": user_id}}},
				"http": {"method": method},
			},
			"rawPath": "/requests",
		}

		if body is not None:
			event["body"] = json.dumps(body)

		if request_id:
			event["pathParameters"] = {"requestId": request_id}
			event["rawPath"] = f"/requests/{request_id}"

		return event

	def test_requires_authentication(self):
		event = self.event("POST /requests")
		event["requestContext"]["authorizer"] = {}

		result = self.app.lambda_handler(event, None)

		self.assertEqual(result["statusCode"], 401)
		self.mock_table.put_item.assert_not_called()

	def test_creates_request(self):
		event = self.event(
			"POST /requests",
			body={"clientName": "Example Client", "description": "Help requested"},
		)

		result = self.app.lambda_handler(event, None)
		body = json.loads(result["body"])

		self.assertEqual(result["statusCode"], 201)
		self.assertEqual(body["status"], "PENDING")

		saved_item = self.mock_table.put_item.call_args.kwargs["Item"]
		self.assertEqual(saved_item["ownerId"], "user-123")
		self.assertEqual(saved_item["userId"], body["requestId"])

	def test_rejects_missing_description(self):
		event = self.event("POST /requests", body={"clientName": "Example Client"})

		result = self.app.lambda_handler(event, None)

		self.assertEqual(result["statusCode"], 400)
		self.mock_table.put_item.assert_not_called()

	def test_gets_own_request(self):
		self.mock_table.get_item.return_value = {
			"Item": {
				"userId": "request-123",
				"ownerId": "user-123",
				"clientName": "Example Client",
				"description": "Help requested",
				"status": "PENDING",
				"createdAt": "2026-10-18T10:00:00+00:00",
			}
		}

		result = self.app.lambda_handler(
			self.event("GET /requests/{requestId}", request_id="request-123"),
			None,
		)

		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(json.loads(result["body"])["requestId"], "request-123")

	def test_blocks_other_users_request(self):
		self.mock_table.get_item.return_value = {
			"Item": {
				"userId": "request-123",
				"ownerId": "another-user",
			}
		}

		result = self.app.lambda_handler(
			self.event("GET /requests/{requestId}", request_id="request-123"),
			None,
		)

		self.assertEqual(result["statusCode"], 404)


if __name__ == "__main__":
	unittest.main()
