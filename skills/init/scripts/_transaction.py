"""Private, bounded filesystem effects for init map/prune transactions."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from .lifecycle_core import (
        JOURNAL_NAME,
        NEW_FILE_MODE,
        SNAPSHOT_NAME,
        canonical_json,
        derived_transaction_paths,
        expected_apply,
        file_observation,
        normalize_path,
        safe_path,
        sha256_bytes,
        transaction_basis,
        transaction_id,
        validate_apply_observation,
    )
except ImportError:  # Direct script execution has no package parent.
    from lifecycle_core import (
        JOURNAL_NAME,
        NEW_FILE_MODE,
        SNAPSHOT_NAME,
        canonical_json,
        derived_transaction_paths,
        expected_apply,
        file_observation,
        normalize_path,
        safe_path,
        sha256_bytes,
        transaction_basis,
        transaction_id,
        validate_apply_observation,
    )

_PRIVATE_MODE = 0o600
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _exclusive_write(path: Path, data: bytes, mode: int) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW, mode)
    try:
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError("exclusive write made no progress")
            offset += written
        os.fchmod(descriptor, mode)
        if stat.S_IMODE(os.fstat(descriptor).st_mode) != mode:
            raise OSError("could not set requested mode")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


def _matches(entry: Mapping[str, Any], side: str, root: Path) -> bool:
    exists = entry[f"{side}_exists"]
    path = safe_path(root, str(entry["path"]))
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return not exists
    if not stat.S_ISREG(info.st_mode) or not exists:
        return False
    data, mode = _read_regular_with_mode(path)
    return (
        sha256_bytes(data) == entry[f"{side}_sha256"]
        and mode == entry[f"{side}_mode"]
    )


def _validate_entry(entry: Mapping[str, Any], identifier: str, *, snapshot: bool = False) -> None:
    required = {
        "path", "action", "pre_exists", "pre_sha256", "pre_mode",
        "post_exists", "post_sha256", "post_mode", "apply_path",
        "pre_recovery_path", "post_recovery_path", "state",
    }
    if set(entry) != required:
        raise ValueError("journal entry is incomplete")
    path = normalize_path(str(entry["path"]))
    if snapshot != (path == SNAPSHOT_NAME):
        raise ValueError("journal snapshot role is invalid")
    if not isinstance(entry["pre_exists"], bool) or not isinstance(entry["post_exists"], bool):
        raise ValueError("journal existence flag is invalid")
    expected_action = "delete" if not entry["post_exists"] else ("replace" if entry["pre_exists"] else "create")
    if entry["action"] != expected_action:
        raise ValueError("journal action is invalid")
    for side in ("pre", "post"):
        exists = entry[f"{side}_exists"]
        digest = entry[f"{side}_sha256"]
        mode = entry[f"{side}_mode"]
        recovery = entry[f"{side}_recovery_path"]
        if exists:
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("journal hash is invalid")
            if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
                raise ValueError("journal mode is invalid")
            if recovery != derived_transaction_paths(identifier, path)[f"{side}_recovery_path"]:
                raise ValueError("journal recovery path is invalid")
        elif digest is not None or mode is not None or recovery is not None:
            raise ValueError("journal absent side has an artifact")
    names = derived_transaction_paths(identifier, path)
    if entry["apply_path"] != names["apply_path"]:
        raise ValueError("journal apply path is invalid")
    if entry["state"] not in {"pending", "applying", "applied", "rolling-back", "rolled-back"}:
        raise ValueError("journal target state is invalid")


def _validate_journal(journal: Mapping[str, Any]) -> None:
    journal_keys = {
        "schema_version", "transaction_id", "operation", "phase",
        "recovery_from_phase", "intended_snapshot_sha256", "snapshot", "targets",
    }
    if not isinstance(journal, Mapping) or set(journal) != journal_keys or journal.get("schema_version") != 1:
        raise ValueError("journal schema version is invalid")
    identifier = journal.get("transaction_id")
    if not isinstance(identifier, str) or len(identifier) != 64:
        raise ValueError("journal transaction id is invalid")
    operation = journal.get("operation")
    targets = journal.get("targets")
    snapshot = journal.get("snapshot")
    if operation not in {"map", "prune"} or not isinstance(targets, list) or not isinstance(snapshot, Mapping):
        raise ValueError("journal schema is invalid")
    if journal.get("phase") not in {"preparing", "prepared", "applying-products", "products-applied", "committing-snapshot", "snapshot-committed", "cleaning", "recovery-required"}:
        raise ValueError("journal phase is invalid")
    recovery_phases = {None, "preparing", "prepared", "applying-products", "products-applied", "committing-snapshot", "snapshot-committed", "cleaning"}
    if journal.get("recovery_from_phase") not in recovery_phases:
        raise ValueError("journal recovery phase is invalid")
    if (journal["phase"] == "recovery-required") != (journal["recovery_from_phase"] is not None):
        raise ValueError("journal recovery phase binding is invalid")
    if len({str(entry.get("path")) for entry in targets if isinstance(entry, Mapping)}) != len(targets):
        raise ValueError("journal target paths are not unique")
    for entry in targets:
        if not isinstance(entry, Mapping):
            raise ValueError("journal target is invalid")
        _validate_entry(entry, identifier)
    _validate_entry(snapshot, identifier, snapshot=True)
    if snapshot["action"] not in {"create", "replace"}:
        raise ValueError("journal snapshot action is invalid")
    if journal["intended_snapshot_sha256"] != snapshot["post_sha256"]:
        raise ValueError("journal intended snapshot hash is invalid")
    if any(entry["path"] == SNAPSHOT_NAME for entry in targets):
        raise ValueError("journal target overlaps snapshot")
    if transaction_id(transaction_basis(operation, targets, snapshot)) != identifier:
        raise ValueError("journal transaction identity mismatch")


def _validate_artifact(root: Path, relative: str, digest: str, mode: int) -> Path:
    path = safe_path(root, relative, require_exists=True)
    data, observed_mode = _read_regular_with_mode(path)
    if observed_mode != mode or sha256_bytes(data) != digest:
        raise ValueError("transaction artifact does not match its bound role")
    return path


def _read_regular_with_mode(path: Path) -> tuple[bytes, int]:
    descriptor = os.open(path, os.O_RDONLY | _NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("transaction artifact is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), stat.S_IMODE(info.st_mode)
    finally:
        os.close(descriptor)


def _read_regular(path: Path) -> bytes:
    return _read_regular_with_mode(path)[0]


def _effect_bytes(effect: Mapping[str, Any]) -> bytes | None:
    action = effect.get("action")
    if action == "delete":
        return None
    value = effect.get("bytes", effect.get("content"))
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    raise ValueError("write effect requires bytes or UTF-8 content")


def _effect_entry(root: Path, effect: Mapping[str, Any]) -> tuple[dict[str, Any], bytes | None]:
    relative = normalize_path(str(effect["path"]))
    destination = safe_path(root, relative)
    before_exists = destination.exists()
    if before_exists:
        before = file_observation(root, relative)
    else:
        before = None
    expected_sha = effect.get("expected_pre_sha256")
    expected_mode = effect.get("expected_pre_mode")
    if expected_sha is not None or expected_mode is not None:
        if before is None or before["sha256"] != expected_sha or before["mode"] != expected_mode:
            raise ValueError("accepted target preimage changed")
    after = _effect_bytes(effect)
    action = "delete" if after is None else ("replace" if before else "create")
    mode = int(effect.get("mode", before["mode"] if before else NEW_FILE_MODE)) if after is not None else None
    if mode is not None and not 0 <= mode <= 0o7777:
        raise ValueError("effect mode is outside S_IMODE range")
    entry = {"path": relative, "action": action, "pre_exists": bool(before), "pre_sha256": before["sha256"] if before else None, "pre_mode": before["mode"] if before else None, "post_exists": after is not None, "post_sha256": sha256_bytes(after) if after is not None else None, "post_mode": mode}
    return entry, after


def _journal_write(root: Path, journal: Mapping[str, Any]) -> None:
    _validate_journal(journal)
    transaction = str(journal["transaction_id"])
    next_relative = derived_transaction_paths(transaction, SNAPSHOT_NAME)["next_path"]
    next_path = safe_path(root, next_relative)
    if next_path.exists():
        info = os.lstat(next_path)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != _PRIVATE_MODE:
            raise ValueError("orphan next journal artifact is unsafe")
        try:
            orphan = json.loads(_read_regular(next_path).decode("utf-8"))
            _validate_journal(orphan)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError("orphan next journal artifact is unsafe") from error
        if orphan["transaction_id"] != transaction:
            raise ValueError("orphan next journal artifact has the wrong identity")
        os.unlink(next_path)
        _fsync_directory(next_path.parent)
    _exclusive_write(next_path, canonical_json(dict(journal), pretty=True), _PRIVATE_MODE)
    os.replace(next_path, root / JOURNAL_NAME)
    _fsync_directory(root)


def _image_copy(root: Path, relative: str, data: bytes) -> None:
    path = safe_path(root, relative)
    _exclusive_write(path, data, _PRIVATE_MODE)
    if sha256_bytes(_read_regular(path)) != sha256_bytes(data) or stat.S_IMODE(os.lstat(path).st_mode) != _PRIVATE_MODE:
        raise ValueError("recovery image verification failed")


def _prepare_apply(root: Path, entry: Mapping[str, Any], direction: str) -> Path | None:
    expected = expected_apply(entry, direction)
    if expected is None:
        return None
    source_key = "post_recovery_path" if direction in {"forward", "complete"} else "pre_recovery_path"
    source_relative = entry.get(source_key)
    if not source_relative:
        raise ValueError("missing immutable recovery image")
    source = _validate_artifact(root, str(source_relative), expected["sha256"], _PRIVATE_MODE)
    data = _read_regular(source)
    apply_path = safe_path(root, str(entry["apply_path"]))
    _exclusive_write(apply_path, data, int(expected["mode"]))
    observation = {"regular": stat.S_ISREG(os.lstat(apply_path).st_mode), "sha256": sha256_bytes(_read_regular(apply_path)), "mode": stat.S_IMODE(os.lstat(apply_path).st_mode)}
    if not validate_apply_observation(entry, direction, observation):
        raise ValueError("apply image does not match bound destination state")
    return apply_path


def _consume_apply(root: Path, entry: Mapping[str, Any], direction: str) -> None:
    destination = safe_path(root, str(entry["path"]))
    expected = expected_apply(entry, direction)
    if expected is None:
        if destination.exists():
            info = os.lstat(destination)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("delete destination is not regular")
            os.unlink(destination)
            _fsync_directory(destination.parent)
        return
    apply_path = safe_path(root, str(entry["apply_path"]))
    if apply_path.exists():
        _validate_artifact(root, str(entry["apply_path"]), expected["sha256"], int(expected["mode"]))
    else:
        apply_path = _prepare_apply(root, entry, direction)
        assert apply_path is not None
    # The source was re-opened and checked after its file and parent fsync; rename
    # installs its bytes and mode atomically. Do not chmod the destination afterward.
    os.replace(apply_path, destination)
    descriptor = os.open(destination, os.O_RDONLY | _NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(destination.parent)
    observed = file_observation(root, str(entry["path"]))
    if observed["sha256"] != expected["sha256"] or observed["mode"] != expected["mode"]:
        raise ValueError("renamed destination does not match bound image")


def _cleanup(root: Path, journal: Mapping[str, Any]) -> None:
    _validate_journal(journal)
    for entry in list(journal["targets"]) + [journal["snapshot"]]:
        for key in ("apply_path", "pre_recovery_path", "post_recovery_path"):
            relative = entry.get(key)
            if not relative:
                continue
            path = safe_path(root, str(relative))
            if path.exists():
                if key == "apply_path":
                    expected = expected_apply(entry, "forward")
                    rollback = expected_apply(entry, "rollback")
                    valid = (
                        expected is not None
                        and _matches_artifact(path, expected["sha256"], int(expected["mode"]))
                    ) or (
                        rollback is not None
                        and _matches_artifact(path, rollback["sha256"], int(rollback["mode"]))
                    )
                    if not valid:
                        raise ValueError("cleanup apply artifact is unsafe")
                else:
                    side = "pre" if key.startswith("pre_") else "post"
                    _validate_artifact(root, str(relative), entry[f"{side}_sha256"], _PRIVATE_MODE)
                os.unlink(path)
                _fsync_directory(path.parent)
    next_path = safe_path(root, derived_transaction_paths(str(journal["transaction_id"]), SNAPSHOT_NAME)["next_path"])
    if next_path.exists():
        info = os.lstat(next_path)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != _PRIVATE_MODE:
            raise ValueError("cleanup next journal artifact is unsafe")
        try:
            next_journal = json.loads(_read_regular(next_path).decode("utf-8"))
            _validate_journal(next_journal)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("cleanup next journal artifact is unsafe") from exc
        if next_journal["transaction_id"] != journal["transaction_id"]:
            raise ValueError("cleanup next journal artifact has the wrong identity")
        os.unlink(next_path)
        _fsync_directory(next_path.parent)
    journal_path = root / JOURNAL_NAME
    if journal_path.exists():
        journal_info = os.lstat(journal_path)
        if not stat.S_ISREG(journal_info.st_mode) or stat.S_IMODE(journal_info.st_mode) != _PRIVATE_MODE:
            raise ValueError("journal artifact mode is unsafe")
        os.unlink(journal_path)
        _fsync_directory(root)


def _matches_artifact(path: Path, digest: str, mode: int) -> bool:
    try:
        data, observed_mode = _read_regular_with_mode(path)
        return observed_mode == mode and sha256_bytes(data) == digest
    except (OSError, ValueError):
        return False


def _snapshot_entry(root: Path, payload: Mapping[str, Any]) -> tuple[dict[str, Any], bytes]:
    data = canonical_json(dict(payload), pretty=True)
    effect = {"path": SNAPSHOT_NAME, "bytes": data, "mode": NEW_FILE_MODE}
    entry, content = _effect_entry(root, effect)
    assert content is not None
    return entry, content


def apply(
    root: Path,
    effects: list[dict[str, Any]],
    accepted_ids: set[str],
    *,
    snapshot_payload: Mapping[str, Any] | None = None,
    operation: str = "map",
) -> dict[str, Any]:
    """Apply accepted product effects; with snapshot_payload, commit snapshot last and clean journal last."""
    root = root.resolve(strict=True)
    if (root / JOURNAL_NAME).exists():
        return recover(root, accepted_ids)
    entries: list[dict[str, Any]] = []
    contents: list[bytes | None] = []
    for effect in effects:
        proposal_id = effect.get("proposal_id")
        if proposal_id and proposal_id not in accepted_ids:
            raise ValueError("effect lacks accepted proposal")
        entry, content = _effect_entry(root, effect)
        entries.append(entry)
        contents.append(content)
    snapshot, snapshot_content = _snapshot_entry(root, snapshot_payload or {"schema_version": 1, "repository_root": ".", "owned_artifacts": [], "last_applied_topology": {"max_depth": 3, "shim_policy": "off", "coverage_units": [], "exclusions": []}})
    basis = transaction_basis(operation, entries, snapshot)
    identifier = transaction_id(basis)
    for entry in entries + [snapshot]:
        names = derived_transaction_paths(identifier, entry["path"])
        entry["pre_recovery_path"] = names["pre_recovery_path"] if entry["pre_exists"] else None
        entry["post_recovery_path"] = names["post_recovery_path"] if entry["post_exists"] else None
        entry["apply_path"] = names["apply_path"]
        entry["state"] = "pending"
    journal = {"schema_version": 1, "transaction_id": identifier, "operation": operation, "phase": "preparing", "recovery_from_phase": None, "intended_snapshot_sha256": snapshot["post_sha256"], "snapshot": snapshot, "targets": entries}
    _validate_journal(journal)
    for entry in entries + [snapshot]:
        if not _matches(entry, "pre", root):
            raise ValueError("target preimage changed before journal creation")
    _exclusive_write(root / JOURNAL_NAME, canonical_json(journal, pretty=True), _PRIVATE_MODE)
    for entry, content in zip(entries + [snapshot], contents + [snapshot_content]):
        if entry["pre_exists"]:
            if not _matches(entry, "pre", root):
                raise ValueError("target preimage changed before recovery image copy")
            _image_copy(root, entry["pre_recovery_path"], _read_regular(safe_path(root, entry["path"], require_exists=True)))
        if entry["post_exists"]:
            assert content is not None
            _image_copy(root, entry["post_recovery_path"], content)
    for entry in entries + [snapshot]:
        if expected_apply(entry, "forward") is not None:
            _prepare_apply(root, entry, "forward")
    journal["phase"] = "prepared"
    _journal_write(root, journal)
    journal["phase"] = "applying-products"
    _journal_write(root, journal)
    for entry in entries:
        entry["state"] = "applying"
        _journal_write(root, journal)
        _consume_apply(root, entry, "forward")
        entry["state"] = "applied"
        _journal_write(root, journal)
    journal["phase"] = "products-applied"
    _journal_write(root, journal)
    if snapshot_payload is None:
        return {"transaction_id": identifier, "phase": journal["phase"], "effects": entries}
    journal["phase"] = "committing-snapshot"
    _journal_write(root, journal)
    _consume_apply(root, snapshot, "forward")
    journal["phase"] = "snapshot-committed"
    _journal_write(root, journal)
    journal["phase"] = "cleaning"
    _journal_write(root, journal)
    _cleanup(root, journal)
    return {"transaction_id": identifier, "phase": "complete", "effects": entries}

def recover(root: Path, accepted_ids: set[str] | None = None) -> dict[str, Any]:
    """Finish recognized committed work or reverse a recognized pre-commit mix."""
    root = root.resolve(strict=True)
    journal_path = root / JOURNAL_NAME
    try:
        journal_info = os.lstat(journal_path)
        if not stat.S_ISREG(journal_info.st_mode) or stat.S_IMODE(journal_info.st_mode) != _PRIVATE_MODE:
            raise ValueError("journal artifact is unsafe")
        journal = json.loads(_read_regular(journal_path).decode("utf-8"))
        _validate_journal(journal)
        identifier = journal["transaction_id"]
        targets = list(journal["targets"])
        snapshot = journal["snapshot"]

        def matches(entry: Mapping[str, Any], side: str) -> bool:
            try:
                return _matches(entry, side, root)
            except (FileNotFoundError, OSError, ValueError):
                return False

        committed = matches(snapshot, "post") and all(matches(item, "post") for item in targets)
        if committed and journal["phase"] in {"committing-snapshot", "snapshot-committed", "cleaning"}:
            _cleanup(root, journal)
            return {"transaction_id": identifier, "phase": "complete", "recovered": True}
        rollbackable = matches(snapshot, "pre") and all(matches(item, "pre") or matches(item, "post") for item in targets)
        if rollbackable and journal["phase"] in {"prepared", "applying-products", "products-applied", "committing-snapshot", "recovery-required"}:
            for entry in reversed(targets):
                if matches(entry, "post"):
                    entry["state"] = "rolling-back"
                    _journal_write(root, journal)
                    _consume_apply(root, entry, "rollback")
                    if not matches(entry, "pre"):
                        raise ValueError("rollback image verification failed")
                    entry["state"] = "rolled-back"
                    _journal_write(root, journal)
            journal["phase"] = "cleaning"
            journal["recovery_from_phase"] = None
            _journal_write(root, journal)
            _cleanup(root, journal)
            return {"transaction_id": identifier, "phase": "rolled-back", "recovered": True}

        accepted = accepted_ids or set()
        if matches(snapshot, "pre"):
            proposal_id = "P-RECOVER-ROLLBACK-TRANSACTION-" + sha256_bytes(
                canonical_json({"transaction_id": identifier, "action": "recover-rollback-transaction"})
            )[:12]
            if proposal_id not in accepted:
                raise ValueError(f"recovery requires acceptance: {proposal_id}")
            for entry in reversed(targets):
                if not matches(entry, "pre"):
                    _consume_apply(root, entry, "rollback")
                if not matches(entry, "pre"):
                    raise ValueError("accepted rollback image verification failed")
                entry["state"] = "rolled-back"
            journal["phase"] = "cleaning"
            journal["recovery_from_phase"] = None
            _journal_write(root, journal)
            _cleanup(root, journal)
            return {"transaction_id": identifier, "phase": "rolled-back", "recovered": True, "accepted_proposal": proposal_id}

        if matches(snapshot, "post"):
            proposal_id = "P-RECOVER-COMPLETE-TRANSACTION-" + sha256_bytes(
                canonical_json({"transaction_id": identifier, "action": "recover-complete-transaction"})
            )[:12]
            if proposal_id not in accepted:
                raise ValueError(f"recovery requires acceptance: {proposal_id}")
            for entry in targets:
                if not matches(entry, "post"):
                    _consume_apply(root, entry, "complete")
                if not matches(entry, "post"):
                    raise ValueError("accepted completion image verification failed")
                entry["state"] = "applied"
            journal["phase"] = "cleaning"
            journal["recovery_from_phase"] = None
            _journal_write(root, journal)
            _cleanup(root, journal)
            return {"transaction_id": identifier, "phase": "complete", "recovered": True, "accepted_proposal": proposal_id}
        raise ValueError("journal state cannot be recovered safely")
    except (KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"transaction recovery is blocked: {exc}; journal evidence was preserved") from exc
