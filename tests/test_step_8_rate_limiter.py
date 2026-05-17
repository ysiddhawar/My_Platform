import unittest
from unittest.mock import Mock, AsyncMock

from starlette.requests import Request


class RateLimiterTests(unittest.TestCase):
    """
    Smoke tests for the custom rate limiter implementation.

    Tests the InMemoryBucket and RateLimitMiddleware directly
    to verify sliding-window rate limiting works.
    """

    def setUp(self):
        # Import here so failures cause a clear import error
        from api.server.rate_limiter import InMemoryBucket, RateLimitMiddleware
        self.InMemoryBucket = InMemoryBucket
        self.RateLimitMiddleware = RateLimitMiddleware

        # Reset buckets by reimporting (in production this is fine since
        # buckets are per-process; for testing we create fresh instances)
        import api.server.rate_limiter as rl
        
        # Force re-creation of buckets for test isolation
        import importlib
        importlib.reload(rl)
        self.rate_limiter = rl

    # ------------------------------------------------------------------
    # InMemoryBucket Tests
    # ------------------------------------------------------------------

    def test_bucket_allows_initial_requests(self):
        bucket = self.InMemoryBucket(max_requests=5, window_seconds=60)
        for _ in range(5):
            self.assertTrue(bucket.is_allowed("test_key"))

    def test_bucket_rejects_excess_requests(self):
        bucket = self.InMemoryBucket(max_requests=3, window_seconds=60)
        for _ in range(3):
            bucket.is_allowed("test_key")
        self.assertFalse(bucket.is_allowed("test_key"))

    def test_bucket_has_separate_keys(self):
        bucket = self.InMemoryBucket(max_requests=3, window_seconds=60)
        for _ in range(3):
            bucket.is_allowed("key_a")
        # key_a should be exhausted
        self.assertFalse(bucket.is_allowed("key_a"))
        # key_b should still be allowed
        self.assertTrue(bucket.is_allowed("key_b"))

    def test_bucket_remaining_returns_correct_count(self):
        bucket = self.InMemoryBucket(max_requests=10, window_seconds=60)
        # 10 remaining initially
        self.assertEqual(bucket.remaining("test_key"), 10)
        bucket.is_allowed("test_key")
        # 9 remaining after one request
        self.assertEqual(bucket.remaining("test_key"), 9)
        for _ in range(9):
            bucket.is_allowed("test_key")
        # 0 remaining after all requests
        self.assertEqual(bucket.remaining("test_key"), 0)

    def test_bucket_window_expires(self):
        """
        Test that the window resets after the time window.
        We use a very short window to avoid waiting.
        """
        import time
        bucket = self.InMemoryBucket(max_requests=2, window_seconds=0.05)
        self.assertTrue(bucket.is_allowed("test_key"))
        self.assertTrue(bucket.is_allowed("test_key"))
        self.assertFalse(bucket.is_allowed("test_key"))
        # Wait for window to expire
        time.sleep(0.1)
        self.assertTrue(bucket.is_allowed("test_key"))

    # ------------------------------------------------------------------
    # RateLimit Bucket Resolution Tests
    # ------------------------------------------------------------------

    def test_resolve_bucket_returns_most_specific(self):
        """
        Given the RATE_LIMITS tuple, ensure that longer matching prefixes
        are preferred over shorter ones.
        """
        resolver = getattr(self.rate_limiter, '_resolve_bucket', None)
        if not resolver:
            self.skipTest("Skipping: cannot access _resolve_bucket")

        # Jog resolution - /api/v1/execution-tools is a known prefix
        bucket = resolver("/api/v1/execution-tools/execute-trade")
        self.assertEqual(bucket._max_requests, 30)

        # Auth bucket
        auth_bucket = resolver("/api/v1/auth/login")
        self.assertEqual(auth_bucket._max_requests, 10)

        # Default bucket for unknown path
        default_bucket = resolver("/api/v1/unknown-route")
        self.assertEqual(default_bucket._max_requests, 60)

    # ------------------------------------------------------------------
    # Middleware Architecture Tests
    # ------------------------------------------------------------------

    def test_middleware_allows_health_and_options(self):
        """
        The middleware should not rate-limit health endpoints or OPTIONS preflight.
        """
        middleware = self.RateLimitMiddleware(app=Mock())

        async def call_next(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"status": "ok"})

        import asyncio

        # Health path
        scope_health = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": [],
        }
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        req_health = Request(scope_health, receive)
        response = asyncio.run(middleware.dispatch(req_health, call_next))
        self.assertEqual(response.status_code, 200)

        # Options preflight
        scope_options = {
            "type": "http",
            "method": "OPTIONS",
            "path": "/api/v1/auth/login",
            "headers": [],
        }
        req_options = Request(scope_options, receive)
        response = asyncio.run(middleware.dispatch(req_options, call_next))
        self.assertEqual(response.status_code, 200)

    def test_middleware_returns_429_on_excess(self):
        """
        After exhausting the auth rate limit, the middleware should return 429.
        """
        middleware = self.RateLimitMiddleware(app=Mock())

        async def call_next(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"status": "ok"})

        import asyncio

        def make_request(path: str):
            scope = {
                "type": "http",
                "method": "POST",
                "path": path,
                "headers": [
                    (b"host", b"localhost"),
                ],
                "client": ("127.0.0.1", 54321),
            }
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}
            return Request(scope, receive)

        # Auth bucket allows 10 req/min — exhaust it and check 429
        for _ in range(10):
            response = asyncio.run(middleware.dispatch(make_request("/api/v1/auth/login"), call_next))
            self.assertEqual(response.status_code, 200,
                             msg=f"Expected 200, got {response.status_code} at iteration {_}")

        # The 11th request should be 429
        response = asyncio.run(middleware.dispatch(make_request("/api/v1/auth/login"), call_next))
        self.assertEqual(response.status_code, 429)

        # Check the 429 response has proper headers
        body = response.body.decode() if hasattr(response, 'body') else ''
        self.assertIn("Too many requests", body)

    def test_middleware_returns_retry_after_header(self):
        """
        The 429 response should include X-RateLimit-Remaining and Retry-After headers.
        """
        middleware = self.RateLimitMiddleware(app=Mock())

        async def call_next(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"status": "ok"})

        import asyncio

        def make_request(path: str):
            scope = {
                "type": "http",
                "method": "POST",
                "path": path,
                "headers": [],
                "client": ("192.168.1.1", 12345),
            }
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}
            return Request(scope, receive)

        # Exhaust auth bucket
        for _ in range(10):
            asyncio.run(middleware.dispatch(make_request("/api/v1/auth/login"), call_next))

        response = asyncio.run(middleware.dispatch(make_request("/api/v1/auth/login"), call_next))
        self.assertEqual(response.status_code, 429)

        # Check for rate limit headers
        headers = dict(response.headers)
        self.assertIn("x-ratelimit-remaining", headers, "Missing X-RateLimit-Remaining header")
        self.assertIn("retry-after", headers, "Missing Retry-After header")

    def test_middleware_allows_default_rate_for_unlisted_paths(self):
        """
        Paths not explicitly listed should fall back to the default rate limit.
        """
        middleware = self.RateLimitMiddleware(app=Mock())

        async def call_next(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"status": "ok"})

        import asyncio

        def make_request(path: str):
            scope = {
                "type": "http",
                "method": "GET",
                "path": path,
                "headers": [],
                "client": ("10.0.0.1", 9876),
            }
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}
            return Request(scope, receive)

        # Default limit is 60 req/min — all 60 should pass
        for i in range(60):
            response = asyncio.run(middleware.dispatch(make_request("/api/v1/some-random-path"), call_next))
            self.assertEqual(response.status_code, 200,
                             msg=f"Expected 200 at index {i}, got {response.status_code}")

        # The 61st should fail
        response = asyncio.run(middleware.dispatch(make_request("/api/v1/some-random-path"), call_next))
        self.assertEqual(response.status_code, 429)

    def test_middleware_disabled_respects_flag(self):
        """
        When disabled, the middleware should always pass requests through.
        """
        from api.server.rate_limiter import RateLimitMiddleware
        middleware = RateLimitMiddleware(app=Mock(), enabled=False)

        async def call_next(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"status": "ok"})

        import asyncio

        def make_request(path: str):
            scope = {
                "type": "http",
                "method": "POST",
                "path": path,
                "headers": [],
                "client": ("10.0.0.1", 1234),
            }
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}
            return Request(scope, receive)

        # Even 100 requests on the auth endpoint should pass when disabled
        for i in range(100):
            response = asyncio.run(middleware.dispatch(make_request("/api/v1/auth/login"), call_next))
            self.assertEqual(response.status_code, 200,
                             msg=f"Expected 200 with disabled middleware at index {i}, got {response.status_code}")

    def test_environment_variable_config(self):
        """
        Verify that environment variable overrides work correctly.
        """
        import os
        from api.server.rate_limiter import _env_int

        # Test default fallback
        self.assertEqual(_env_int("NONEXISTENT_VAR_12345", 42), 42)

        # Test reading from env
        os.environ["TEST_RATE_LIMIT_VALUE"] = "25"
        self.assertEqual(_env_int("TEST_RATE_LIMIT_VALUE", 10), 25)
        del os.environ["TEST_RATE_LIMIT_VALUE"]

        # Test invalid env value falls back to default
        os.environ["TEST_RATE_LIMIT_BAD"] = "not_a_number"
        self.assertEqual(_env_int("TEST_RATE_LIMIT_BAD", 99), 99)
        del os.environ["TEST_RATE_LIMIT_BAD"]


if __name__ == "__main__":
    unittest.main()