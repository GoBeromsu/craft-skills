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
        normalize_path,
        operation_root,
        pinned_root_fd,
        validate_snapshot,
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
        normalize_path,
        operation_root,
        pinned_root_fd,
        validate_snapshot,
        sha256_bytes,
        transaction_basis,
        transaction_id,
        validate_apply_observation,
    )

_PRIVATE_MODE = 0o600
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _valid_hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


class RecoveryBlocked(RuntimeError):
    """Recovery cannot start safely or requires fresh acceptance."""


class RecoveryFailure(RuntimeError):
    """A validated recovery attempt failed after mutation began."""


def _root_fd(root: Path) -> int:
    return pinned_root_fd(root)


_pinned_root = operation_root


def _exclusive_write_relative(root: Path, relative: str, data: bytes, mode: int) -> None:
    parent_fd, name = _open_parent_dir(root, relative)
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW,
            mode,
            dir_fd=parent_fd,
        )
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
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def _matches(entry: Mapping[str, Any], side: str, root: Path) -> bool:
    exists = entry[f"{side}_exists"]
    try:
        data, mode = _read_relative_with_mode(root, str(entry["path"]))
    except FileNotFoundError:
        return not exists
    if not exists:
        return False
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
    if not isinstance(entry["path"], str):
        raise ValueError("journal path is invalid")
    path = normalize_path(entry["path"])
    if snapshot != (path == SNAPSHOT_NAME):
        raise ValueError("journal snapshot role is invalid")
    if not isinstance(entry["pre_exists"], bool) or not isinstance(entry["post_exists"], bool):
        raise ValueError("journal existence flag is invalid")
    expected_action = "delete" if not entry["post_exists"] else ("replace" if entry["pre_exists"] else "create")
    if not isinstance(entry["action"], str) or entry["action"] != expected_action:
        raise ValueError("journal action is invalid")
    for side in ("pre", "post"):
        exists = entry[f"{side}_exists"]
        digest = entry[f"{side}_sha256"]
        mode = entry[f"{side}_mode"]
        recovery = entry[f"{side}_recovery_path"]
        if exists:
            if not _valid_hash(digest):
                raise ValueError("journal hash is invalid")
            if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
                raise ValueError("journal mode is invalid")
            if not isinstance(recovery, str):
                raise ValueError("journal recovery path is invalid")
            if recovery != derived_transaction_paths(identifier, path)[f"{side}_recovery_path"]:
                raise ValueError("journal recovery path is invalid")
        elif digest is not None or mode is not None or recovery is not None:
            raise ValueError("journal absent side has an artifact")
    names = derived_transaction_paths(identifier, path)
    if not isinstance(entry["apply_path"], str) or entry["apply_path"] != names["apply_path"]:
        raise ValueError("journal apply path is invalid")
    if not isinstance(entry["state"], str) or entry["state"] not in {"pending", "applying", "applied", "rolling-back", "rolled-back"}:
        raise ValueError("journal target state is invalid")


def _validate_journal(journal: Mapping[str, Any]) -> None:
    journal_keys = {
        "schema_version", "transaction_id", "operation", "phase",
        "recovery_from_phase", "intended_snapshot_sha256", "snapshot", "targets",
    }
    if (
        not isinstance(journal, Mapping)
        or set(journal) != journal_keys
        or not isinstance(journal.get("schema_version"), int)
        or isinstance(journal.get("schema_version"), bool)
        or journal.get("schema_version") != 1
    ):
        raise ValueError("journal schema version is invalid")
    identifier = journal.get("transaction_id")
    if not _valid_hash(identifier):
        raise ValueError("journal transaction id is invalid")
    operation = journal.get("operation")
    targets = journal.get("targets")
    snapshot = journal.get("snapshot")
    if not isinstance(operation, str) or operation not in {"map", "prune"} or not isinstance(targets, list) or not isinstance(snapshot, Mapping):
        raise ValueError("journal schema is invalid")
    if not isinstance(journal.get("phase"), str) or journal.get("phase") not in {"preparing", "prepared", "applying-products", "products-applied", "committing-snapshot", "snapshot-committed", "cleaning", "recovery-required"}:
        raise ValueError("journal phase is invalid")
    recovery_phases = {None, "preparing", "prepared", "applying-products", "products-applied", "committing-snapshot", "snapshot-committed", "cleaning"}
    recovery_from = journal.get("recovery_from_phase")
    if recovery_from is not None and not isinstance(recovery_from, str):
        raise ValueError("journal recovery phase is invalid")
    if recovery_from not in recovery_phases:
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
    if not _valid_hash(journal["intended_snapshot_sha256"]) or journal["intended_snapshot_sha256"] != snapshot["post_sha256"]:
        raise ValueError("journal intended snapshot hash is invalid")
    if any(entry["path"] == SNAPSHOT_NAME for entry in targets):
        raise ValueError("journal target overlaps snapshot")
    if transaction_id(transaction_basis(operation, targets, snapshot)) != identifier:
        raise ValueError("journal transaction identity mismatch")


