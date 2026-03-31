import asyncio
import uuid
import unittest

from fastapi.responses import JSONResponse
from starlette.requests import Request

from api.server.api_registry import api_registry
from api.server.security import AuthenticationMiddleware, ensure_account_access


class APISecurityTests(unittest.TestCase):
    def _make_request(self, path: str, headers: dict | None = None) -> Request:
        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in (headers or {}).items()
            ],
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        return Request(scope, receive)

    def test_auth_middleware_requires_token_for_protected_path(self):
        middleware = AuthenticationMiddleware(app=lambda scope, receive, send: None)

        async def call_next(request):
            return JSONResponse({"status": "ok"})

        response = asyncio.run(middleware.dispatch(self._make_request("/api/v1/journal/trades"), call_next))
        self.assertEqual(response.status_code, 401)

    def test_auth_middleware_allows_public_auth_path(self):
        middleware = AuthenticationMiddleware(app=lambda scope, receive, send: None)

        async def call_next(request):
            return JSONResponse({"status": "ok"})

        response = asyncio.run(middleware.dispatch(self._make_request("/api/v1/auth/login"), call_next))
        self.assertEqual(response.status_code, 200)

    def test_ownership_helper(self):
        username = f"sec_{uuid.uuid4().hex[:8]}"
        created = api_registry.auth_service.create_user(
            username=username,
            password="StrongPass123",
            account_ids=["ACC-SEC-1"],
            roles=["user"],
        )
        user = created["user"]
        ensure_account_access(user, "ACC-SEC-1")
        with self.assertRaises(Exception):
            ensure_account_access(user, "ACC-SEC-2")


if __name__ == "__main__":
    unittest.main()
