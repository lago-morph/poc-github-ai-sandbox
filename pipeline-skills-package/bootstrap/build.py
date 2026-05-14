#!/usr/bin/env python3
"""Build the pipeline-skills-package bootstrap bundle.

Produces three artefacts under --output:

  install.md                          - the recipe (self-executing Markdown)
  pipeline-skills-package.tar.gz      - the tarball form
  MANIFEST.txt                        - sha256 sums of every bundled file

The recipe and tarball contain identical file trees. Source paths
inside pipeline-skills-package/ are mapped to their target paths in
the new repo per the bundle layout defined in bootstrap/install.md
section 2.

Usage:
  python build.py --source pipeline-skills-package/ \\
                  --output pipeline-skills-package/bootstrap/dist/
"""
from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import sys
import tarfile
from pathlib import Path
from typing import Iterable, Optional

SKILL_NAMES = (
    "batch-job",
    "task-dag",
    "orchestrate-issue",
    "onboarding",
    "composition-guide",
)


def load_excludes(source_root: Path) -> list[str]:
    path = source_root / "bootstrap" / "distribution-exclude.txt"
    if not path.exists():
        return []
    patterns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def _glob_match(rel_path: str, pattern: str) -> bool:
    if fnmatch.fnmatch(rel_path, pattern):
        return True
    if pattern.startswith("**/"):
        tail = pattern[3:]
        if fnmatch.fnmatch(rel_path, tail):
            return True
        parts = rel_path.split("/")
        for i in range(len(parts)):
            if fnmatch.fnmatch("/".join(parts[i:]), tail):
                return True
    return False


def is_excluded(rel_path: str, patterns: list[str]) -> bool:
    parts = rel_path.split("/")
    for pat in patterns:
        if pat.endswith("/"):
            prefix = pat.rstrip("/")
            if rel_path == prefix or rel_path.startswith(prefix + "/"):
                return True
            if any(p == prefix for p in parts):
                return True
            continue
        if _glob_match(rel_path, pat):
            return True
    return False


def map_to_bundle_path(rel: str) -> Optional[str]:
    """Map a source path (relative to pipeline-skills-package/) to its
    destination inside the bundle. Returns None for unrecognised paths,
    which the caller treats as "skip silently"."""
    parts = rel.split("/")
    head = parts[0]

    if head in {"OVERVIEW.md", "SPEC-PACKAGE.md"} and len(parts) == 1:
        return f"docs/{head}"
    if head in {"TESTING-IN-POC.md", "NEW-REPO-PLAN.md"} and len(parts) == 1:
        return head
    if head == "bootstrap" and len(parts) == 2 and parts[1] == "install.md":
        return "bootstrap/install.md"

    if head == "skills" and len(parts) >= 3:
        skill = parts[1]
        rest = "/".join(parts[2:])
        if skill not in SKILL_NAMES:
            return None
        if rest == "SPEC.md":
            return f"docs/skills/{skill}/SPEC.md"
        return f".claude/skills/{skill}/{rest}"

    if head == "test-harness" and len(parts) >= 2:
        rest = "/".join(parts[1:])
        if rest == "SPEC.md":
            return "docs/test-harness/SPEC.md"
        return f"test-harness/{rest}"

    return None


def walk_sources(source_root: Path, patterns: list[str]) -> Iterable[tuple[Path, str, str]]:
    for src in sorted(source_root.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(source_root).as_posix()
        if is_excluded(rel, patterns):
            continue
        bundle = map_to_bundle_path(rel)
        if bundle is None:
            continue
        yield src, rel, bundle


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _pick_fence(content: str) -> str:
    fence = "```"
    while fence in content:
        fence += "`"
    return fence


def build_recipe(entries, install_md_text: str) -> str:
    lines: list[str] = []
    lines.append("# Bootstrap recipe — pipeline-skills-package")
    lines.append("")
    lines.append("This file is a self-executing installation guide. An agent reads")
    lines.append("it top to bottom and creates each file at the path its")
    lines.append("`### <path>` header specifies, using the content from the fenced")
    lines.append("code block immediately below the header.")
    lines.append("")
    lines.append("Two forms exist for this bundle: this recipe Markdown (what you")
    lines.append("are reading) and `pipeline-skills-package.tar.gz`. They produce")
    lines.append("byte-identical file trees.")
    lines.append("")
    lines.append("## Section 1 — install instructions")
    lines.append("")
    lines.append("The instructions below come verbatim from `bootstrap/install.md`")
    lines.append("in this same bundle. Follow them.")
    lines.append("")
    lines.append(install_md_text.rstrip())
    lines.append("")
    lines.append("## Section 4 — bundled files (inlined)")
    lines.append("")
    lines.append("Each `### <path>` header below identifies a destination path in")
    lines.append("the repo root. The fenced code block beneath is the verbatim file")
    lines.append("contents. Create any missing parent directories, then write the")
    lines.append("file. Binary files appear in `base64` fences and must be decoded.")
    lines.append("")

    for src, _rel, bundle, _digest, _size in entries:
        lines.append(f"### {bundle}")
        lines.append("")
        try:
            content = src.read_text(encoding="utf-8")
            is_text = True
        except UnicodeDecodeError:
            content = src.read_bytes()
            is_text = False
        if is_text:
            fence = _pick_fence(content)
            lines.append(f"{fence}text")
            # split() keeps a trailing empty element when content ends in \n
            # so the parser can faithfully reconstruct the original bytes.
            lines.extend(content.split("\n"))
            lines.append(fence)
        else:
            encoded = base64.b64encode(content).decode("ascii")
            lines.append("```base64")
            lines.append(encoded)
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def build_tarball(entries, dest: Path) -> None:
    with tarfile.open(dest, "w:gz") as tar:
        for src, _rel, bundle, _digest, _size in entries:
            info = tar.gettarinfo(name=str(src), arcname=bundle)
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            with src.open("rb") as fh:
                tar.addfile(info, fh)


def build_manifest(entries) -> str:
    lines = [
        "# MANIFEST — pipeline-skills-package bundle",
        "# Format: <sha256>  <size_bytes>  <bundle_path>",
        "",
    ]
    for _src, _rel, bundle, digest, size in entries:
        lines.append(f"{digest}  {size:>10}  {bundle}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        print(f"error: --source not found: {source}", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)

    patterns = load_excludes(source)
    install_md_path = source / "bootstrap" / "install.md"
    if not install_md_path.exists():
        print(f"error: missing {install_md_path}", file=sys.stderr)
        return 2
    install_md_text = install_md_path.read_text(encoding="utf-8")

    walked = list(walk_sources(source, patterns))
    entries = []
    for src, rel, bundle in walked:
        digest = sha256_of(src)
        size = src.stat().st_size
        entries.append((src, rel, bundle, digest, size))

    manifest = build_manifest(entries)
    (output / "MANIFEST.txt").write_text(manifest, encoding="utf-8")

    recipe = build_recipe(entries, install_md_text)
    (output / "install.md").write_text(recipe, encoding="utf-8")

    build_tarball(entries, output / "pipeline-skills-package.tar.gz")

    total_bytes = sum(e[4] for e in entries)
    print(f"Built bundle: {len(entries)} files, {total_bytes} bytes total")
    print(f"  recipe  : {output / 'install.md'}")
    print(f"  tarball : {output / 'pipeline-skills-package.tar.gz'}")
    print(f"  manifest: {output / 'MANIFEST.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
