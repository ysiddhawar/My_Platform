import tempfile
import unittest
from pathlib import Path

from api.server.auth_service import AuthService
from persistence_layer.session_repository import SessionRepository
from persistence_layer.user_repository import UserRepository


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.user_repository = UserRepository(db_path=str(base / "users.db"))
        self.session_repository = SessionRepository(db_path=str(base / "sessions.db"))
        self.auth_service = AuthService(
            user_repository=self.user_repository,
            session_repository=self.session_repository,
        )

    def tearDown(self):
        self.session_repository.close()
        self.user_repository.close()
        self._tmp.cleanup()

    def test_user_login_logout_roundtrip(self):
        created = self.auth_service.create_user(
            username="tester",
            password="StrongPass123",
            account_ids=["ACC-1"],
            roles=["user"],
        )
        self.assertEqual(created["user"]["username"], "tester")

        login = self.auth_service.login("tester", "StrongPass123")
        self.assertTrue(login["token"])

        auth = self.auth_service.authenticate_token(login["token"])
        self.assertEqual(auth["user"]["username"], "tester")
        self.assertTrue(self.auth_service.has_account_access(auth["user"], "ACC-1"))
        self.assertFalse(self.auth_service.has_account_access(auth["user"], "ACC-2"))

        logout = self.auth_service.logout(login["token"])
        self.assertEqual(logout["status"], "logged_out")

        with self.assertRaises(Exception):
            self.auth_service.authenticate_token(login["token"])

    def test_bootstrap_only_once(self):
        first = self.auth_service.bootstrap_admin(
            username="admin",
            password="AdminPass123",
        )
        self.assertIn("admin", first["user"]["roles"])

        with self.assertRaises(Exception):
            self.auth_service.bootstrap_admin(
                username="admin2",
                password="AdminPass123",
            )


if __name__ == "__main__":
    unittest.main()
