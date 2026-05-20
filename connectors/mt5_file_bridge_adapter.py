from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import json
import shutil
import time

from connectors.broker_adapter import BaseBrokerAdapter, NormalizedEventBuilder


class MT5FileBridgeAdapter(BaseBrokerAdapter):
    """
    Polls a filesystem inbox written by an external MT5 EA/desktop bridge.

    Expected raw event shape:
    {
      "event_type": "TRADE_FILLED" | "TRADE_CLOSED" | "POSITION_MODIFIED" | "SCALE_IN" | "PARTIAL_CLOSE" | "ACCOUNT_STATE" | "OPEN_POSITIONS_SYNC",
      "payload": {...}
    }

    Alternate legacy fields accepted:
    - "type"
    - flat payload without nested "payload"
    """

    def __init__(
        self,
        broker_id: str,
        inbox_dir: str,
        archive_dir: Optional[str] = None,
        poll_interval_seconds: float = 0.25,
    ):
        super().__init__()
        self._broker_id = broker_id
        self._inbox_dir = Path(inbox_dir)
        self._archive_dir = Path(archive_dir) if archive_dir else self._inbox_dir / "processed"
        self._poll_interval_seconds = max(float(poll_interval_seconds), 0.05)
        self._last_event_at: Optional[str] = None
        self._last_event_type: Optional[str] = None
        self._last_event_file: Optional[str] = None

    def _connect_impl(self):
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        self._archive_dir.mkdir(parents=True, exist_ok=True)

    def _disconnect_impl(self):
        return None

    def _snapshot_json_files(self, directory: Path) -> list[tuple[Path, float]]:
        if not directory.exists():
            return []
        files: list[tuple[Path, float]] = []
        for path in directory.glob("*.json"):
            try:
                if not path.is_file():
                    continue
                files.append((path, path.stat().st_mtime))
            except OSError:
                continue
        return sorted(files, key=lambda item: (item[1], item[0].name))

    def _poll_event(self) -> Optional[Dict[str, Any]]:
        for path, _mtime in self._snapshot_json_files(self._inbox_dir):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                archived_path = self._archive_dir / path.name
                shutil.move(str(path), str(archived_path))
                self._last_event_at = datetime.now(timezone.utc).isoformat()
                self._last_event_type = str(payload.get("event_type") or payload.get("type") or "unknown")
                self._last_event_file = path.name
                return payload
            except FileNotFoundError:
                continue
            except Exception:
                failed_path = self._archive_dir / f"failed_{int(time.time() * 1000)}_{path.name}"
                try:
                    shutil.move(str(path), str(failed_path))
                except (FileNotFoundError, OSError):
                    pass
        time.sleep(self._poll_interval_seconds)
        return None

    def _normalize_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = raw_event.get("event_type") or raw_event.get("type")
        if not event_type:
            raise ValueError("MT5 bridge event missing event_type")

        payload = raw_event.get("payload")
        if payload is None:
            payload = {k: v for k, v in raw_event.items() if k not in {"event_type", "type"}}
        if not isinstance(payload, dict):
            raise ValueError("MT5 bridge payload must be dict")

        payload = dict(payload)
        payload.setdefault("broker_id", self._broker_id)
        return NormalizedEventBuilder.build_event(event_type=event_type, payload=payload)

    def supports_order_ticket_submission(self) -> bool:
        return False

    def submit_order_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider": self._broker_id,
            "status": "sync_only",
            "supported": False,
            "message": "MT5 integration is sync-only. Place trades in MT5 and MyPlatform will import historical, open, and future trade updates automatically.",
        }

    def self_test(self) -> Dict[str, Any]:
        """
        Write a test file to the inbox, poll for it, verify it archives.
        Returns a detailed result dict with pass/fail per step.
        """
        steps: list[dict[str, Any]] = []
        self._connect_impl()

        # Step 1: check inbox exists and is writable
        inbox_ok = self._inbox_dir.exists()
        writable = os.access(self._inbox_dir, os.W_OK)
        steps.append({"step": "inbox_writable", "ok": inbox_ok and writable, "detail": str(self._inbox_dir)})

        # Step 2: write a test file
        test_filename = f"__self_test_{uuid.uuid4().hex[:8]}.json"
        test_payload = {"event_type": "SELF_TEST", "payload": {"ts": time.time(), "source": "self_test"}}
        try:
            test_path = self._inbox_dir / test_filename
            test_path.write_text(json.dumps(test_payload), encoding="utf-8")
            steps.append({"step": "write_test_file", "ok": True, "detail": str(test_path)})
        except Exception as exc:
            steps.append({"step": "write_test_file", "ok": False, "detail": str(exc)})
            return {"overall": "FAIL", "steps": steps}

        # Step 3: poll for the file
        try:
            polled = self._poll_event()
            if polled is not None and polled.get("event_type") == "SELF_TEST":
                steps.append({"step": "poll_event", "ok": True, "detail": "Test file polled successfully"})
            else:
                steps.append({"step": "poll_event", "ok": False, "detail": f"Expected SELF_TEST, got {polled.get('event_type') if polled else 'None'}"})
        except Exception as exc:
            steps.append({"step": "poll_event", "ok": False, "detail": str(exc)})

        # Step 4: check file moved to archive
        archived = self._archive_dir / test_filename
        failed_archived = list(self._archive_dir.glob(f"failed_*_{test_filename}"))
        if archived.exists():
            steps.append({"step": "file_archived", "ok": True, "detail": str(archived)})
            # clean up
            try:
                archived.unlink()
            except Exception:
                pass
        elif failed_archived:
            steps.append({"step": "file_archived", "ok": False, "detail": f"File moved to failed bucket: {failed_archived[0]}"})
        else:
            steps.append({"step": "file_archived", "ok": False, "detail": f"Not found in archive dir ({self._archive_dir})"})
            # orphan cleanup — scan for any self-test files left in inbox
            for orphan in self._inbox_dir.glob("__self_test_*.json"):
                try:
                    orphan.unlink()
                except Exception:
                    pass

        # Step 5: verify archive is writable
        archive_ok = self._archive_dir.exists()
        archive_writable = os.access(self._archive_dir, os.W_OK)
        steps.append({"step": "archive_writable", "ok": archive_ok and archive_writable, "detail": str(self._archive_dir)})

        passed = all(s["ok"] for s in steps)
        return {"overall": "PASS" if passed else "FAIL", "steps": steps}

    def get_health_snapshot(self) -> Dict[str, Any]:
        inbox_files = self._snapshot_json_files(self._inbox_dir)
        archive_files = self._snapshot_json_files(self._archive_dir)
        newest_inbox = max((mtime for _path, mtime in inbox_files), default=None)
        newest_archive = max((mtime for _path, mtime in archive_files), default=None)
        return {
            "connected": self.is_connected(),
            "status": "connected" if self.is_connected() else "disconnected",
            "inbox_pending_count": len(inbox_files),
            "archive_file_count": len(archive_files),
            "last_event_at": self._last_event_at,
            "last_event_type": self._last_event_type,
            "last_event_file": self._last_event_file,
            "latest_inbox_mtime": datetime.fromtimestamp(newest_inbox, timezone.utc).isoformat() if newest_inbox else None,
            "latest_archive_mtime": datetime.fromtimestamp(newest_archive, timezone.utc).isoformat() if newest_archive else None,
            "bridge_alive": self.is_connected(),
            "inbox_dir": str(self._inbox_dir),
            "archive_dir": str(self._archive_dir),
        }

    @property
    def inbox_dir(self) -> str:
        return str(self._inbox_dir)

    @property
    def archive_dir(self) -> str:
        return str(self._archive_dir)
