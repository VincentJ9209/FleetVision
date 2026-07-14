from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from fleetvision.review.severity_scope_review_mapping import (
    CanonicalScopeFields,
    ScopeReviewSelection,
)
from fleetvision.review.severity_scope_review_package import VerifiedScopePackage


class ScopeReviewStateError(RuntimeError):
    """Raised when local scope-review state is inconsistent or unsafe."""


@dataclass(frozen=True)
class StoredScopeReview:
    review_case_id: str
    selection: Mapping[str, Any]
    canonical_fields: Mapping[str, str]
    revision: int
    saved_at_utc: str


@dataclass(frozen=True)
class ScopeProgressCounts:
    total: int
    reviewed: int
    pending: int
    needs_adjudication: int
    low_confidence: int
    catastrophic: int


class ScopeReviewStateStore:
    """Single-user SQLite state store for severity-scope review."""

    _SUPPORTED_FILTERS = {
        "all",
        "pending",
        "reviewed",
        "needs_adjudication",
        "low_confidence",
        "catastrophic",
    }

    def __init__(self, workspace_root: Path, *, backup_retention: int) -> None:
        if backup_retention <= 0:
            raise ScopeReviewStateError("backup_retention 必須是正整數")
        self.workspace_root = workspace_root.resolve()
        self.state_dir = self.workspace_root / "state"
        self.backup_dir = self.workspace_root / "backups"
        self.export_dir = self.workspace_root / "exports"
        self.log_dir = self.workspace_root / "app_logs"
        self.database_path = self.state_dir / "scope_review_state.sqlite3"
        self.event_log_path = self.state_dir / "scope_review_events.jsonl"
        self.backup_retention = backup_retention

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30.0,
            isolation_level=None,
        )
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
    def _canonical_json(payload: Mapping[str, Any]) -> str:
        return json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _workspace_identity(self, package: VerifiedScopePackage) -> dict[str, str]:
        return {
            "schema_version": package.config.schema_version,
            "f1_workspace_root": str(package.f1_workspace_root),
            "scope_source_csv_sha256": package.source_csv_sha256,
            "scope_template_workbook_sha256": package.template_workbook_sha256,
            "scope_asset_manifest_sha256": package.asset_manifest_sha256,
            "expected_case_count": str(package.config.expected_case_count),
            "reviewer": package.config.reviewer,
            "timezone": package.config.timezone,
        }

    def _expected_cases(
        self,
        package: VerifiedScopePackage,
    ) -> list[tuple[str, int, str, str]]:
        return [
            (
                case.review_case_id,
                case.case_index,
                case.source_case_fingerprint,
                case.image_id,
            )
            for case in package.cases
        ]

    def initialize(self, package: VerifiedScopePackage) -> None:
        """Create or reopen a workspace pinned to one immutable F1 package."""

        if package.app_workspace_root.resolve() != self.workspace_root:
            raise ScopeReviewStateError("state workspace 與 verified package 不一致")
        for path in (
            self.state_dir,
            self.backup_dir,
            self.export_dir,
            self.log_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

        identity = self._workspace_identity(package)
        expected_cases = self._expected_cases(package)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workspace_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_cases (
                    review_case_id TEXT PRIMARY KEY,
                    case_index INTEGER NOT NULL UNIQUE,
                    source_case_fingerprint TEXT NOT NULL,
                    image_id TEXT NOT NULL,
                    ui_selection_json TEXT NOT NULL DEFAULT '{}',
                    canonical_fields_json TEXT NOT NULL DEFAULT '{}',
                    review_status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (review_status IN ('pending','reviewed','needs_adjudication')),
                    scope_group TEXT NOT NULL DEFAULT '',
                    scope_confidence TEXT NOT NULL DEFAULT '',
                    revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
                    saved_at_utc TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    review_case_id TEXT,
                    revision INTEGER,
                    event_json TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS export_history (
                    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    output_path TEXT NOT NULL UNIQUE,
                    sha256 TEXT NOT NULL,
                    exported_at_utc TEXT NOT NULL
                );
                """
            )
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing_identity = {
                    row["key"]: row["value"]
                    for row in connection.execute(
                        "SELECT key, value FROM workspace_metadata ORDER BY key"
                    ).fetchall()
                }
                if existing_identity and existing_identity != identity:
                    raise ScopeReviewStateError(
                        "existing scope-review workspace identity 不符"
                    )
                if not existing_identity:
                    connection.executemany(
                        "INSERT INTO workspace_metadata(key, value) VALUES(?, ?)",
                        sorted(identity.items()),
                    )

                existing_cases = [
                    (
                        row["review_case_id"],
                        int(row["case_index"]),
                        row["source_case_fingerprint"],
                        row["image_id"],
                    )
                    for row in connection.execute(
                        """
                        SELECT review_case_id, case_index,
                               source_case_fingerprint, image_id
                        FROM review_cases ORDER BY case_index
                        """
                    ).fetchall()
                ]
                if existing_cases and existing_cases != expected_cases:
                    raise ScopeReviewStateError(
                        "existing scope-review cases 與 F1 source 不符"
                    )
                if not existing_cases:
                    connection.executemany(
                        """
                        INSERT INTO review_cases(
                            review_case_id, case_index,
                            source_case_fingerprint, image_id
                        ) VALUES(?, ?, ?, ?)
                        """,
                        expected_cases,
                    )

                connection.execute(
                    """
                    INSERT INTO app_state(key, value)
                    VALUES('successful_save_count', '0')
                    ON CONFLICT(key) DO NOTHING
                    """
                )
                if expected_cases:
                    connection.execute(
                        """
                        INSERT INTO app_state(key, value)
                        VALUES('last_viewed_case_id', ?)
                        ON CONFLICT(key) DO NOTHING
                        """,
                        (expected_cases[0][0],),
                    )
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise ScopeReviewStateError(
                        f"SQLite integrity check failed：{integrity}"
                    )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        self._synchronize_event_log()

    def _parse_event_log_last_id(self) -> int:
        if not self.event_log_path.exists():
            return 0
        last_id = 0
        with self.event_log_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    event_id = int(payload["event_id"])
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ScopeReviewStateError(
                        f"event log 第 {line_number} 行損壞"
                    ) from exc
                if event_id != last_id + 1:
                    raise ScopeReviewStateError("event log IDs 不連續")
                last_id = event_id
        return last_id

    def _synchronize_event_log(self) -> None:
        if not self.database_path.is_file():
            return
        last_id = self._parse_event_log_last_id()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id, event_type, review_case_id, revision,
                       event_json, created_at_utc
                FROM audit_events
                WHERE event_id > ?
                ORDER BY event_id
                """,
                (last_id,),
            ).fetchall()
        if not rows:
            return
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.event_log_path.open("a", encoding="utf-8", newline="\n") as handle:
            expected_id = last_id + 1
            for row in rows:
                event_id = int(row["event_id"])
                if event_id != expected_id:
                    raise ScopeReviewStateError("audit event IDs 不連續")
                payload = {
                    "event_id": event_id,
                    "event_type": row["event_type"],
                    "review_case_id": row["review_case_id"],
                    "revision": row["revision"],
                    "created_at_utc": row["created_at_utc"],
                    "details": json.loads(row["event_json"]),
                }
                handle.write(
                    json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
                )
                expected_id += 1
            handle.flush()
            os.fsync(handle.fileno())

    def save_review(
        self,
        review_case_id: str,
        selection: ScopeReviewSelection,
        canonical: CanonicalScopeFields,
    ) -> StoredScopeReview:
        """Save one scope review transactionally and append an audit event."""

        if not self.database_path.is_file():
            raise ScopeReviewStateError("state store 尚未初始化")
        with self._connection() as connection:
            metadata = {
                row["key"]: row["value"]
                for row in connection.execute(
                    "SELECT key, value FROM workspace_metadata"
                ).fetchall()
            }
            if canonical.scope_reviewer != metadata.get("reviewer", ""):
                raise ScopeReviewStateError("reviewer 與 workspace identity 不符")
            try:
                timestamp = datetime.fromisoformat(canonical.scope_reviewed_at_utc)
            except ValueError as exc:
                raise ScopeReviewStateError("review timestamp 不是 ISO 8601") from exc
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ScopeReviewStateError("review timestamp 必須包含時區")

            current = connection.execute(
                "SELECT revision FROM review_cases WHERE review_case_id = ?",
                (review_case_id,),
            ).fetchone()
            if current is None:
                raise ScopeReviewStateError(
                    f"未知的 review_case_id：{review_case_id}"
                )
            revision = int(current["revision"]) + 1
            saved_at = self._utc_now()
            selection_json = self._canonical_json(asdict(selection))
            canonical_json = self._canonical_json(canonical.as_dict())
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    UPDATE review_cases
                    SET ui_selection_json = ?, canonical_fields_json = ?,
                        review_status = ?, scope_group = ?, scope_confidence = ?,
                        revision = ?, saved_at_utc = ?
                    WHERE review_case_id = ?
                    """,
                    (
                        selection_json,
                        canonical_json,
                        canonical.scope_review_status,
                        canonical.scope_group,
                        canonical.scope_confidence,
                        revision,
                        saved_at,
                        review_case_id,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO audit_events(
                        event_type, review_case_id, revision,
                        event_json, created_at_utc
                    ) VALUES('scope_review_saved', ?, ?, ?, ?)
                    """,
                    (
                        review_case_id,
                        revision,
                        self._canonical_json(
                            {
                                "selection": asdict(selection),
                                "canonical_fields": canonical.as_dict(),
                            }
                        ),
                        saved_at,
                    ),
                )
                connection.execute(
                    """
                    UPDATE app_state
                    SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT)
                    WHERE key = 'successful_save_count'
                    """
                )
                connection.execute(
                    """
                    INSERT INTO app_state(key, value)
                    VALUES('last_viewed_case_id', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (review_case_id,),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        self._synchronize_event_log()
        return StoredScopeReview(
            review_case_id=review_case_id,
            selection=asdict(selection),
            canonical_fields=canonical.as_dict(),
            revision=revision,
            saved_at_utc=saved_at,
        )

    def get_review(self, review_case_id: str) -> StoredScopeReview | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT review_case_id, ui_selection_json,
                       canonical_fields_json, revision, saved_at_utc
                FROM review_cases
                WHERE review_case_id = ? AND revision > 0
                """,
                (review_case_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredScopeReview(
            review_case_id=row["review_case_id"],
            selection=json.loads(row["ui_selection_json"]),
            canonical_fields=json.loads(row["canonical_fields_json"]),
            revision=int(row["revision"]),
            saved_at_utc=row["saved_at_utc"],
        )

    def progress(self) -> ScopeProgressCounts:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN review_status='reviewed' THEN 1 ELSE 0 END) AS reviewed,
                    SUM(CASE WHEN review_status='pending' THEN 1 ELSE 0 END) AS pending,
                    SUM(CASE WHEN review_status='needs_adjudication' THEN 1 ELSE 0 END) AS needs_adjudication,
                    SUM(CASE WHEN scope_confidence='low' THEN 1 ELSE 0 END) AS low_confidence,
                    SUM(CASE WHEN scope_group='OUT_OF_SCOPE_CATASTROPHIC' THEN 1 ELSE 0 END) AS catastrophic
                FROM review_cases
                """
            ).fetchone()
        return ScopeProgressCounts(
            total=int(row["total"] or 0),
            reviewed=int(row["reviewed"] or 0),
            pending=int(row["pending"] or 0),
            needs_adjudication=int(row["needs_adjudication"] or 0),
            low_confidence=int(row["low_confidence"] or 0),
            catastrophic=int(row["catastrophic"] or 0),
        )

    def case_ids(self, filter_name: str = "all") -> tuple[str, ...]:
        if filter_name not in self._SUPPORTED_FILTERS:
            raise ScopeReviewStateError(f"不支援的 filter：{filter_name}")
        where = {
            "all": "1=1",
            "pending": "review_status='pending'",
            "reviewed": "review_status='reviewed'",
            "needs_adjudication": "review_status='needs_adjudication'",
            "low_confidence": "scope_confidence='low'",
            "catastrophic": "scope_group='OUT_OF_SCOPE_CATASTROPHIC'",
        }[filter_name]
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT review_case_id FROM review_cases WHERE {where} ORDER BY case_index"
            ).fetchall()
        return tuple(row["review_case_id"] for row in rows)

    def successful_save_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key='successful_save_count'"
            ).fetchone()
        return 0 if row is None else int(row["value"])

    def last_viewed_case_id(self) -> str:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key='last_viewed_case_id'"
            ).fetchone()
        return "" if row is None else str(row["value"])

    def create_backup(self) -> Path:
        """Create an SQLite backup and retain only the newest configured count."""

        if not self.database_path.is_file():
            raise ScopeReviewStateError("state database 不存在")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = self.backup_dir / f"scope_review_state_{timestamp}.sqlite3"
        with self._connection() as source:
            target = sqlite3.connect(output)
            try:
                source.backup(target)
                integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise ScopeReviewStateError(
                        f"backup SQLite integrity check failed：{integrity}"
                    )
            finally:
                target.close()
        backups = sorted(
            self.backup_dir.glob("scope_review_state_*.sqlite3"),
            key=lambda path: path.name,
            reverse=True,
        )
        for stale in backups[self.backup_retention :]:
            stale.unlink(missing_ok=True)
        return output

    def record_export(self, output_path: Path, sha256: str) -> None:
        exported_at = self._utc_now()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO export_history(output_path, sha256, exported_at_utc)
                VALUES(?, ?, ?)
                """,
                (str(output_path.resolve()), sha256, exported_at),
            )
            connection.execute(
                """
                INSERT INTO audit_events(
                    event_type, review_case_id, revision,
                    event_json, created_at_utc
                ) VALUES('scope_review_exported', NULL, NULL, ?, ?)
                """,
                (
                    self._canonical_json(
                        {"output_path": str(output_path.resolve()), "sha256": sha256}
                    ),
                    exported_at,
                ),
            )
        self._synchronize_event_log()
