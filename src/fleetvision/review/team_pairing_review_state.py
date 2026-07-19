from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from fleetvision.review.team_pairing_review_mapping import (
    AngleReviewSelection,
    BatchReviewSelection,
    CanonicalAngleFields,
    CanonicalBatchFields,
    CanonicalPairFields,
    PairReviewSelection,
)


class TeamPairingReviewStateError(RuntimeError):
    """Raised when the local Team Pairing review state is unsafe or inconsistent."""


REQUIRED_TABLES = (
    "app_state",
    "audit_events",
    "batch_members",
    "batch_reviews",
    "candidate_batches",
    "export_history",
    "image_reviews",
    "pair_candidates",
    "pair_reviews",
    "source_images",
    "workspace_metadata",
)


@dataclass(frozen=True)
class TeamPairingWorkspaceIdentity:
    schema_version: str
    project_root: str
    source_root: str
    candidate_manifest_sha256: str
    inventory_sha256: str
    batch_candidates_sha256: str
    batch_members_sha256: str
    config_sha256: str
    reviewer: str
    timezone: str
    expected_image_count: int
    expected_batch_count: int
    expected_pair_count: int

    def as_mapping(self) -> dict[str, str]:
        values = asdict(self)
        return {key: str(value) for key, value in values.items()}


@dataclass(frozen=True)
class SourceImageSeed:
    image_id: str
    inventory_sequence: int
    relative_path: str
    is_readable: bool


@dataclass(frozen=True)
class CandidateBatchSeed:
    batch_id: str
    batch_sequence: int
    start_time_utc: str
    end_time_utc: str


@dataclass(frozen=True)
class BatchMemberSeed:
    batch_id: str
    image_id: str
    member_sequence: int


@dataclass(frozen=True)
class PairCandidateSeed:
    pair_candidate_id: str
    pair_sequence: int
    before_batch_id: str
    after_batch_id: str


@dataclass(frozen=True)
class TeamPairingCandidatePackage:
    workspace_root: Path
    identity: TeamPairingWorkspaceIdentity
    images: tuple[SourceImageSeed, ...]
    batches: tuple[CandidateBatchSeed, ...]
    members: tuple[BatchMemberSeed, ...]
    pairs: tuple[PairCandidateSeed, ...]


@dataclass(frozen=True)
class StoredReview:
    entity_type: str
    entity_id: str
    selection: Mapping[str, Any]
    canonical_fields: Mapping[str, Any]
    revision: int
    saved_at_utc: str


@dataclass(frozen=True)
class TeamPairingProgressCounts:
    images_total: int
    images_reviewed: int
    batches_total: int
    batches_terminal: int
    pairs_total: int
    pairs_terminal: int