def _validate_artifact(root: Path, relative: str, digest: str, mode: int) -> Path:
    normalize_path(relative)
    data, observed_mode = _read_relative_with_mode(root, relative)
    if observed_mode != mode or sha256_bytes(data) != digest:
        raise ValueError("transaction artifact does not match its bound role")
    return root / relative


def _read_relative_with_mode(root: Path, relative: str) -> tuple[bytes, int]:
    parts = tuple(normalize_path(relative).split("/"))
    directory_fd = _root_fd(root)
    try:
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        descriptor = os.open(parts[-1], os.O_RDONLY | _NOFOLLOW | getattr(os, "O_NONBLOCK", 0), dir_fd=directory_fd)
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
    finally:
        os.close(directory_fd)


def _open_parent_dir(root: Path, relative: str) -> tuple[int, str]:
    parts = tuple(normalize_path(relative).split("/"))
    directory_fd = _root_fd(root)
    try:
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        return directory_fd, parts[-1]
    except Exception:
        os.close(directory_fd)
        raise


def _lstat_relative(root: Path, relative: str) -> os.stat_result:
    parent_fd, name = _open_parent_dir(root, relative)
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    finally:
        os.close(parent_fd)


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
    if not isinstance(effect.get("path"), str):
        raise ValueError("effect path is invalid")
    relative = normalize_path(effect["path"])
    try:
        before_bytes, before_mode = _read_relative_with_mode(root, relative)
    except FileNotFoundError:
        before = None
    except OSError as error:
        raise ValueError("effect target is unsafe or unreadable") from error
    else:
        before = {
            "path": relative,
            "sha256": sha256_bytes(before_bytes),
            "mode": before_mode,
            "size": len(before_bytes),
        }
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
    try:
        next_bytes, next_mode = _read_relative_with_mode(root, next_relative)
    except FileNotFoundError:
        pass
    else:
        if next_mode != _PRIVATE_MODE:
            raise ValueError("orphan next journal artifact is unsafe")
        try:
            orphan = json.loads(next_bytes.decode("utf-8"))
            _validate_journal(orphan)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError("orphan next journal artifact is unsafe") from error
        if orphan["transaction_id"] != transaction:
            raise ValueError("orphan next journal artifact has the wrong identity")
        root_fd = _root_fd(root)
        try:
            os.unlink(next_relative, dir_fd=root_fd)
            os.fsync(root_fd)
        finally:
            os.close(root_fd)
    _exclusive_write_relative(root, next_relative, canonical_json(dict(journal), pretty=True), _PRIVATE_MODE)
    root_fd = _root_fd(root)
    try:
        os.replace(next_relative, JOURNAL_NAME, src_dir_fd=root_fd, dst_dir_fd=root_fd)
        os.fsync(root_fd)
    finally:
        os.close(root_fd)


def _image_copy(root: Path, relative: str, data: bytes) -> None:
    _exclusive_write_relative(root, relative, data, _PRIVATE_MODE)
    observed, mode = _read_relative_with_mode(root, relative)
    if sha256_bytes(observed) != sha256_bytes(data) or mode != _PRIVATE_MODE:
        raise ValueError("recovery image verification failed")


def _prepare_apply(root: Path, entry: Mapping[str, Any], direction: str) -> Path | None:
    expected = expected_apply(entry, direction)
    if expected is None:
        return None
    source_key = "post_recovery_path" if direction in {"forward", "complete"} else "pre_recovery_path"
    source_relative = entry.get(source_key)
    if not source_relative:
        raise ValueError("missing immutable recovery image")
    _validate_artifact(root, str(source_relative), expected["sha256"], _PRIVATE_MODE)
    data, _ = _read_relative_with_mode(root, str(source_relative))
    apply_path = root / normalize_path(str(entry["apply_path"]))
    _exclusive_write_relative(root, str(entry["apply_path"]), data, int(expected["mode"]))
    applied, applied_mode = _read_relative_with_mode(root, str(entry["apply_path"]))
    observation = {"regular": True, "sha256": sha256_bytes(applied), "mode": applied_mode}
    if not validate_apply_observation(entry, direction, observation):
        raise ValueError("apply image does not match bound destination state")
    return apply_path


