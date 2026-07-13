from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from fleetvision.review.validation_error_review_mapping import (
    CanonicalReviewFields,
    ReviewSelection,
)
from fleetvision.review.validation_error_review_package import VerifiedSourcePackage


class ReviewStateError(RuntimeError):
    """Raised when local review state is inconsistent or unsafe."""


@dataclass(frozen=True)
class StoredReview:
    review_case_id: str
    selection: Mapping[str, Any]
    canonical_fields: Mapping[str, str]
    revision: int
    saved_at_utc: str


@dataclass(frozen=True)
class ProgressCounts:
    total: int
    reviewed: int
    pending: int
    needs_adjudication: int
    high_priority: int
    annotation_issues: int


class ReviewStateStore:
    """Single-user SQLite state store for local Phase 04.5L review."""

    _SUPPORTED_FILTERS = {
        "all",
        "pending",
        "reviewed",
        "needs_adjudication",
        "high_priority",
        "annotation_issues",
    }

    def __init__(self, workspace_root: Path, *, backup_retention: int) -> None:
        if backup_retention <= 0:
            raise ReviewStateError("backup_retention must be positive")

        self.workspace_root = workspace_root.resolve()
        self.state_dir = self.workspace_root / "state"
        self.backup_dir = self.workspace_root / "backups"
        self.export_dir = self.workspace_root / "exports"
        self.log_dir = self.workspace_root / "app_logs"
        self.database_path = self.state_dir / "review_state.sqlite3"
        self.event_log_path = self.state_dir / "review_events.jsonl"
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
        """Yield one configured connection and always release Windows locks."""

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

    def _workspace_identity(
        self,
        package: VerifiedSourcePackage,
    ) -> dict[str, str]:
        config = package.config
        return {
            "schema_version": config.schema_version,
            "batch_root": str(package.batch_root),
            "workbook_sha256": config.workbook_sha256,
            "frozen_zip_sha256": config.frozen_zip_sha256,
            "expected_case_count": str(config.expected_case_count),
            "reviewer": config.reviewer,
            "timezone": config.timezone,
        }

    def _expected_cases(
        self,
        package: VerifiedSourcePackage,
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

    def initialize(self, package: VerifiedSourcePackage) -> None:
        """Create or reopen a workspace pinned to exactly one source package."""

        if package.config.workspace_root.resolve() != self.workspace_root:
            raise ReviewStateError(
                "state store workspace does not match verified package config"
            )

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
                        CHECK (
                            review_status IN (
                                'pending',
                                'reviewed',
                                'needs_adjudication'
                            )
                        ),
                    retraining_priority TEXT NOT NULL DEFAULT '',
                    annotation_quality TEXT NOT NULL DEFAULT '',
                    revision INTEGER NOT NULL DEFAULT 0
                        CHECK (revision >= 0),
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
                        "SELECT key, value FROM workspace_metadata "
                        "ORDER BY key"
                    ).fetchall()
                }
                if existing_identity and existing_identity != identity:
                    raise ReviewStateError(
                        "workspace identity does not match source package"
                    )
                if not existing_identity:
                    connection.executemany(
                        "INSERT INTO workspace_metadata(key, value) "
                        "VALUES(?, ?)",
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
                        FROM review_cases
                        ORDER BY case_index
                        """
                    ).fetchall()
                ]
                if existing_cases and existing_cases != expected_cases:
                    raise ReviewStateError(
                        "workspace source cases do not match verified package"
                    )
                if not existing_cases:
                    connection.executemany(
                        """
                        INSERT INTO review_cases(
                            review_case_id,
                            case_index,
                            source_case_fingerprint,
                            image_id
                        )
                        VALUES(?, ?, ?, ?)
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

                integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
                if integrity != "ok":
                    raise ReviewStateError(
                        f"SQLite integrity check failed: {integrity}"
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
                    raise ReviewStateError(
                        f"event log is malformed at line {line_number}"
                    ) from exc
                if event_id != last_id + 1:
                    raise ReviewStateError(
                        "event log IDs are not contiguous"
                    )
                last_id = event_id
        return last_id

    def _synchronize_event_log(self) -> None:
        """Append audit events missing from the JSONL mirror."""

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
                    raise ReviewStateError(
                        "audit event IDs are not contiguous"
                    )
                payload = {
                    "event_id": event_id,
                    "event_type": row["event_type"],
                    "review_case_id": row["review_case_id"],
                    "revision": row["revision"],
                    "created_at_utc": row["created_at_utc"],
                    "details": json.loads(row["event_json"]),
                }
                handle.write(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )
                expected_id += 1
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _validate_review_payload(
        canonical: CanonicalReviewFields,
        *,
        expected_reviewer: str,
    ) -> None:
        if canonical.review_status not in {
            "reviewed",
            "needs_adjudication",
        }:
            raise ReviewStateError(
                "saved review status must be reviewed or needs_adjudication"
            )
        if canonical.reviewer != expected_reviewer:
            raise ReviewStateError(
                "reviewer does not match workspace identity"
            )
        try:
            timestamp = datetime.fromisoformat(canonical.reviewed_at_utc)
        except ValueError as exc:
            raise ReviewStateError(
                "reviewed_at_utc must be valid ISO 8601"
            ) from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ReviewStateError(
                "reviewed_at_utc must include a timezone offset"
            )

    def save_review(
        self,
        review_case_id: str,
        selection: ReviewSelection,
        canonical: CanonicalReviewFields,
    ) -> StoredReview:
        """Save one review transactionally and append one audit event."""

        if not self.database_path.is_file():
            raise ReviewStateError("state store has not been initialized")

        with self._connection() as connection:
            metadata = {
                row["key"]: row["value"]
                for row in connection.execute(
                    "SELECT key, value FROM workspace_metadata"
                ).fetchall()
            }
            expected_reviewer = metadata.get("reviewer", "")
            self._validate_review_payload(
                canonical,
                expected_reviewer=expected_reviewer,
            )

            selection_json = self._canonical_json(asdict(selection))
            canonical_json = self._canonical_json(canonical.as_dict())
            saved_at = self._utc_now()

            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    """
                    SELECT revision
                    FROM review_cases
                    WHERE review_case_id = ?
                    """,
                    (review_case_id,),
                ).fetchone()
                if row is None:
                    raise ReviewStateError(
                        f"unknown review_case_id: {review_case_id}"
                    )

                revision = int(row["revision"]) + 1
                connection.execute(
                    """
                    UPDATE review_cases
                    SET ui_selection_json = ?,
                        canonical_fields_json = ?,
                        review_status = ?,
                        retraining_priority = ?,
                        annotation_quality = ?,
                        revision = ?,
                        saved_at_utc = ?
                    WHERE review_case_id = ?
                    """,
                    (
                        selection_json,
                        canonical_json,
                        canonical.review_status,
                        canonical.retraining_priority,
                        canonical.annotation_quality,
                        revision,
                        saved_at,
                        review_case_id,
                    ),
                )

                count_row = connection.execute(
                    """
                    SELECT value
                    FROM app_state
                    WHERE key = 'successful_save_count'
                    """
                ).fetchone()
                successful_save_count = int(count_row["value"]) + 1
                connection.execute(
                    """
                    UPDATE app_state
                    SET value = ?
                    WHERE key = 'successful_save_count'
                    """,
                    (str(successful_save_count),),
                )

                event_details = {
                    "review_status": canonical.review_status,
                    "retraining_priority": canonical.retraining_priority,
                    "annotation_quality": canonical.annotation_quality,
                    "successful_save_count": successful_save_count,
                }
                connection.execute(
                    """
                    INSERT INTO audit_events(
                        event_type,
                        review_case_id,
                        revision,
                        event_json,
                        created_at_utc
                    )
                    VALUES('review_saved', ?, ?, ?, ?)
                    """,
                    (
                        review_case_id,
                        revision,
                        self._canonical_json(event_details),
                        saved_at,
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

        self._synchronize_event_log()
        return StoredReview(
            review_case_id=review_case_id,
            selection=json.loads(selection_json),
            canonical_fields=json.loads(canonical_json),
            revision=revision,
            saved_at_utc=saved_at,
        )

    def get_review(self, review_case_id: str) -> StoredReview | None:
        if not self.database_path.is_file():
            raise ReviewStateError("state store has not been initialized")

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT review_case_id, ui_selection_json,
                       canonical_fields_json, revision, saved_at_utc
                FROM review_cases
                WHERE review_case_id = ?
                """,
                (review_case_id,),
            ).fetchone()
        if row is None:
            raise ReviewStateError(
                f"unknown review_case_id: {review_case_id}"
            )
        if int(row["revision"]) == 0:
            return None
        return StoredReview(
            review_case_id=row["review_case_id"],
            selection=json.loads(row["ui_selection_json"]),
            canonical_fields=json.loads(row["canonical_fields_json"]),
            revision=int(row["revision"]),
            saved_at_utc=row["saved_at_utc"],
        )

    def progress(self) -> ProgressCounts:
        if not self.database_path.is_file():
            raise ReviewStateError("state store has not been initialized")

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN review_status = 'reviewed'
                        THEN 1 ELSE 0 END) AS reviewed,
                    SUM(CASE WHEN review_status = 'pending'
                        THEN 1 ELSE 0 END) AS pending,
                    SUM(CASE WHEN review_status = 'needs_adjudication'
                        THEN 1 ELSE 0 END) AS needs_adjudication,
                    SUM(CASE WHEN retraining_priority = 'high'
                        THEN 1 ELSE 0 END) AS high_priority,
                    SUM(CASE WHEN annotation_quality = 'defect_suspected'
                        THEN 1 ELSE 0 END) AS annotation_issues
                FROM review_cases
                """
            ).fetchone()

        return ProgressCounts(
            total=int(row["total"] or 0),
            reviewed=int(row["reviewed"] or 0),
            pending=int(row["pending"] or 0),
            needs_adjudication=int(row["needs_adjudication"] or 0),
            high_priority=int(row["high_priority"] or 0),
            annotation_issues=int(row["annotation_issues"] or 0),
        )

    def list_case_ids(self, filter_name: str = "all") -> list[str]:
        if filter_name not in self._SUPPORTED_FILTERS:
            raise ReviewStateError(
                f"unsupported filter: {filter_name}"
            )

        clauses = {
            "all": "",
            "pending": "WHERE review_status = 'pending'",
            "reviewed": "WHERE review_status = 'reviewed'",
            "needs_adjudication": (
                "WHERE review_status = 'needs_adjudication'"
            ),
            "high_priority": (
                "WHERE retraining_priority = 'high'"
            ),
            "annotation_issues": (
                "WHERE annotation_quality = 'defect_suspected'"
            ),
        }
        query = (
            "SELECT review_case_id FROM review_cases "
            f"{clauses[filter_name]} ORDER BY case_index"
        )
        with self._connection() as connection:
            return [
                row["review_case_id"]
                for row in connection.execute(query).fetchall()
            ]

    def set_last_viewed(self, review_case_id: str) -> None:
        with self._connection() as connection:
            exists = connection.execute(
                """
                SELECT 1
                FROM review_cases
                WHERE review_case_id = ?
                """,
                (review_case_id,),
            ).fetchone()
            if exists is None:
                raise ReviewStateError(
                    f"unknown review_case_id: {review_case_id}"
                )
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO app_state(key, value)
                    VALUES('last_viewed_case_id', ?)
                    ON CONFLICT(key) DO UPDATE
                    SET value = excluded.value
                    """,
                    (review_case_id,),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def get_last_viewed(self) -> str | None:
        if not self.database_path.is_file():
            raise ReviewStateError("state store has not been initialized")

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT value
                FROM app_state
                WHERE key = 'last_viewed_case_id'
                """
            ).fetchone()
        return None if row is None else str(row["value"])

    def successful_save_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT value
                FROM app_state
                WHERE key = 'successful_save_count'
                """
            ).fetchone()
        return 0 if row is None else int(row["value"])

    def database_integrity_check(self) -> str:
        with self._connection() as connection:
            return str(
                connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
            )

    def create_backup(self) -> Path:
        """Create an online SQLite backup and enforce retention."""

        if not self.database_path.is_file():
            raise ReviewStateError("state database does not exist")

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        output = self.backup_dir / f"review_state_{timestamp}.sqlite3"
        staging = self.backup_dir / f".{output.name}.staging"

        if output.exists() or staging.exists():
            raise ReviewStateError(
                f"backup path collision: {output}"
            )

        try:
            with self._connection() as source:
                source.execute("PRAGMA wal_checkpoint(PASSIVE)")
                destination = sqlite3.connect(staging)
                try:
                    source.backup(destination)
                    integrity = destination.execute(
                        "PRAGMA integrity_check"
                    ).fetchone()[0]
                    if integrity != "ok":
                        raise ReviewStateError(
                            f"backup integrity check failed: {integrity}"
                        )
                    destination.commit()
                finally:
                    destination.close()
            staging.replace(output)
        except Exception:
            staging.unlink(missing_ok=True)
            raise

        backups = sorted(
            self.backup_dir.glob("review_state_*.sqlite3")
        )
        for stale in backups[:-self.backup_retention]:
            stale.unlink()
        return output
