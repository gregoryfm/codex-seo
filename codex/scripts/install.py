#!/usr/bin/env python3
"""Install Codex skills and agent procedures into an explicitly selected scope."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from typing import Any

RECEIPT_NAME = ".codex-seo-managed-agents.json"
RECEIPT_VERSION = 1


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def installation_skills(package: Path, scope: Path) -> list[tuple[Path, Path]]:
    skills = sorted(path for path in (package / "skills").iterdir() if (path / "SKILL.md").is_file())
    agents = sorted((package / "agents").glob("*.toml"))
    if not skills or not agents:
        raise ValueError("The package needs generated skills and agent files. Run convert.py first.")
    return [(source, scope / ".agents" / "skills" / source.name) for source in skills]


def installation_agents(package: Path, agent_home: Path) -> list[tuple[Path, Path]]:
    agents = sorted((package / "agents").glob("*.toml"))
    if not agents:
        raise ValueError("The package needs generated agent files. Run convert.py first.")
    return [(source, agent_home / "agents" / source.name) for source in agents]


def owned_link(source: Path, destination: Path) -> bool:
    try:
        return destination.is_symlink() and destination.resolve() == source.resolve()
    except (OSError, RuntimeError):
        return False


def removal_links(package: Path, scope: Path, agent_home: Path) -> list[tuple[Path, Path]]:
    links = []
    for source_dir, destination_dir in (
        (package / "skills", scope / ".agents" / "skills"),
        (package / "agents", agent_home / "agents"),
    ):
        if not destination_dir.is_dir():
            continue
        for destination in sorted(destination_dir.iterdir()):
            if not destination.is_symlink():
                continue
            try:
                source = destination.resolve()
            except (OSError, RuntimeError):
                continue
            if source.parent == source_dir.resolve() and source.name == destination.name:
                links.append((source, destination))
    return links


def parent_conflict(path: Path) -> str | None:
    current = path
    while not current.exists() and not current.is_symlink():
        if current.parent == current:
            return None
        current = current.parent
    if not current.is_dir():
        return str(current)
    return None


def read_receipt(path: Path, package: Path) -> tuple[dict[str, Any] | None, bytes | None]:
    if not path.exists() and not path.is_symlink():
        return None, None
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Conflicting ownership receipt: {path}")
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid ownership receipt: {path}") from error
    if (
        not isinstance(receipt, dict)
        or receipt.get("version") != RECEIPT_VERSION
        or receipt.get("package") != str(package)
        or not isinstance(receipt.get("agents"), dict)
    ):
        raise ValueError(f"Ownership receipt belongs to a different installer or package: {path}")
    for name, record in receipt["agents"].items():
        source = package / "agents" / name
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not name.endswith(".toml")
            or not isinstance(record, dict)
            or record.get("source") != str(source.resolve())
            or not isinstance(record.get("installed_sha256"), str)
            or len(record["installed_sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in record["installed_sha256"])
        ):
            raise ValueError(f"Invalid ownership entry in receipt: {path}")
    return receipt, raw


def receipt_bytes(package: Path, records: dict[str, dict[str, str]]) -> bytes:
    return (json.dumps({
        "version": RECEIPT_VERSION,
        "package": str(package),
        "agents": dict(sorted(records.items())),
    }, indent=2, sort_keys=True) + "\n").encode()


def file_hash(path: Path) -> str:
    return digest(path.read_bytes())


def ensure_parent(path: Path, created_dirs: list[Path]) -> None:
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    if current.is_symlink() and not current.is_dir():
        raise OSError(f"Parent path is not a directory: {current}")
    if not current.is_dir():
        raise OSError(f"Parent path is not a directory: {current}")
    for directory in reversed(missing):
        directory.mkdir()
        created_dirs.append(directory)


def temp_path(directory: Path, prefix: str) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=prefix, dir=directory)
    os.close(descriptor)
    return Path(name)


def prepared_copy(source: Path, destination: Path, content: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=".codex-seo-agent-", dir=destination.parent)
    path = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(path, stat.S_IMODE(source.stat().st_mode))
        return path
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        path.unlink(missing_ok=True)
        raise


def atomic_write(path: Path, content: bytes) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".codex-seo-receipt-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def remove_staged(path: Path, staged: list[tuple[Path, Path]]) -> None:
    backup = temp_path(path.parent, ".codex-seo-removed-")
    os.replace(path, backup)
    staged.append((path, backup))


def rollback_staged(staged: list[tuple[Path, Path]]) -> None:
    for path, backup in reversed(staged):
        if not backup.exists() and not backup.is_symlink():
            continue
        if path.exists() or path.is_symlink():
            # A concurrent writer may have recreated the destination. Preserve it.
            continue
        os.replace(backup, path)


def cleanup_staged(staged: list[tuple[Path, Path]]) -> None:
    for _, backup in staged:
        try:
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            else:
                backup.unlink(missing_ok=True)
        except OSError:
            pass


def install_plan(package: Path, scope: Path, agent_home: Path) -> tuple[list[dict[str, Any]], bytes | None, bytes, Path, str]:
    skill_links = installation_skills(package, scope)
    agent_copies = installation_agents(package, agent_home)
    receipt_path = agent_home / "agents" / RECEIPT_NAME
    receipt, receipt_raw = read_receipt(receipt_path, package)
    records = dict(receipt["agents"]) if receipt else {}
    changes: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for source, destination in skill_links:
        conflict = parent_conflict(destination.parent)
        if conflict:
            conflicts.append(conflict)
        elif (destination.exists() or destination.is_symlink()) and not owned_link(source, destination):
            conflicts.append(str(destination))
        else:
            changes.append({
                "action": "keep" if owned_link(source, destination) else "link",
                "kind": "skill",
                "source": str(source),
                "destination": str(destination),
            })

    for source, destination in agent_copies:
        conflict = parent_conflict(destination.parent)
        if conflict:
            conflicts.append(conflict)
            continue
        source_content = source.read_bytes()
        source_hash = digest(source_content)
        entry = records.get(source.name)
        present = destination.exists() or destination.is_symlink()
        if not present:
            action = "copy"
        elif owned_link(source, destination):
            action = "migrate"
        elif entry and entry.get("source") == str(source.resolve()) and destination.is_file() and not destination.is_symlink():
            if file_hash(destination) != entry["installed_sha256"]:
                action = "preserve"
            elif file_hash(destination) == source_hash:
                action = "keep"
            else:
                action = "refresh"
        else:
            conflicts.append(str(destination))
            continue
        if action in {"copy", "migrate", "refresh", "keep"}:
            records[source.name] = {"source": str(source.resolve()), "installed_sha256": source_hash}
        changes.append({
            "action": action,
            "kind": "agent",
            "source": str(source),
            "destination": str(destination),
            "sha256": source_hash,
            "previous_sha256": entry["installed_sha256"] if entry else None,
        })

    if conflicts:
        raise ValueError("Conflicting paths. Nothing changed: " + ", ".join(sorted(set(conflicts))))
    desired_receipt = receipt_bytes(package, records)
    receipt_action = "write" if receipt_raw is None else "keep" if receipt_raw == desired_receipt else "update"
    return changes, receipt_raw, desired_receipt, receipt_path, receipt_action


def apply_install(
    package: Path,
    changes: list[dict[str, Any]],
    receipt_path: Path,
    receipt_raw: bytes | None,
    desired_receipt: bytes,
) -> None:
    created_dirs: list[Path] = []
    created_links: list[Path] = []
    replacements: list[tuple[Path, Path | None, str]] = []
    staged_temps: dict[Path, Path] = {}
    try:
        # Prepare every copy before changing an installed file.
        contents: dict[Path, bytes] = {}
        for change in changes:
            if change["kind"] == "agent" and change["action"] in {"copy", "migrate", "refresh"}:
                source = Path(change["source"])
                destination = Path(change["destination"])
                content = source.read_bytes()
                if digest(content) != change["sha256"]:
                    raise ValueError(f"Source changed during installation: {source}")
                ensure_parent(destination.parent, created_dirs)
                contents[destination] = content
        for change in changes:
            if change["kind"] == "skill" and change["action"] == "link":
                destination = Path(change["destination"])
                ensure_parent(destination.parent, created_dirs)
            if change["kind"] == "agent" and change["action"] in {"copy", "migrate", "refresh"}:
                destination = Path(change["destination"])
                temporary = prepared_copy(Path(change["source"]), destination, contents[destination])
                staged_temps[destination] = temporary

        for change in changes:
            if change["kind"] == "skill" and change["action"] == "link":
                source = Path(change["source"])
                destination = Path(change["destination"])
                destination.symlink_to(source, target_is_directory=True)
                created_links.append(destination)

        for change in changes:
            if change["kind"] != "agent" or change["action"] not in {"copy", "migrate", "refresh"}:
                continue
            destination = Path(change["destination"])
            backup = None
            present = destination.exists() or destination.is_symlink()
            if present != (change["action"] != "copy"):
                raise ValueError(f"Installed agent changed during installation: {destination}")
            if present:
                backup = temp_path(destination.parent, ".codex-seo-backup-")
                os.replace(destination, backup)
            replacements.append((destination, backup, change["sha256"]))
            if change["action"] == "migrate" and not owned_link(Path(change["source"]), backup):
                raise ValueError(f"Installed agent link changed during installation: {destination}")
            if change["action"] == "refresh" and (
                backup.is_symlink() or not backup.is_file()
                or file_hash(backup) != change["previous_sha256"]
            ):
                raise ValueError(f"Installed agent changed during installation: {destination}")
            os.replace(staged_temps[destination], destination)

        current_receipt = receipt_path.read_bytes() if receipt_path.exists() and not receipt_path.is_symlink() else None
        if current_receipt != receipt_raw:
            raise ValueError(f"Ownership receipt changed during installation: {receipt_path}")
        ensure_parent(receipt_path.parent, created_dirs)
        if desired_receipt != receipt_raw:
            atomic_write(receipt_path, desired_receipt)
    except BaseException:
        for destination, backup, installed_hash in reversed(replacements):
            if destination.exists() or destination.is_symlink():
                if destination.is_symlink() or not destination.is_file() or file_hash(destination) != installed_hash:
                    continue
                destination.unlink()
            if backup is not None and (backup.exists() or backup.is_symlink()):
                os.replace(backup, destination)
        for destination in reversed(created_links):
            if owned_link(Path(next(item["source"] for item in changes if item["destination"] == str(destination))), destination):
                destination.unlink()
        for temporary in staged_temps.values():
            temporary.unlink(missing_ok=True)
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    cleanup_staged([(destination, backup) for destination, backup, _ in replacements if backup is not None])
    for temporary in staged_temps.values():
        temporary.unlink(missing_ok=True)


def uninstall_plan(package: Path, scope: Path, agent_home: Path) -> tuple[list[dict[str, Any]], bytes | None, Path, str]:
    receipt_path = agent_home / "agents" / RECEIPT_NAME
    receipt, receipt_raw = read_receipt(receipt_path, package)
    changes = []
    links = removal_links(package, scope, agent_home)
    linked_paths = {destination for _, destination in links}
    for source, destination in links:
        changes.append({
            "action": "remove",
            "kind": "skill" if source.parent == (package / "skills").resolve() else "agent-link",
            "source": str(source),
            "destination": str(destination),
        })
    if receipt:
        for name, record in sorted(receipt["agents"].items()):
            destination = agent_home / "agents" / name
            source = Path(record["source"])
            if destination in linked_paths:
                continue
            if not destination.exists() and not destination.is_symlink():
                action = "forget"
            elif destination.is_file() and not destination.is_symlink() and file_hash(destination) == record["installed_sha256"]:
                action = "remove"
            else:
                action = "preserve"
            changes.append({
                "action": action,
                "kind": "agent-copy",
                "source": str(source),
                "destination": str(destination),
                "sha256": record["installed_sha256"],
            })
    receipt_action = "remove" if receipt_raw is not None else "keep"
    return changes, receipt_raw, receipt_path, receipt_action


def apply_uninstall(changes: list[dict[str, Any]], receipt_path: Path, receipt_raw: bytes | None) -> None:
    staged: list[tuple[Path, Path]] = []
    try:
        current_receipt = receipt_path.read_bytes() if receipt_path.exists() and not receipt_path.is_symlink() else None
        if current_receipt != receipt_raw:
            raise ValueError(f"Ownership receipt changed during uninstall: {receipt_path}")
        for change in changes:
            if change["action"] != "remove":
                continue
            destination = Path(change["destination"])
            if not destination.exists() and not destination.is_symlink():
                continue
            if change["kind"] in {"skill", "agent-link"}:
                if not destination.is_symlink() or Path(change["source"]).resolve() != destination.resolve():
                    raise ValueError(f"Installed link changed during uninstall: {destination}")
            elif (
                not destination.is_file()
                or destination.is_symlink()
                or file_hash(destination) != change["sha256"]
            ):
                raise ValueError(f"Installed agent changed during uninstall: {destination}")
            remove_staged(destination, staged)
        if receipt_raw is not None:
            remove_staged(receipt_path, staged)
    except BaseException:
        rollback_staged(staged)
        raise
    cleanup_staged(staged)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--project", type=Path, help="Install in this project only")
    scope.add_argument("--user", action="store_true", help="Install for the current user")
    parser.add_argument("--apply", action="store_true", help="Apply the previewed changes")
    parser.add_argument("--uninstall", action="store_true", help="Remove only this package's installed files")
    args = parser.parse_args()
    package = Path(__file__).resolve().parent.parent
    target = (args.project if args.project is not None else Path.home()).expanduser().resolve()
    agent_home = (
        Path(os.environ.get("CODEX_HOME", str(target / ".codex"))).expanduser().resolve()
        if args.user else target / ".codex"
    )
    try:
        if args.uninstall:
            changes, receipt_raw, receipt_path, receipt_action = uninstall_plan(package, target, agent_home)
            plan = {
                "applied": args.apply,
                "changes": changes,
                "ownership_receipt": {"action": receipt_action, "destination": str(receipt_path)},
            }
            if args.apply:
                apply_uninstall(changes, receipt_path, receipt_raw)
        else:
            changes, receipt_raw, desired_receipt, receipt_path, receipt_action = install_plan(package, target, agent_home)
            plan = {
                "applied": args.apply,
                "changes": changes,
                "ownership_receipt": {"action": receipt_action, "destination": str(receipt_path)},
            }
            if args.apply:
                apply_install(package, changes, receipt_path, receipt_raw, desired_receipt)
        print(json.dumps(plan, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
