from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from threading import RLock
from typing import Optional, List, Dict, Any

from models.ai_prescription import AIPrescription


class PrescriptionRepositoryError(Exception):
    pass


class PrescriptionRepository:
    """
    Institutional AI Prescription Repository

    Responsibilities:
    - Persist AIPrescription objects
    - Track lifecycle (pending / applied / expired)
    - Track user confirmation
    - Enable follow-up performance evaluation
    - Enable recovery-safe config re-application
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "prescription_store.db"):

        self._lock = RLock()
        self._db_path = Path(db_path)
        self._connection = None

        self._initialize()

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def _initialize(self):

        with self._lock:

            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )

            self._connection.execute("PRAGMA journal_mode=WAL;")
            self._connection.execute("PRAGMA synchronous=FULL;")

            self._create_schema()

    def _create_schema(self):

        cursor = self._connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                prescription_id TEXT PRIMARY KEY,
                diagnosis_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                actions_json TEXT NOT NULL,
                narrative TEXT,
                status TEXT NOT NULL,
                user_confirmed INTEGER NOT NULL,
                applied_at TEXT,
                followup_due TEXT,
                schema_version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prescription_account
            ON prescriptions (account_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prescription_status
            ON prescriptions (status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_followup_due
            ON prescriptions (followup_due)
        """)

        self._connection.commit()

    # ==========================================================
    # SAVE / UPSERT
    # ==========================================================

    def save(self, prescription: AIPrescription):

        if not isinstance(prescription, AIPrescription):
            raise PrescriptionRepositoryError("Invalid AIPrescription object")

        with self._lock:

            payload = self._serialize(prescription)

            try:
                cursor = self._connection.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO prescriptions (
                        prescription_id,
                        diagnosis_id,
                        account_id,
                        actions_json,
                        narrative,
                        status,
                        user_confirmed,
                        applied_at,
                        followup_due,
                        schema_version,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, payload)

                self._connection.commit()

            except sqlite3.Error as e:
                self._connection.rollback()
                raise PrescriptionRepositoryError(str(e))

    # ==========================================================
    # READ OPERATIONS
    # ==========================================================

    def get(self, prescription_id: str) -> Optional[AIPrescription]:

        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT * FROM prescriptions WHERE prescription_id = ?",
                (prescription_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return self._deserialize(row)

    def get_by_account(
        self,
        account_id: str,
        status: Optional[str] = None
    ) -> List[AIPrescription]:

        query = """
            SELECT * FROM prescriptions
            WHERE account_id = ?
        """

        params: List[Any] = [account_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._deserialize(r) for r in rows]

    def get_pending_confirmations(
        self,
        account_id: str
    ) -> List[AIPrescription]:

        return self.get_by_account(account_id, status="pending")

    # ==========================================================
    # STATUS MANAGEMENT
    # ==========================================================

    def mark_confirmed(self, prescription_id: str, applied_at: str):

        with self._lock:
            cursor = self._connection.cursor()

            cursor.execute("""
                UPDATE prescriptions
                SET user_confirmed = 1,
                    status = 'applied',
                    applied_at = ?,
                    updated_at = ?
                WHERE prescription_id = ?
            """, (applied_at, applied_at, prescription_id))

            self._connection.commit()

    def mark_expired(self, prescription_id: str, timestamp: str):

        with self._lock:
            cursor = self._connection.cursor()

            cursor.execute("""
                UPDATE prescriptions
                SET status = 'expired',
                    updated_at = ?
                WHERE prescription_id = ?
            """, (timestamp, prescription_id))

            self._connection.commit()

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def _serialize(self, prescription: AIPrescription):

        d = prescription.to_dict()

        return (
            d["prescription_id"],
            d["diagnosis_id"],
            d["account_id"],
            json.dumps(d.get("actions", [])),
            d.get("narrative"),
            d.get("status"),
            int(d.get("user_confirmed", False)),
            d.get("applied_at"),
            d.get("followup_due"),
            self.SCHEMA_VERSION,
            d["created_at"],
            d["updated_at"],
        )

    def _deserialize(self, row):

        columns = [
            "prescription_id",
            "diagnosis_id",
            "account_id",
            "actions_json",
            "narrative",
            "status",
            "user_confirmed",
            "applied_at",
            "followup_due",
            "schema_version",
            "created_at",
            "updated_at",
        ]

        record = dict(zip(columns, row))

        data = {
            "prescription_id": record["prescription_id"],
            "diagnosis_id": record["diagnosis_id"],
            "account_id": record["account_id"],
            "actions": json.loads(record["actions_json"]),
            "narrative": record["narrative"],
            "status": record["status"],
            "user_confirmed": bool(record["user_confirmed"]),
            "applied_at": record["applied_at"],
            "followup_due": record["followup_due"],
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
        }

        return AIPrescription.from_dict(data)

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None