#!/usr/bin/env python3
"""Link the Codex skills and agents into an explicitly selected scope."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


def installation_links(package: Path, scope: Path, agent_home: Path) -> list[tuple[Path, Path]]:
    skills = sorted(path for path in (package / "skills").iterdir() if (path / "SKILL.md").is_file())
    agents = sorted((package / "agents").glob("*.toml"))
    if not skills or not agents:
        raise ValueError("The package needs generated skills and agent files. Run convert.py first.")
    return [
        *((source, scope / ".agents" / "skills" / source.name) for source in skills),
        *((source, agent_home / "agents" / source.name) for source in agents),
    ]


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
            if source.parent == source_dir and source.name == destination.name:
                links.append((source, destination))
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--project", type=Path, help="Install in this project only")
    scope.add_argument("--user", action="store_true", help="Install for the current user")
    parser.add_argument("--apply", action="store_true", help="Apply the previewed changes")
    parser.add_argument("--uninstall", action="store_true", help="Remove only links to this package")
    args = parser.parse_args()
    package = Path(__file__).resolve().parent.parent
    target = (args.project if args.project is not None else Path.home()).expanduser().resolve()
    agent_home = (
        Path(os.environ.get("CODEX_HOME", str(target / ".codex"))).expanduser().resolve()
        if args.user else target / ".codex"
    )
    try:
        links = (
            removal_links(package, target, agent_home) if args.uninstall
            else installation_links(package, target, agent_home)
        )
        if not args.uninstall:
            conflicts = [
                str(destination) for source, destination in links
                if (destination.exists() or destination.is_symlink()) and not owned_link(source, destination)
            ]
            if conflicts:
                raise ValueError("Conflicting paths. Nothing changed: " + ", ".join(conflicts))
        changes = []
        for source, destination in links:
            action = "remove" if args.uninstall else "keep" if owned_link(source, destination) else "link"
            changes.append({"action": action, "source": str(source), "destination": str(destination)})
        if args.apply:
            created = []
            try:
                for change, (source, destination) in zip(changes, links):
                    if change["action"] == "remove":
                        if owned_link(source, destination):
                            destination.unlink()
                    elif change["action"] == "link":
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.symlink_to(source, target_is_directory=source.is_dir())
                        created.append((source, destination))
            except OSError:
                for source, destination in reversed(created):
                    if owned_link(source, destination):
                        destination.unlink()
                raise
        print(json.dumps({"applied": args.apply, "changes": changes}, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
