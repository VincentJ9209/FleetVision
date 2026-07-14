from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from fleetvision.review.annotation_correction_review_mapping import (
    CanonicalCorrectionFields,
    CorrectionReviewSelection,
)
from fleetvision.review.annotation_correction_review_package import VerifiedCorrectionReviewPackage


class CorrectionReviewStateError(RuntimeError):
    """Raised when local Phase 04.5M state is inconsistent or unsafe."""


@dataclass(frozen=True)
class StoredCorrectionReview:
    correction_case_id: str
    selection: Mapping[str, Any]
    canonical_fields: Mapping[str, str]
    revision: int
    saved_at_utc: str


@dataclass(frozen=True)
class CorrectionProgressCounts:
    total: int
    reviewed: int
    pending: int
    needs_adjudication: int


class CorrectionReviewStateStore:
    _SUPPORTED_FILTERS = {"all", "pending", "reviewed", "needs_adjudication"}

    def __init__(self, workspace_root: Path, *, backup_retention: int) -> None:
        if backup_retention <= 0:
            raise CorrectionReviewStateError("backup_retention 必須是正整數")
        self.workspace_root = workspace_root.resolve()
        self.state_dir = self.workspace_root
        self.backup_dir = self.workspace_root / "backups"
        self.export_dir = self.workspace_root.parent / "exports"
        self.database_path = self.workspace_root / "correction_review_state.sqlite3"
        self.event_log_path = self.workspace_root / "correction_review_events.jsonl"
        self.backup_retention = backup_retention

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _canonical_json(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _workspace_identity(self, package: VerifiedCorrectionReviewPackage) -> dict[str, str]:
        return {
            "schema_version": package.config.schema_version,
            "workspace_root": str(package.workspace_root),
            "source_csv_sha256": package.source_csv_sha256,
            "source_manifest_sha256": package.source_manifest_sha256,
            "source_contract_sha256": package.source_contract_sha256,
            "package_gate_sha256": package.package_gate_sha256,
            "reviewer": package.config.reviewer,
            "timezone": package.config.timezone,
            "expected_case_count": str(len(package.cases)),
        }

    def _expected_cases(self, package: VerifiedCorrectionReviewPackage) -> list[tuple[str, int, str, str, str]]:
        return [
            (case.correction_case_id, case.case_index, case.review_case_id, case.source_case_fingerprint, case.image_id)
            for case in package.cases
        ]

    def initialize(self, package: VerifiedCorrectionReviewPackage) -> None:
        if package.app_workspace_root.resolve() != self.workspace_root:
            raise CorrectionReviewStateError("state workspace 與 verified package 不一致")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        identity = self._workspace_identity(package)
        expected_cases = self._expected_cases(package)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workspace_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS review_cases(
                    correction_case_id TEXT PRIMARY KEY,
                    case_index INTEGER NOT NULL UNIQUE,
                    review_case_id TEXT NOT NULL UNIQUE,
                    source_case_fingerprint TEXT NOT NULL,
                    image_id TEXT NOT NULL,
                    ui_selection_json TEXT NOT NULL DEFAULT '{}',
                    canonical_fields_json TEXT NOT NULL DEFAULT '{}',
                    review_status TEXT NOT NULL DEFAULT 'pending' CHECK(review_status IN ('pending','reviewed','needs_adjudication')),
                    correction_decision TEXT NOT NULL DEFAULT '',
                    correction_operation TEXT NOT NULL DEFAULT '',
                    revision INTEGER NOT NULL DEFAULT 0 CHECK(revision >= 0),
                    saved_at_utc TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS app_state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit_events(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    correction_case_id TEXT,
                    revision INTEGER,
                    event_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS export_history(
                    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    output_path TEXT NOT NULL UNIQUE,
                    sha256 TEXT NOT NULL,
                    exported_at_utc TEXT NOT NULL
                );
                """
            )
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing_identity = {row["key"]: row["value"] for row in connection.execute("SELECT key,value FROM workspace_metadata ORDER BY key")}
                if existing_identity and existing_identity != identity:
                    raise CorrectionReviewStateError("existing correction-review workspace identity 不符")
                if not existing_identity:
                    connection.executemany("INSERT INTO workspace_metadata(key,value) VALUES(?,?)", sorted(identity.items()))
                existing_cases = [tuple(row) for row in connection.execute("SELECT correction_case_id,case_index,review_case_id,source_case_fingerprint,image_id FROM review_cases ORDER BY case_index")]
                if existing_cases and existing_cases != expected_cases:
                    raise CorrectionReviewStateError("existing correction-review cases 與 source 不符")
                if not existing_cases:
                    connection.executemany("INSERT INTO review_cases(correction_case_id,case_index,review_case_id,source_case_fingerprint,image_id) VALUES(?,?,?,?,?)", expected_cases)
                connection.execute("INSERT INTO app_state(key,value) VALUES('successful_save_count','0') ON CONFLICT(key) DO NOTHING")
                connection.execute("INSERT INTO app_state(key,value) VALUES('last_viewed_case_id',?) ON CONFLICT(key) DO NOTHING", (expected_cases[0][0],))
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise CorrectionReviewStateError(f"SQLite integrity check failed：{integrity}")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        self._synchronize_event_log()

    def _parse_event_log_last_id(self) -> int:
        if not self.event_log_path.exists():
            return 0
        last = 0
        with self.event_log_path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                try:
                    event_id = int(json.loads(raw)["event_id"])
                except Exception as exc:
                    raise CorrectionReviewStateError(f"event log 第 {line_number} 行損壞") from exc
                if event_id != last + 1:
                    raise CorrectionReviewStateError("event log IDs 不連續")
                last = event_id
        return last

    def verify_event_log_continuity(self) -> None:
        self._parse_event_log_last_id()

    def _synchronize_event_log(self) -> None:
        if not self.database_path.is_file():
            return
        last_id = self._parse_event_log_last_id()
        with self._connection() as connection:
            rows = connection.execute("SELECT event_id,event_type,correction_case_id,revision,event_json,created_at_utc FROM audit_events WHERE event_id>? ORDER BY event_id", (last_id,)).fetchall()
        if not rows:
            return
        with self.event_log_path.open("a", encoding="utf-8", newline="\n") as handle:
            expected = last_id + 1
            for row in rows:
                event_id = int(row["event_id"])
                if event_id != expected:
                    raise CorrectionReviewStateError("audit event IDs 不連續")
                payload = {
                    "event_id": event_id,
                    "event_type": row["event_type"],
                    "correction_case_id": row["correction_case_id"],
                    "revision": row["revision"],
                    "created_at_utc": row["created_at_utc"],
                    "details": json.loads(row["event_json"]),
                }
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
                expected += 1
            handle.flush(); os.fsync(handle.fileno())

    def save_review(
        self,
        correction_case_id: str,
        selection: CorrectionReviewSelection,
        canonical: CanonicalCorrectionFields,
    ) -> StoredCorrectionReview:
        if not self.database_path.is_file():
            raise CorrectionReviewStateError("state store 尚未初始化")
        with self._connection() as connection:
            metadata = {row["key"]: row["value"] for row in connection.execute("SELECT key,value FROM workspace_metadata")}
            if canonical.correction_reviewer != metadata.get("reviewer", ""):
                raise CorrectionReviewStateError("reviewer 與 workspace identity 不符")
            try:
                timestamp = datetime.fromisoformat(canonical.correction_reviewed_at_utc)
            except ValueError as exc:
                raise CorrectionReviewStateError("review timestamp 不是 ISO 8601") from exc
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise CorrectionReviewStateError("review timestamp 必須包含時區")
            current = connection.execute("SELECT revision,source_case_fingerprint FROM review_cases WHERE correction_case_id=?", (correction_case_id,)).fetchone()
            if current is None:
                raise CorrectionReviewStateError(f"未知 correction_case_id：{correction_case_id}")
            revision = int(current["revision"]) + 1
            saved_at = self._utc_now()
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "UPDATE review_cases SET ui_selection_json=?,canonical_fields_json=?,review_status=?,correction_decision=?,correction_operation=?,revision=?,saved_at_utc=? WHERE correction_case_id=?",
                    (
                        self._canonical_json(asdict(selection)), self._canonical_json(canonical.as_dict()),
                        canonical.correction_review_status, canonical.correction_decision, canonical.correction_operation,
                        revision, saved_at, correction_case_id,
                    ),
                )
                connection.execute(
                    "INSERT INTO audit_events(event_type,correction_case_id,revision,event_json,created_at_utc) VALUES('annotation_correction_review_saved',?,?,?,?)",
                    (correction_case_id, revision, self._canonical_json({"selection": asdict(selection), "canonical_fields": canonical.as_dict(), "source_case_fingerprint": current["source_case_fingerprint"]}), saved_at),
                )
                connection.execute("UPDATE app_state SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT) WHERE key='successful_save_count'")
                connection.execute("INSERT INTO app_state(key,value) VALUES('last_viewed_case_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (correction_case_id,))
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        self._synchronize_event_log()
        return StoredCorrectionReview(correction_case_id, asdict(selection), canonical.as_dict(), revision, saved_at)

    def get_review(self, correction_case_id: str) -> StoredCorrectionReview | None:
        with self._connection() as connection:
            row = connection.execute("SELECT correction_case_id,ui_selection_json,canonical_fields_json,revision,saved_at_utc FROM review_cases WHERE correction_case_id=? AND revision>0", (correction_case_id,)).fetchone()
        if row is None:
            return None
        return StoredCorrectionReview(row["correction_case_id"], json.loads(row["ui_selection_json"]), json.loads(row["canonical_fields_json"]), int(row["revision"]), row["saved_at_utc"])

    def progress(self) -> CorrectionProgressCounts:
        with self._connection() as connection:
            row = connection.execute("SELECT COUNT(*) total,SUM(review_status='reviewed') reviewed,SUM(review_status='pending') pending,SUM(review_status='needs_adjudication') needs_adjudication FROM review_cases").fetchone()
        return CorrectionProgressCounts(int(row["total"] or 0), int(row["reviewed"] or 0), int(row["pending"] or 0), int(row["needs_adjudication"] or 0))

    def case_ids(self, filter_name: str = "all") -> tuple[str, ...]:
        if filter_name not in self._SUPPORTED_FILTERS:
            raise CorrectionReviewStateError(f"不支援的 filter：{filter_name}")
        where = {"all": "1=1", "pending": "review_status='pending'", "reviewed": "review_status='reviewed'", "needs_adjudication": "review_status='needs_adjudication'"}[filter_name]
        with self._connection() as connection:
            rows = connection.execute(f"SELECT correction_case_id FROM review_cases WHERE {where} ORDER BY case_index").fetchall()
        return tuple(row["correction_case_id"] for row in rows)

    def successful_save_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute("SELECT value FROM app_state WHERE key='successful_save_count'").fetchone()
        return 0 if row is None else int(row["value"])

    def last_viewed_case_id(self) -> str:
        with self._connection() as connection:
            row = connection.execute("SELECT value FROM app_state WHERE key='last_viewed_case_id'").fetchone()
        return "" if row is None else str(row["value"])

    def create_backup(self, *, timestamp: str | None = None) -> Path:
        if not self.database_path.is_file():
            raise CorrectionReviewStateError("state store 尚未初始化")
        token = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.backup_dir / f"correction_review_state_{token}.sqlite3"
        if target.exists():
            raise CorrectionReviewStateError("backup path collision")
        temp = self.backup_dir / f".{target.name}.tmp"

        source = self._connect()
        destination = sqlite3.connect(temp)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
            source.close()

        check = sqlite3.connect(temp)
        try:
            integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            check.close()

        if integrity != "ok":
            temp.unlink(missing_ok=True)
            raise CorrectionReviewStateError(f"backup integrity check failed：{integrity}")
        temp.replace(target)
        backups = sorted(self.backup_dir.glob("correction_review_state_*.sqlite3"))
        for old in backups[:-self.backup_retention]:
            old.unlink()
        return target

    def record_export(self, output_path: Path, sha256: str) -> None:
        with self._connection() as connection:
            try:
                connection.execute("INSERT INTO export_history(output_path,sha256,exported_at_utc) VALUES(?,?,?)", (str(output_path.resolve()), sha256, self._utc_now()))
            except sqlite3.IntegrityError as exc:
                raise CorrectionReviewStateError("export history 已存在") from exc
