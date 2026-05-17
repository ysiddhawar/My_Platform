from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from threading import RLock
from typing import Optional, List, Dict, Any

from models.ai_diagnosis import AIDiagnosis


class DiagnosisRepositoryError(Exception):
    pass


class DiagnosisRepository:
    """
    Institutional AI Diagnosis Repository

    Responsibilities:
    - Persist AIDiagnosis objects
    - Maintain AI audit history
    - Enable longitudinal behavioral analysis
    - Enable replay & recovery compatibility
    - Support versioned schema
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "diagnosis_store.db"):

        self._lock = RLock()
        self._db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

        self._initialize()

    @property
    def _conn(self) -> sqlite3.Connection:
        assert self._connection is not None
        return self._connection

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def _initialize(self):

        with self._lock:

            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )

            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=FULL;")

            self._create_schema()

    def _create_schema(self):

        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                diagnosis_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                risk_tier TEXT,
                health_score REAL,
                findings_json TEXT NOT NULL,
                strengths_json TEXT NOT NULL,
                metadata_json TEXT,
                schema_version INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnosis_account
            ON diagnoses (account_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON diagnoses (created_at)
        """)

        self._conn.commit()

    # ==========================================================
    # SAVE / UPSERT
    # ==========================================================

    def save(self, diagnosis: AIDiagnosis):

        if not isinstance(diagnosis, AIDiagnosis):
            raise DiagnosisRepositoryError("Invalid AIDiagnosis object")

        with self._lock:

            payload = self._serialize(diagnosis)

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO diagnoses (
                        diagnosis_id,
                        account_id,
                        risk_tier,
                        health_score,
                        findings_json,
                        strengths_json,
                        metadata_json,
                        schema_version,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, payload)

                self._conn.commit()

            except sqlite3.Error as e:
                self._conn.rollback()
                raise DiagnosisRepositoryError(str(e))

    # ==========================================================
    # READ OPERATIONS
    # ==========================================================

    def get(self, diagnosis_id: str) -> Optional[AIDiagnosis]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM diagnoses WHERE diagnosis_id = ?",
                (diagnosis_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return self._deserialize(row)

    def get_by_account(
        self,
        account_id: str,
        limit: Optional[int] = None
    ) -> List[AIDiagnosis]:

        query = """
            SELECT * FROM diagnoses
            WHERE account_id = ?
            ORDER BY created_at DESC
        """

        if limit:
            query += f" LIMIT {int(limit)}"

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, (account_id,))
            rows = cursor.fetchall()

        return [self._deserialize(r) for r in rows]

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def _serialize(self, diagnosis: AIDiagnosis):

        d = diagnosis.to_dict()

        return (
            d["diagnosis_id"],
            d["account_id"],
            d.get("risk_tier"),
            d.get("health_score"),
            json.dumps(d.get("findings", [])),
            json.dumps(d.get("strengths", [])),
            json.dumps(d.get("metadata", {})),
            self.SCHEMA_VERSION,
            d["created_at"],
        )

    def _deserialize(self, row):

        columns = [
            "diagnosis_id",
            "account_id",
            "risk_tier",
            "health_score",
            "findings_json",
            "strengths_json",
            "metadata_json",
            "schema_version",
            "created_at",
        ]

        record = dict(zip(columns, row))

        data = {
            "diagnosis_id": record["diagnosis_id"],
            "account_id": record["account_id"],
            "risk_tier": record["risk_tier"],
            "health_score": record["health_score"],
            "findings": json.loads(record["findings_json"]),
            "strengths": json.loads(record["strengths_json"]),
            "metadata": json.loads(record["metadata_json"]) if record["metadata_json"] else {},
            "created_at": record["created_at"],
        }

        return AIDiagnosis.from_dict(data)

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._conn.close()
                self._connection: sqlite3.Connection | None = None