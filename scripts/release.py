"""Cut or open a JsonIBase release.

Usage:

    python scripts/release.py 0.1.0
    python scripts/release.py 0.1.0 --dry
    python scripts/release.py --post-release 0.2.0.dev0

The release command requires a clean tree, updates CHANGELOG.md by renaming the
`[Unreleased]` section, commits the version/changelog change, and tags the same
commit as `vX.Y.Z`. Push the branch and tag to trigger `.github/workflows/publish.yml`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "src" / "jsonibase" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r'__version__ = "([^"]+)"')
UNRELEASED_HEADER = re.compile(r"^## \[Unreleased\]\s*$", re.MULTILINE)
RELEASE_VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:[a-z0-9.]+)?")
DEV_VERSION_RE = re.compile(r"\d+\.\d+\.\d+\.dev\d+")


def _current_version() -> str:
    match = VERSION_RE.search(INIT.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("Could not find __version__ in src/jsonibase/__init__.py")
    return match.group(1)


def _set_version(new: str) -> None:
    text = INIT.read_text(encoding="utf-8")
    text = VERSION_RE.sub(f'__version__ = "{new}"', text, count=1)
    INIT.write_text(text, encoding="utf-8")


def _rename_unreleased(version: str, today: str) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    if not UNRELEASED_HEADER.search(text):
        raise SystemExit("No `## [Unreleased]` section in CHANGELOG.md")
    text = UNRELEASED_HEADER.sub(f"## [{version}] - {today}", text, count=1)
    CHANGELOG.write_text(text, encoding="utf-8")


def _add_unreleased() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    if UNRELEASED_HEADER.search(text):
        return
    parts = text.split("\n", 2)
    if len(parts) < 3:
        raise SystemExit("CHANGELOG.md has unexpected layout")
    head = parts[0] + "\n" + parts[1] + "\n"
    CHANGELOG.write_text(head + "\n## [Unreleased]\n\n" + parts[2], encoding="utf-8")


def _git(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=capture,
        text=True,
    )
    return result.stdout.strip() if capture else ""


def _require_clean_tree() -> None:
    dirty = _git("status", "--porcelain", capture=True)
    if dirty:
        raise SystemExit("Working tree not clean:\n" + dirty)


def cut(version: str, dry: bool) -> int:
    if not RELEASE_VERSION_RE.fullmatch(version):
        raise SystemExit(f"Refusing non-release version: {version!r}")

    current = _current_version()
    if current != version and not current.endswith(".dev0") and not dry:
        raise SystemExit(
            f"Current version is {current!r}; expected {version!r} or an "
            "in-progress `.dev0` suffix."
        )

    today = dt.date.today().isoformat()
    if dry:
        print(f"would set version {current} -> {version}")
        print(f"would rename `## [Unreleased]` -> `## [{version}] - {today}`")
        print(f"would commit + tag v{version}")
        return 0

    _require_clean_tree()
    _set_version(version)
    _rename_unreleased(version, today)
    _git("add", str(INIT.relative_to(ROOT)), str(CHANGELOG.relative_to(ROOT)))
    _git("commit", "-m", f"Release {version}")
    _git("tag", "-a", f"v{version}", "-m", f"jsonibase {version}")
    print(f"cut v{version}. Push with:")
    print(f"  git push origin master v{version}")
    return 0


def post_release(dev_version: str, dry: bool) -> int:
    if not DEV_VERSION_RE.fullmatch(dev_version):
        raise SystemExit(f"Expected a dev version like `0.2.0.dev0`, got {dev_version!r}")
    if dry:
        print(f"would bump to {dev_version} and re-open `## [Unreleased]`")
        return 0

    _require_clean_tree()
    _set_version(dev_version)
    _add_unreleased()
    _git("add", str(INIT.relative_to(ROOT)), str(CHANGELOG.relative_to(ROOT)))
    _git("commit", "-m", f"Open {dev_version} dev cycle")
    print(f"bumped to {dev_version}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("version", help="Release version or next dev version")
    parser.add_argument("--dry", action="store_true", help="Show changes without writing")
    parser.add_argument(
        "--post-release",
        action="store_true",
        help="Bump to the given .devN and re-open [Unreleased]",
    )
    args = parser.parse_args(argv)
    if args.post_release:
        return post_release(args.version, args.dry)
    return cut(args.version, args.dry)


if __name__ == "__main__":
    sys.exit(main())
