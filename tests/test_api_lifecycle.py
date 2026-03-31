import unittest

from api.server.api_registry import APIRegistry


class APILifecycleTests(unittest.TestCase):
    def test_registry_startup_and_close(self):
        registry = APIRegistry()
        registry.startup()
        self.assertTrue(registry.health_monitor._running)
        self.assertTrue(registry._started)

        registry.close()
        self.assertFalse(registry.health_monitor._running)
        self.assertFalse(registry._started)


if __name__ == "__main__":
    unittest.main()