def _consume_apply(root: Path, entry: Mapping[str, Any], direction: str) -> None:
    destination_relative = str(entry["path"])
    expected = expected_apply(entry, direction)
    if expected is None:
        parent_fd, name = _open_parent_dir(root, destination_relative)
        try:
            try:
                descriptor = os.open(name, os.O_RDONLY | _NOFOLLOW, dir_fd=parent_fd)
            except FileNotFoundError:
                return
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise ValueError("delete destination is not regular")
            finally:
                os.close(descriptor)
            os.unlink(name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return
    apply_path = root / normalize_path(str(entry["apply_path"]))
    try:
        _validate_artifact(root, str(entry["apply_path"]), expected["sha256"], int(expected["mode"]))
    except FileNotFoundError:
        apply_path = _prepare_apply(root, entry, direction)
        assert apply_path is not None
    except ValueError:
        existing, existing_mode = _read_relative_with_mode(root, str(entry["apply_path"]))
        bound_images = [
            image
            for candidate_direction in ("forward", "rollback")
            if (image := expected_apply(entry, candidate_direction)) is not None
        ]
        if not any(
            sha256_bytes(existing) == image["sha256"] and existing_mode == int(image["mode"])
            for image in bound_images
        ):
            raise ValueError("existing apply artifact is not a bound transaction image")
        parent_fd, name = _open_parent_dir(root, str(entry["apply_path"]))
        try:
            os.unlink(name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        apply_path = _prepare_apply(root, entry, direction)
        assert apply_path is not None
    # The source was re-opened and checked after its file and parent fsync; rename
    # installs its bytes and mode atomically. Do not chmod the destination afterward.
    apply_relative = str(entry["apply_path"])
    source_parent_fd, source_name = _open_parent_dir(root, apply_relative)
    destination_parent_fd, destination_name = _open_parent_dir(root, destination_relative)
    try:
        os.replace(
            source_name,
            destination_name,
            src_dir_fd=source_parent_fd,
            dst_dir_fd=destination_parent_fd,
        )
        os.fsync(destination_parent_fd)
        descriptor = os.open(destination_name, os.O_RDONLY | _NOFOLLOW, dir_fd=destination_parent_fd)
        try:
            info = os.fstat(descriptor)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            os.fsync(descriptor)
            observed_hash = sha256_bytes(b"".join(chunks))
            observed_mode = stat.S_IMODE(info.st_mode)
        finally:
            os.close(descriptor)
    finally:
        os.close(source_parent_fd)
        os.close(destination_parent_fd)
    if observed_hash != expected["sha256"] or observed_mode != expected["mode"]:
        raise ValueError("renamed destination does not match bound image")


def _cleanup(root: Path, journal: Mapping[str, Any]) -> None:
    _validate_journal(journal)
    for entry in list(journal["targets"]) + [journal["snapshot"]]:
        for key in ("apply_path", "pre_recovery_path", "post_recovery_path"):
            relative = entry.get(key)
            if not relative:
                continue
            try:
                data, mode = _read_relative_with_mode(root, str(relative))
            except FileNotFoundError:
                continue
            if key == "apply_path":
                expected = expected_apply(entry, "forward")
                rollback = expected_apply(entry, "rollback")
                valid = (
                    expected is not None
                    and sha256_bytes(data) == expected["sha256"]
                    and mode == int(expected["mode"])
                ) or (
                    rollback is not None
                    and sha256_bytes(data) == rollback["sha256"]
                    and mode == int(rollback["mode"])
                )
                if not valid:
                    raise ValueError("cleanup apply artifact is unsafe")
            else:
                side = "pre" if key.startswith("pre_") else "post"
                if sha256_bytes(data) != entry[f"{side}_sha256"] or mode != _PRIVATE_MODE:
                    raise ValueError("cleanup recovery artifact is unsafe")
            parent_fd, name = _open_parent_dir(root, str(relative))
            try:
                os.unlink(name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
    next_relative = derived_transaction_paths(str(journal["transaction_id"]), SNAPSHOT_NAME)["next_path"]
    try:
        next_bytes, next_mode = _read_relative_with_mode(root, next_relative)
    except FileNotFoundError:
        pass
    else:
        if next_mode != _PRIVATE_MODE:
            raise ValueError("cleanup next journal artifact is unsafe")
        try:
            next_journal = json.loads(next_bytes.decode("utf-8"))
            _validate_journal(next_journal)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("cleanup next journal artifact is unsafe") from exc
        if next_journal["transaction_id"] != journal["transaction_id"]:
            raise ValueError("cleanup next journal artifact has the wrong identity")
        root_fd = _root_fd(root)
        try:
            os.unlink(next_relative, dir_fd=root_fd)
            os.fsync(root_fd)
        finally:
            os.close(root_fd)
    try:
        _, journal_mode = _read_relative_with_mode(root, JOURNAL_NAME)
    except FileNotFoundError:
        pass
    else:
        if journal_mode != _PRIVATE_MODE:
            raise ValueError("journal artifact mode is unsafe")
        root_fd = _root_fd(root)
        try:
            os.unlink(JOURNAL_NAME, dir_fd=root_fd)
            os.fsync(root_fd)
        finally:
            os.close(root_fd)


def _snapshot_entry(root: Path, payload: Mapping[str, Any]) -> tuple[dict[str, Any], bytes]:
    data = canonical_json(dict(payload), pretty=True)
    effect = {"path": SNAPSHOT_NAME, "bytes": data, "mode": NEW_FILE_MODE}
    entry, content = _effect_entry(root, effect)
    assert content is not None
    return entry, content


def _apply_pinned(
    root: Path,
    effects: list[dict[str, Any]],
    accepted_ids: set[str],
    *,
    snapshot_payload: Mapping[str, Any],
    operation: str = "map",
) -> dict[str, Any]:
    """Apply accepted product effects, commit the validated snapshot last, and clean the journal last."""
    try:
        _lstat_relative(root, JOURNAL_NAME)
    except FileNotFoundError:
        pass
    else:
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
    # The snapshot is the authority every later audit, prune, and recovery decision
    # trusts, so it must satisfy the exact ownership contract before it is journaled.
    validate_snapshot(snapshot_payload)
    snapshot, snapshot_content = _snapshot_entry(root, snapshot_payload)
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
    _exclusive_write_relative(root, JOURNAL_NAME, canonical_json(journal, pretty=True), _PRIVATE_MODE)
    for entry, content in zip(entries + [snapshot], contents + [snapshot_content]):
        if entry["pre_exists"]:
            if not _matches(entry, "pre", root):
                raise ValueError("target preimage changed before recovery image copy")
            preimage, _ = _read_relative_with_mode(root, str(entry["path"]))
            _image_copy(root, entry["pre_recovery_path"], preimage)
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
    journal["phase"] = "committing-snapshot"
    _journal_write(root, journal)
    _consume_apply(root, snapshot, "forward")
    journal["phase"] = "snapshot-committed"
    _journal_write(root, journal)
    journal["phase"] = "cleaning"
    _journal_write(root, journal)
    _cleanup(root, journal)
    return {"transaction_id": identifier, "phase": "complete", "effects": entries}


def apply(
    root: Path,
    effects: list[dict[str, Any]],
    accepted_ids: set[str],
    *,
    snapshot_payload: Mapping[str, Any],
    operation: str = "map",
) -> dict[str, Any]:
    root = root.absolute()
    with _pinned_root(root):
        return _apply_pinned(
            root,
            effects,
            accepted_ids,
            snapshot_payload=snapshot_payload,
            operation=operation,
        )

def _recovery_proposal_id(
    root: Path,
    journal: Mapping[str, Any],
    journal_bytes: bytes,
    action: str,
    selected_images: Iterable[Mapping[str, Any]],
) -> str:
    observed: list[dict[str, Any]] = []
    for entry in list(journal["targets"]) + [journal["snapshot"]]:
        try:
            data, mode = _read_relative_with_mode(root, str(entry["path"]))
            observed.append({"path": entry["path"], "exists": True, "sha256": sha256_bytes(data), "mode": mode})
        except FileNotFoundError:
            observed.append({"path": entry["path"], "exists": False, "sha256": None, "mode": None})
    basis = {
        "transaction_id": journal["transaction_id"],
        "action": action,
        "journal_sha256": sha256_bytes(journal_bytes),
        "observed": observed,
        "selected_images": [dict(image) for image in selected_images],
    }
    return "P-" + action.upper() + "-" + sha256_bytes(canonical_json(basis))[:12]


def _preflight_recovery_images(
    root: Path,
    targets: Iterable[Mapping[str, Any]],
    direction: str,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    use_post = direction == "complete"
    side = "post" if use_post else "pre"
    for entry in targets:
        expected = expected_apply(entry, direction)
        if expected is None:
            selected.append({"path": entry["path"], "destination_exists": False, "recovery_path": None, "sha256": None, "mode": None})
            continue
        recovery_path = entry[f"{side}_recovery_path"]
        if not isinstance(recovery_path, str):
            raise ValueError("selected immutable recovery image is missing")
        _validate_artifact(root, recovery_path, expected["sha256"], _PRIVATE_MODE)
        selected.append({
            "path": entry["path"],
            "destination_exists": True,
            "recovery_path": recovery_path,
            "sha256": expected["sha256"],
            "mode": expected["mode"],
        })
    return selected


def _preflight_transaction_artifacts(
    root: Path,
    journal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    observed: list[dict[str, Any]] = []
    for entry in list(journal["targets"]) + [journal["snapshot"]]:
        for side in ("pre", "post"):
            if not entry[f"{side}_exists"]:
                continue
            relative = entry[f"{side}_recovery_path"]
            _validate_artifact(root, relative, entry[f"{side}_sha256"], _PRIVATE_MODE)
            observed.append({
                "role": f"{side}-recovery",
                "target": entry["path"],
                "path": relative,
                "exists": True,
                "sha256": entry[f"{side}_sha256"],
                "mode": _PRIVATE_MODE,
            })
        apply_relative = entry["apply_path"]
        try:
            data, mode = _read_relative_with_mode(root, apply_relative)
        except FileNotFoundError:
            observed.append({
                "role": "apply",
                "target": entry["path"],
                "path": apply_relative,
                "exists": False,
                "sha256": None,
                "mode": None,
            })
            continue
        candidates = [
            image
            for direction in ("forward", "rollback")
            if (image := expected_apply(entry, direction)) is not None
        ]
        digest = sha256_bytes(data)
        if not any(digest == image["sha256"] and mode == int(image["mode"]) for image in candidates):
            raise ValueError("apply artifact is not a bound transaction image")
        observed.append({
            "role": "apply",
            "target": entry["path"],
            "path": apply_relative,
            "exists": True,
            "sha256": digest,
            "mode": mode,
        })
    _preflight_cleanup(root, journal)
    next_relative = derived_transaction_paths(str(journal["transaction_id"]), SNAPSHOT_NAME)["next_path"]
    try:
        next_bytes, next_mode = _read_relative_with_mode(root, next_relative)
    except FileNotFoundError:
        observed.append({
            "role": "journal-next",
            "target": SNAPSHOT_NAME,
            "path": next_relative,
            "exists": False,
            "sha256": None,
            "mode": None,
        })
    else:
        observed.append({
            "role": "journal-next",
            "target": SNAPSHOT_NAME,
            "path": next_relative,
            "exists": True,
            "sha256": sha256_bytes(next_bytes),
            "mode": next_mode,
        })
    return observed


def _preflight_cleanup(root: Path, journal: Mapping[str, Any]) -> None:
    for entry in list(journal["targets"]) + [journal["snapshot"]]:
        for key in ("apply_path", "pre_recovery_path", "post_recovery_path"):
            relative = entry.get(key)
            if not relative:
                continue
            try:
                data, mode = _read_relative_with_mode(root, str(relative))
            except FileNotFoundError:
                continue
            if key == "apply_path":
                forward = expected_apply(entry, "forward")
                rollback = expected_apply(entry, "rollback")
                if not (
                    (forward is not None and sha256_bytes(data) == forward["sha256"] and mode == int(forward["mode"]))
                    or (rollback is not None and sha256_bytes(data) == rollback["sha256"] and mode == int(rollback["mode"]))
                ):
                    raise ValueError("cleanup apply artifact is unsafe")
            else:
                side = "pre" if key.startswith("pre_") else "post"
                if sha256_bytes(data) != entry[f"{side}_sha256"] or mode != _PRIVATE_MODE:
                    raise ValueError("cleanup recovery artifact is unsafe")
    next_relative = derived_transaction_paths(str(journal["transaction_id"]), SNAPSHOT_NAME)["next_path"]
    try:
        next_bytes, next_mode = _read_relative_with_mode(root, next_relative)
    except FileNotFoundError:
        pass
    else:
        if next_mode != _PRIVATE_MODE:
            raise ValueError("cleanup next journal artifact is unsafe")
        try:
            next_journal = json.loads(next_bytes.decode("utf-8"))
            _validate_journal(next_journal)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError("cleanup next journal artifact is unsafe") from error
        if next_journal["transaction_id"] != journal["transaction_id"]:
            raise ValueError("cleanup next journal artifact has the wrong identity")


def _recover_pinned(root: Path, accepted_ids: set[str] | None = None) -> dict[str, Any]:
    """Finish recognized committed work or reverse a recognized pre-commit mix."""
    mutating = False
    try:
        journal_bytes, journal_mode = _read_relative_with_mode(root, JOURNAL_NAME)
        if journal_mode != _PRIVATE_MODE:
            raise ValueError("journal artifact is unsafe")
        journal = json.loads(journal_bytes.decode("utf-8"))
        _validate_journal(journal)
        identifier = journal["transaction_id"]
        targets = list(journal["targets"])
        snapshot = journal["snapshot"]
        accepted = accepted_ids or set()

        def matches(entry: Mapping[str, Any], side: str) -> bool:
            try:
                return _matches(entry, side, root)
            except (FileNotFoundError, OSError, ValueError):
                return False

        if journal["phase"] == "preparing":
            if accepted:
                raise ValueError("accepted recovery proposal is not offered by current evidence")
            if not matches(snapshot, "pre") or not all(matches(item, "pre") for item in targets):
                raise ValueError("preparing transaction changed a product")
            _preflight_cleanup(root, journal)
            mutating = True
            _cleanup(root, journal)
            return {"transaction_id": identifier, "phase": "aborted", "recovered": True}

        complete_artifacts = _preflight_transaction_artifacts(root, journal)
        committed = matches(snapshot, "post") and all(matches(item, "post") for item in targets)
        if committed and journal["phase"] in {"committing-snapshot", "snapshot-committed", "cleaning"}:
            if accepted:
                raise ValueError("accepted recovery proposal is not offered by current evidence")
            _preflight_cleanup(root, journal)
            mutating = True
            _cleanup(root, journal)
            return {"transaction_id": identifier, "phase": "complete", "recovered": True}
        rollbackable = matches(snapshot, "pre") and all(matches(item, "pre") or matches(item, "post") for item in targets)
        if rollbackable and journal["phase"] in {"prepared", "applying-products", "products-applied", "committing-snapshot", "recovery-required"}:
            if accepted:
                raise ValueError("accepted recovery proposal is not offered by current evidence")
            _preflight_recovery_images(root, targets, "rollback")
            mutating = True
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

        if matches(snapshot, "pre"):
            selected_images = _preflight_recovery_images(root, targets, "rollback")
            proposal_id = _recovery_proposal_id(root, journal, journal_bytes, "recover-rollback-transaction", [*complete_artifacts, *selected_images])
            if accepted - {proposal_id}:
                raise ValueError("accepted recovery proposal is not offered by current evidence")
            if proposal_id not in accepted:
                raise ValueError(f"recovery requires acceptance: {proposal_id}")
            mutating = True
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
            selected_images = _preflight_recovery_images(root, targets, "complete")
            proposal_id = _recovery_proposal_id(root, journal, journal_bytes, "recover-complete-transaction", [*complete_artifacts, *selected_images])
            if accepted - {proposal_id}:
                raise ValueError("accepted recovery proposal is not offered by current evidence")
            if proposal_id not in accepted:
                raise ValueError(f"recovery requires acceptance: {proposal_id}")
            mutating = True
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
        error_type = RecoveryFailure if mutating else RecoveryBlocked
        raise error_type(f"transaction recovery is blocked: {exc}; journal evidence was preserved") from exc


def recover(root: Path, accepted_ids: set[str] | None = None) -> dict[str, Any]:
    root = root.absolute()
    with _pinned_root(root):
        return _recover_pinned(root, accepted_ids)