class TeamPairingReviewStateStore:
    _BATCH_FILTERS = {
        "all",
        "pending",
        "confirmed",
        "split_required",
        "merge_required",
        "exclude",
        "uncertain",
    }
    _IMAGE_FILTERS = {"all", "pending", "reviewed", "needs_adjudication"}
    _PAIR_FILTERS = {"all", "pending", "confirmed", "rejected", "uncertain"}
    _VIEW_MODES = {"batch", "image", "pair"}

    def __init__(
        self,
        workspace_root: Path,
        *,
        identity: TeamPairingWorkspaceIdentity,
        backup_every_successful_saves: int,
        backup_retention: int,
    ) -> None:
        if backup_every_successful_saves <= 0:
            raise TeamPairingReviewStateError(
                "backup_every_successful_saves 必須是正整數"
            )
        if backup_retention <= 0:
            raise TeamPairingReviewStateError("backup_retention 必須是正整數")

        self.workspace_root = workspace_root.resolve()
        self.review_dir = self.workspace_root / "review"
        self.backup_dir = self.review_dir / "backups"
        self.database_path = self.review_dir / "team_pair_review.sqlite"
        self.event_log_path = self.review_dir / "team_pair_review_events.jsonl"
        self.identity = identity
        self.backup_every_successful_saves = backup_every_successful_saves
        self.backup_retention = backup_retention

    def _connect(self) -> sqlite3.Connection:
        try:
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
        except sqlite3.DatabaseError as exc:
            raise TeamPairingReviewStateError(
                f"SQLite database corrupt or unreadable：{exc}"
            ) from exc

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
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _existing_table_names(self, connection: sqlite3.Connection) -> tuple[str, ...]:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return tuple(str(row["name"]) for row in rows)

    def _validate_preexisting_database(self) -> None:
        if not self.database_path.exists():
            return
        connection = None
        try:
            connection = sqlite3.connect(self.database_path)
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            names = tuple(str(row[0]) for row in rows)
        except sqlite3.DatabaseError as exc:
            raise TeamPairingReviewStateError(
                f"SQLite database corrupt or unreadable：{exc}"
            ) from exc
        finally:
            if connection is not None:
                connection.close()
        if names != REQUIRED_TABLES:
            raise TeamPairingReviewStateError(
                "partial SQLite schema detected; existing review database is not accepted"
            )

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspace_metadata(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS source_images(
                image_id TEXT PRIMARY KEY,
                inventory_sequence INTEGER NOT NULL UNIQUE,
                relative_path TEXT NOT NULL UNIQUE,
                is_readable INTEGER NOT NULL CHECK(is_readable IN (0,1))
            );

            CREATE TABLE IF NOT EXISTS candidate_batches(
                batch_id TEXT PRIMARY KEY,
                batch_sequence INTEGER NOT NULL UNIQUE,
                start_time_utc TEXT NOT NULL,
                end_time_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS batch_members(
                batch_id TEXT NOT NULL REFERENCES candidate_batches(batch_id),
                image_id TEXT NOT NULL REFERENCES source_images(image_id),
                member_sequence INTEGER NOT NULL,
                PRIMARY KEY(batch_id, image_id),
                UNIQUE(batch_id, member_sequence)
            );

            CREATE TABLE IF NOT EXISTS batch_reviews(
                batch_id TEXT PRIMARY KEY REFERENCES candidate_batches(batch_id),
                selection_json TEXT NOT NULL DEFAULT '{}',
                canonical_fields_json TEXT NOT NULL DEFAULT '{}',
                manual_batch_status TEXT NOT NULL DEFAULT 'pending',
                manual_vehicle_id TEXT NOT NULL DEFAULT '',
                manual_stage TEXT NOT NULL DEFAULT 'unknown',
                revision INTEGER NOT NULL DEFAULT 0 CHECK(revision >= 0),
                saved_at_utc TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS image_reviews(
                image_id TEXT PRIMARY KEY REFERENCES source_images(image_id),
                selection_json TEXT NOT NULL DEFAULT '{}',
                canonical_fields_json TEXT NOT NULL DEFAULT '{}',
                review_status TEXT NOT NULL DEFAULT 'pending',
                manual_angle TEXT NOT NULL DEFAULT 'unknown',
                revision INTEGER NOT NULL DEFAULT 0 CHECK(revision >= 0),
                saved_at_utc TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS pair_candidates(
                pair_candidate_id TEXT PRIMARY KEY,
                pair_sequence INTEGER NOT NULL UNIQUE,
                before_batch_id TEXT NOT NULL REFERENCES candidate_batches(batch_id),
                after_batch_id TEXT NOT NULL REFERENCES candidate_batches(batch_id)
            );

            CREATE TABLE IF NOT EXISTS pair_reviews(
                pair_candidate_id TEXT PRIMARY KEY REFERENCES pair_candidates(pair_candidate_id),
                selection_json TEXT NOT NULL DEFAULT '{}',
                canonical_fields_json TEXT NOT NULL DEFAULT '{}',
                manual_pair_status TEXT NOT NULL DEFAULT 'pending',
                derived_case_classification TEXT NOT NULL DEFAULT 'MANUAL_REVIEW_REQUIRED',
                manual_demo_role TEXT NOT NULL DEFAULT 'none',
                revision INTEGER NOT NULL DEFAULT 0 CHECK(revision >= 0),
                saved_at_utc TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS app_state(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events(
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
                event_type TEXT NOT NULL,
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

    @staticmethod
    def _expected_image_rows(
        package: TeamPairingCandidatePackage,
    ) -> list[tuple[str, int, str, int]]:
        return [
            (
                item.image_id,
                int(item.inventory_sequence),
                item.relative_path,
                int(bool(item.is_readable)),
            )
            for item in package.images
        ]

    @staticmethod
    def _expected_batch_rows(
        package: TeamPairingCandidatePackage,
    ) -> list[tuple[str, int, str, str]]:
        return [
            (
                item.batch_id,
                int(item.batch_sequence),
                item.start_time_utc,
                item.end_time_utc,
            )
            for item in package.batches
        ]

    @staticmethod
    def _expected_member_rows(
        package: TeamPairingCandidatePackage,
    ) -> list[tuple[str, str, int]]:
        return [
            (item.batch_id, item.image_id, int(item.member_sequence))
            for item in package.members
        ]

    @staticmethod
    def _expected_pair_rows(
        package: TeamPairingCandidatePackage,
    ) -> list[tuple[str, int, str, str]]:
        return [
            (
                item.pair_candidate_id,
                int(item.pair_sequence),
                item.before_batch_id,
                item.after_batch_id,
            )
            for item in package.pairs
        ]

    def _validate_package(self, package: TeamPairingCandidatePackage) -> None:
        if package.workspace_root.resolve() != self.workspace_root:
            raise TeamPairingReviewStateError("workspace identity root mismatch")
        if package.identity != self.identity:
            raise TeamPairingReviewStateError("workspace identity mismatch")
        if len(package.images) != self.identity.expected_image_count:
            raise TeamPairingReviewStateError("candidate image count mismatch")
        if len(package.batches) != self.identity.expected_batch_count:
            raise TeamPairingReviewStateError("candidate batch count mismatch")
        if len(package.pairs) != self.identity.expected_pair_count:
            raise TeamPairingReviewStateError("candidate pair count mismatch")

    def initialize(self, package: TeamPairingCandidatePackage) -> None:
        self._validate_package(package)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._validate_preexisting_database()

        expected_identity = self.identity.as_mapping()
        expected_images = self._expected_image_rows(package)
        expected_batches = self._expected_batch_rows(package)
        expected_members = self._expected_member_rows(package)
        expected_pairs = self._expected_pair_rows(package)

        try:
            with self._connection() as connection:
                self._create_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                try:
                    existing_identity = {
                        str(row["key"]): str(row["value"])
                        for row in connection.execute(
                            "SELECT key,value FROM workspace_metadata ORDER BY key"
                        ).fetchall()
                    }
                    if existing_identity and existing_identity != expected_identity:
                        raise TeamPairingReviewStateError(
                            "existing workspace identity mismatch"
                        )
                    if not existing_identity:
                        connection.executemany(
                            "INSERT INTO workspace_metadata(key,value) VALUES(?,?)",
                            sorted(expected_identity.items()),
                        )

                    checks: Sequence[tuple[str, str, list[tuple[Any, ...]], str]] = (
                        (
                            "source_images",
                            "SELECT image_id,inventory_sequence,relative_path,is_readable FROM source_images ORDER BY inventory_sequence",
                            expected_images,
                            "INSERT INTO source_images(image_id,inventory_sequence,relative_path,is_readable) VALUES(?,?,?,?)",
                        ),
                        (
                            "candidate_batches",
                            "SELECT batch_id,batch_sequence,start_time_utc,end_time_utc FROM candidate_batches ORDER BY batch_sequence",
                            expected_batches,
                            "INSERT INTO candidate_batches(batch_id,batch_sequence,start_time_utc,end_time_utc) VALUES(?,?,?,?)",
                        ),
                        (
                            "batch_members",
                            "SELECT batch_id,image_id,member_sequence FROM batch_members ORDER BY batch_id,member_sequence",
                            sorted(expected_members),
                            "INSERT INTO batch_members(batch_id,image_id,member_sequence) VALUES(?,?,?)",
                        ),
                        (
                            "pair_candidates",
                            "SELECT pair_candidate_id,pair_sequence,before_batch_id,after_batch_id FROM pair_candidates ORDER BY pair_sequence",
                            expected_pairs,
                            "INSERT INTO pair_candidates(pair_candidate_id,pair_sequence,before_batch_id,after_batch_id) VALUES(?,?,?,?)",
                        ),
                    )

                    for label, query, expected, insert_sql in checks:
                        existing = [tuple(row) for row in connection.execute(query).fetchall()]
                        if existing and existing != expected:
                            raise TeamPairingReviewStateError(
                                f"existing candidate {label} mismatch"
                            )
                        if not existing and expected:
                            connection.executemany(insert_sql, expected)

                    connection.execute(
                        "INSERT OR IGNORE INTO batch_reviews(batch_id) SELECT batch_id FROM candidate_batches"
                    )
                    connection.execute(
                        "INSERT OR IGNORE INTO image_reviews(image_id) SELECT image_id FROM source_images"
                    )
                    connection.execute(
                        "INSERT OR IGNORE INTO pair_reviews(pair_candidate_id) SELECT pair_candidate_id FROM pair_candidates"
                    )
                    connection.execute(
                        "INSERT INTO app_state(key,value) VALUES('successful_save_count','0') ON CONFLICT(key) DO NOTHING"
                    )
                    connection.execute(
                        "INSERT INTO app_state(key,value) VALUES('last_view_mode','batch') ON CONFLICT(key) DO NOTHING"
                    )
                    first_batch = expected_batches[0][0] if expected_batches else ""
                    connection.execute(
                        "INSERT INTO app_state(key,value) VALUES('last_view_item_id',?) ON CONFLICT(key) DO NOTHING",
                        (first_batch,),
                    )
                    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                    if integrity != "ok":
                        raise TeamPairingReviewStateError(
                            f"SQLite integrity check failed：{integrity}"
                        )
                    connection.execute("COMMIT")
                except Exception:
                    connection.execute("ROLLBACK")
                    raise
        except sqlite3.DatabaseError as exc:
            raise TeamPairingReviewStateError(
                f"SQLite database corrupt or unreadable：{exc}"
            ) from exc

        self._synchronize_event_log()

    def table_names(self) -> tuple[str, ...]:
        with self._connection() as connection:
            return self._existing_table_names(connection)

    def integrity_check(self) -> str:
        with self._connection() as connection:
            return str(connection.execute("PRAGMA integrity_check").fetchone()[0])

    def _parse_event_log_last_id(self) -> int:
        if not self.event_log_path.exists():
            return 0
        last = 0
        with self.event_log_path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                try:
                    payload = json.loads(raw)
                    event_id = int(payload["event_id"])
                except Exception as exc:
                    raise TeamPairingReviewStateError(
                        f"event log 第 {line_number} 行損壞"
                    ) from exc
                if event_id != last + 1:
                    raise TeamPairingReviewStateError("event log IDs 不連續")
                last = event_id
        return last

    def _database_event_max(self) -> int:
        if not self.database_path.is_file():
            return 0
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(event_id),0) value FROM audit_events"
            ).fetchone()
        return int(row["value"])

    def verify_event_log_continuity(self) -> int:
        last = self._parse_event_log_last_id()
        database_last = self._database_event_max()
        if last != database_last:
            raise TeamPairingReviewStateError(
                "event log 與 SQLite audit event IDs 不連續"
            )
        return last

    def _synchronize_event_log(self) -> None:
        if not self.database_path.is_file():
            return
        last = self._parse_event_log_last_id()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id,entity_type,entity_id,revision,event_type,event_json,created_at_utc
                FROM audit_events WHERE event_id>? ORDER BY event_id
                """,
                (last,),
            ).fetchall()
        if not rows:
            return
        with self.event_log_path.open("a", encoding="utf-8", newline="\n") as handle:
            expected = last + 1
            for row in rows:
                event_id = int(row["event_id"])
                if event_id != expected:
                    raise TeamPairingReviewStateError("audit event IDs 不連續")
                payload = {
                    "event_id": event_id,
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "revision": int(row["revision"]),
                    "event_type": row["event_type"],
                    "created_at_utc": row["created_at_utc"],
                    "details": json.loads(row["event_json"]),
                }
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
                expected += 1
            handle.flush()
            os.fsync(handle.fileno())

    def _validate_canonical_identity(self, canonical: Mapping[str, Any]) -> None:
        reviewer = str(canonical.get("review_reviewer", "")).strip()
        if reviewer != self.identity.reviewer:
            raise TeamPairingReviewStateError("reviewer 與 workspace identity 不符")
        raw_timestamp = str(canonical.get("reviewed_at_utc", "")).strip()
        try:
            timestamp = datetime.fromisoformat(raw_timestamp)
        except ValueError as exc:
            raise TeamPairingReviewStateError("review timestamp 不是 ISO 8601") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise TeamPairingReviewStateError("review timestamp 必須包含時區")

    def _save_review(
        self,
        *,
        entity_type: str,
        entity_id: str,
        table: str,
        id_column: str,
        selection: Mapping[str, Any],
        canonical: Mapping[str, Any],
        field_updates: Mapping[str, Any],
        simulate_failure_after_audit: bool,
    ) -> StoredReview:
        if not self.database_path.is_file():
            raise TeamPairingReviewStateError("state store 尚未初始化")
        self._validate_canonical_identity(canonical)
        saved_at = self._utc_now()

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                current = connection.execute(
                    f"SELECT revision FROM {table} WHERE {id_column}=?",
                    (entity_id,),
                ).fetchone()
                if current is None:
                    raise TeamPairingReviewStateError(
                        f"未知 {entity_type} ID：{entity_id}"
                    )
                revision = int(current["revision"]) + 1
                assignments = [
                    "selection_json=?",
                    "canonical_fields_json=?",
                ]
                values: list[Any] = [
                    self._canonical_json(selection),
                    self._canonical_json(canonical),
                ]
                for field, value in field_updates.items():
                    assignments.append(f"{field}=?")
                    values.append(value)
                assignments.extend(["revision=?", "saved_at_utc=?"])
                values.extend([revision, saved_at, entity_id])
                connection.execute(
                    f"UPDATE {table} SET {','.join(assignments)} WHERE {id_column}=?",
                    values,
                )
                connection.execute(
                    """
                    INSERT INTO audit_events(
                        entity_type,entity_id,revision,event_type,event_json,created_at_utc
                    ) VALUES(?,?,?,?,?,?)
                    """,
                    (
                        entity_type,
                        entity_id,
                        revision,
                        f"{entity_type}_review_saved",
                        self._canonical_json(
                            {"selection": selection, "canonical_fields": canonical}
                        ),
                        saved_at,
                    ),
                )
                if simulate_failure_after_audit:
                    raise TeamPairingReviewStateError("simulated save failure")
                connection.execute(
                    "UPDATE app_state SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT) WHERE key='successful_save_count'"
                )
                connection.execute(
                    "INSERT INTO app_state(key,value) VALUES('last_view_mode',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (entity_type,),
                )
                connection.execute(
                    "INSERT INTO app_state(key,value) VALUES('last_view_item_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (entity_id,),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

        self._synchronize_event_log()
        save_count = self.successful_save_count()
        if save_count % self.backup_every_successful_saves == 0:
            self.create_backup()
        return StoredReview(
            entity_type,
            entity_id,
            dict(selection),
            dict(canonical),
            revision,
            saved_at,
        )

    def save_batch_review(
        self,
        batch_id: str,
        selection: BatchReviewSelection,
        canonical: CanonicalBatchFields,
        *,
        simulate_failure_after_audit: bool = False,
    ) -> StoredReview:
        return self._save_review(
            entity_type="batch",
            entity_id=batch_id,
            table="batch_reviews",
            id_column="batch_id",
            selection=asdict(selection),
            canonical=canonical.as_dict(),
            field_updates={
                "manual_batch_status": canonical.manual_batch_status,
                "manual_vehicle_id": canonical.manual_vehicle_id,
                "manual_stage": canonical.manual_stage,
            },
            simulate_failure_after_audit=simulate_failure_after_audit,
        )

    def save_image_review(
        self,
        image_id: str,
        selection: AngleReviewSelection,
        canonical: CanonicalAngleFields,
        *,
        simulate_failure_after_audit: bool = False,
    ) -> StoredReview:
        return self._save_review(
            entity_type="image",
            entity_id=image_id,
            table="image_reviews",
            id_column="image_id",
            selection=asdict(selection),
            canonical=canonical.as_dict(),
            field_updates={
                "review_status": canonical.review_status,
                "manual_angle": canonical.manual_angle,
            },
            simulate_failure_after_audit=simulate_failure_after_audit,
        )

    def save_pair_review(
        self,
        pair_candidate_id: str,
        selection: PairReviewSelection,
        canonical: CanonicalPairFields,
        *,
        simulate_failure_after_audit: bool = False,
    ) -> StoredReview:
        return self._save_review(
            entity_type="pair",
            entity_id=pair_candidate_id,
            table="pair_reviews",
            id_column="pair_candidate_id",
            selection=asdict(selection),
            canonical=canonical.as_dict(),
            field_updates={
                "manual_pair_status": canonical.manual_pair_status,
                "derived_case_classification": canonical.derived_case_classification,
                "manual_demo_role": canonical.manual_demo_role,
            },
            simulate_failure_after_audit=simulate_failure_after_audit,
        )

    def _get_review(
        self,
        *,
        entity_type: str,
        entity_id: str,
        table: str,
        id_column: str,
    ) -> StoredReview:
        with self._connection() as connection:
            row = connection.execute(
                f"SELECT selection_json,canonical_fields_json,revision,saved_at_utc FROM {table} WHERE {id_column}=?",
                (entity_id,),
            ).fetchone()
        if row is None:
            raise TeamPairingReviewStateError(f"未知 {entity_type} ID：{entity_id}")
        return StoredReview(
            entity_type,
            entity_id,
            json.loads(row["selection_json"]),
            json.loads(row["canonical_fields_json"]),
            int(row["revision"]),
            str(row["saved_at_utc"]),
        )

    def get_batch_review(self, batch_id: str) -> StoredReview:
        return self._get_review(
            entity_type="batch",
            entity_id=batch_id,
            table="batch_reviews",
            id_column="batch_id",
        )

    def successful_save_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key='successful_save_count'"
            ).fetchone()
        return 0 if row is None else int(row["value"])

    def set_last_viewed(self, mode: str, item_id: str) -> None:
        if mode not in self._VIEW_MODES:
            raise TeamPairingReviewStateError(f"不支援的 view mode：{mode}")
        lookup = {
            "batch": ("candidate_batches", "batch_id"),
            "image": ("source_images", "image_id"),
            "pair": ("pair_candidates", "pair_candidate_id"),
        }[mode]
        with self._connection() as connection:
            row = connection.execute(
                f"SELECT 1 FROM {lookup[0]} WHERE {lookup[1]}=?",
                (item_id,),
            ).fetchone()
            if row is None:
                raise TeamPairingReviewStateError(f"未知 {mode} ID：{item_id}")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO app_state(key,value) VALUES('last_view_mode',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (mode,),
                )
                connection.execute(
                    "INSERT INTO app_state(key,value) VALUES('last_view_item_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (item_id,),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def last_viewed(self) -> tuple[str, str]:
        with self._connection() as connection:
            rows = {
                str(row["key"]): str(row["value"])
                for row in connection.execute(
                    "SELECT key,value FROM app_state WHERE key IN ('last_view_mode','last_view_item_id')"
                ).fetchall()
            }
        return rows.get("last_view_mode", "batch"), rows.get("last_view_item_id", "")

    def progress(self) -> TeamPairingProgressCounts:
        with self._connection() as connection:
            image_row = connection.execute(
                "SELECT COUNT(*) total,SUM(review_status='reviewed') reviewed FROM image_reviews"
            ).fetchone()
            batch_row = connection.execute(
                "SELECT COUNT(*) total,SUM(manual_batch_status!='pending') terminal FROM batch_reviews"
            ).fetchone()
            pair_row = connection.execute(
                "SELECT COUNT(*) total,SUM(manual_pair_status!='pending') terminal FROM pair_reviews"
            ).fetchone()
        return TeamPairingProgressCounts(
            int(image_row["total"] or 0),
            int(image_row["reviewed"] or 0),
            int(batch_row["total"] or 0),
            int(batch_row["terminal"] or 0),
            int(pair_row["total"] or 0),
            int(pair_row["terminal"] or 0),
        )

    def batch_ids(
        self,
        filter_name: str = "all",
        *,
        vehicle_id: str | None = None,
        stage: str | None = None,
    ) -> tuple[str, ...]:
        if filter_name not in self._BATCH_FILTERS:
            raise TeamPairingReviewStateError(f"不支援的 batch filter：{filter_name}")
        clauses = ["1=1"]
        params: list[Any] = []
        if filter_name != "all":
            clauses.append("r.manual_batch_status=?")
            params.append(filter_name)
        if vehicle_id is not None:
            clauses.append("r.manual_vehicle_id=?")
            params.append(vehicle_id)
        if stage is not None:
            clauses.append("r.manual_stage=?")
            params.append(stage)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT r.batch_id
                FROM batch_reviews r
                JOIN candidate_batches b ON b.batch_id=r.batch_id
                WHERE {' AND '.join(clauses)}
                ORDER BY b.batch_sequence
                """,
                params,
            ).fetchall()
        return tuple(str(row["batch_id"]) for row in rows)

    def image_ids(self, filter_name: str = "all") -> tuple[str, ...]:
        if filter_name not in self._IMAGE_FILTERS:
            raise TeamPairingReviewStateError(f"不支援的 image filter：{filter_name}")
        clause = "1=1" if filter_name == "all" else "r.review_status=?"
        params: tuple[Any, ...] = () if filter_name == "all" else (filter_name,)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT r.image_id
                FROM image_reviews r
                JOIN source_images s ON s.image_id=r.image_id
                WHERE {clause}
                ORDER BY s.inventory_sequence
                """,
                params,
            ).fetchall()
        return tuple(str(row["image_id"]) for row in rows)

    def pair_ids(self, filter_name: str = "all") -> tuple[str, ...]:
        if filter_name not in self._PAIR_FILTERS:
            raise TeamPairingReviewStateError(f"不支援的 pair filter：{filter_name}")
        clause = "1=1" if filter_name == "all" else "r.manual_pair_status=?"
        params: tuple[Any, ...] = () if filter_name == "all" else (filter_name,)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT r.pair_candidate_id
                FROM pair_reviews r
                JOIN pair_candidates p ON p.pair_candidate_id=r.pair_candidate_id
                WHERE {clause}
                ORDER BY p.pair_sequence
                """,
                params,
            ).fetchall()
        return tuple(str(row["pair_candidate_id"]) for row in rows)

    def create_backup(self, *, timestamp: str | None = None) -> Path:
        if not self.database_path.is_file():
            raise TeamPairingReviewStateError("state store 尚未初始化")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        token = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.backup_dir / f"team_pair_review_{token}.sqlite"
        if target.exists():
            raise TeamPairingReviewStateError("backup path collision")
        temp = self.backup_dir / f".{target.name}.tmp"

        source = self._connect()
        destination = sqlite3.connect(temp)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
            source.close()

        if self.backup_integrity(temp) != "ok":
            temp.unlink(missing_ok=True)
            raise TeamPairingReviewStateError("backup integrity check failed")
        temp.replace(target)
        backups = sorted(self.backup_dir.glob("team_pair_review_*.sqlite"))
        for old in backups[:-self.backup_retention]:
            old.unlink()
        return target

    @staticmethod
    def backup_integrity(path: Path) -> str:
        connection = None
        try:
            connection = sqlite3.connect(path)
            return str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        except sqlite3.DatabaseError as exc:
            raise TeamPairingReviewStateError(
                f"backup SQLite corrupt：{exc}"
            ) from exc
        finally:
            if connection is not None:
                connection.close()
