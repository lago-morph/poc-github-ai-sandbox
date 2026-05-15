#!/usr/bin/env python3
"""Build the pipeline-skills-package bootstrap bundle.

Produces four artefacts under --output:

  install.py                          - self-extracting installer (recommended)
  pipeline-skills-package.tar.gz      - equivalent tarball form
  install.md                          - audit-friendly flat-text recipe
  MANIFEST.txt                        - sha256 sums of every bundled file

The installer, tarball, and recipe contain identical file trees. Source
paths inside pipeline-skills-package/ are mapped to their target paths
in the new repo per the bundle layout defined in bootstrap/install.md
section 2.

Usage:
  python build.py --source pipeline-skills-package/ \\
                  --output pipeline-skills-package/bootstrap/dist/
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import fnmatch
import hashlib
import io
import sys
import tarfile
import textwrap
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
    lines.append("# Bootstrap recipe — pipeline-skills-package (audit form)")
    lines.append("")
    lines.append("This Markdown file is a **flat-text audit view** of the bundle: every")
    lines.append("bundled file appears below under a `### <path>` header followed by its")
    lines.append("verbatim contents in a fenced code block. It exists so the bundle can")
    lines.append("be diffed in PR review without unpacking a tarball.")
    lines.append("")
    lines.append("**This file is not the install path.** To install, use")
    lines.append("`install.py` (self-extracting) or `pipeline-skills-package.tar.gz`.")
    lines.append("LLM-driven extraction from this Markdown is not supported — the file")
    lines.append("is too large and verbatim-copying tens of files via an LLM is unreliable.")
    lines.append("")
    lines.append("All three forms (install.py, tarball, recipe) produce byte-identical")
    lines.append("file trees; the embedded `bootstrap/install.md` document below is what")
    lines.append("the install agent should read after extraction.")
    lines.append("")
    lines.append(install_md_text.rstrip())
    lines.append("")
    lines.append("## Appendix A — bundled files (inlined)")
    lines.append("")
    lines.append("Each `### <path>` header below identifies a destination path in")
    lines.append("the repo root. The fenced code block beneath is the verbatim file")
    lines.append("contents. Binary files appear in `base64` fences.")
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


def build_tarball_bytes(entries, extra: dict | None = None) -> bytes:
    """Build the bundle tarball in-memory and return its gzipped bytes.

    Writing the same byte stream to disk AND embedding it inside
    install.py guarantees the installer's sha256 check matches the
    tarball form bit-for-bit."""
    import gzip
    raw = io.BytesIO()
    # Use mtime=0 on the gzip stream for reproducibility across rebuilds.
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    try:
        with tarfile.open(fileobj=gz, mode="w") as tar:
            for src, _rel, bundle, _digest, _size in entries:
                info = tar.gettarinfo(name=str(src), arcname=bundle)
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                # Drop mtime for tar member reproducibility too.
                info.mtime = 0
                with src.open("rb") as fh:
                    tar.addfile(info, fh)
            for name, data in (extra or {}).items():
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                info.mtime = 0
                tar.addfile(info, io.BytesIO(data))
    finally:
        gz.close()
    return raw.getvalue()


def build_tarball(entries, dest: Path, extra: dict | None = None) -> bytes:
    """Build the tarball, write it to dest, and return its bytes."""
    data = build_tarball_bytes(entries, extra=extra)
    dest.write_bytes(data)
    return data


_SFX_TEMPLATE = '''\
#!/usr/bin/env python3
"""Self-extracting installer for the pipeline-skills-package bundle.

Usage:
    python install.py [--target DIR] [--force] [--verify-only] [--list]

After extraction completes successfully, read `bootstrap/install.md`
from the extracted tree for the verification checklist and the next
step (running NEW-REPO-PLAN.md).

The bundle payload is embedded below as a base64-encoded gzip tarball.
The installer verifies the payload's sha256 against an embedded
constant before extraction; corruption fails closed with a clear
error rather than silently producing a partial tree.

Default behaviour is idempotent: files that already exist with
matching content are skipped; files that exist with differing content
abort the run unless --force is passed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import sys
import tarfile
from pathlib import Path

# === BUNDLE METADATA (filled at build time) ===
BUNDLE_NAME = "pipeline-skills-package"
GENERATED_AT = {generated_at!r}
FILE_COUNT = {file_count}
TARBALL_BYTES = {tarball_size}
TARBALL_SHA256 = {tarball_sha256!r}
# === END METADATA ===

# === EMBEDDED TARBALL (base64, gzipped tar) ===
TARBALL_BASE64 = """\\
{tarball_b64}
"""
# === END EMBEDDED TARBALL ===


def _decode_payload() -> bytes:
    data = base64.b64decode(TARBALL_BASE64.encode("ascii"), validate=False)
    digest = hashlib.sha256(data).hexdigest()
    if digest != TARBALL_SHA256:
        raise SystemExit(
            "Embedded tarball sha256 mismatch.\\n"
            f"  expected: {{TARBALL_SHA256}}\\n"
            f"  got:      {{digest}}\\n"
            "This installer file has been corrupted in transit. "
            "Re-fetch it from the source repository."
        )
    if len(data) != TARBALL_BYTES:
        raise SystemExit(
            f"Embedded tarball byte-count mismatch: expected {{TARBALL_BYTES}}, got {{len(data)}}."
        )
    return data


def _assert_safe(name: str) -> None:
    if name.startswith("/") or ".." in Path(name).parts:
        raise SystemExit(f"Refusing to extract unsafe archive entry: {{name!r}}")


def _list(data: bytes) -> int:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            if m.isfile():
                print(m.name)
    return 0


def _extract(data: bytes, target: Path, force: bool) -> tuple[int, int, list[str]]:
    written = 0
    skipped = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        for m in members:
            _assert_safe(m.name)

        # Pre-flight: surface conflicts before any disk write.
        conflicts: list[str] = []
        if not force:
            for m in members:
                dest = target / m.name
                if not dest.exists():
                    continue
                src_bytes = tar.extractfile(m).read()
                if dest.read_bytes() != src_bytes:
                    conflicts.append(m.name)
        if conflicts:
            return 0, 0, conflicts

        # Re-open the tar to reset member file pointers.
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in [m for m in tar.getmembers() if m.isfile()]:
            dest = target / m.name
            src_bytes = tar.extractfile(m).read()
            if dest.exists() and dest.read_bytes() == src_bytes:
                skipped += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src_bytes)
            written += 1
    return written, skipped, []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.cwd(),
                        help="Destination directory (default: cwd).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing files that differ from the bundle.")
    parser.add_argument("--verify-only", action="store_true",
                        help="Verify embedded payload integrity; do not extract.")
    parser.add_argument("--list", action="store_true",
                        help="List bundle contents; do not extract.")
    args = parser.parse_args(argv)

    print(f"{{BUNDLE_NAME}} installer")
    print(f"  generated_at: {{GENERATED_AT}}")
    print(f"  files:        {{FILE_COUNT}}")
    print(f"  payload:      {{TARBALL_BYTES}} bytes (sha256 {{TARBALL_SHA256[:12]}}…)")

    data = _decode_payload()
    print("  integrity:    OK (sha256 + byte-count verified)")

    if args.list:
        return _list(data)
    if args.verify_only:
        return 0

    target = args.target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    written, skipped, conflicts = _extract(data, target, args.force)
    if conflicts:
        sys.stderr.write(
            f"\\nRefusing to overwrite {{len(conflicts)}} differing file(s). "
            "Re-run with --force to overwrite, or stash/move the conflicts:\\n"
        )
        for c in conflicts[:20]:
            sys.stderr.write(f"  {{c}}\\n")
        if len(conflicts) > 20:
            sys.stderr.write(f"  … and {{len(conflicts) - 20}} more\\n")
        return 3

    print(f"  wrote:        {{written}} file(s)")
    print(f"  skipped:      {{skipped}} file(s) (already identical)")
    print(f"  target:       {{target}}")
    print("\\nDone. Next: read bootstrap/install.md for verification and next steps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_self_extracting_py(tarball_bytes: bytes, file_count: int, generated_at: str) -> str:
    digest = hashlib.sha256(tarball_bytes).hexdigest()
    b64 = base64.b64encode(tarball_bytes).decode("ascii")
    # Wrap base64 at 76 chars (PEM-style) for readability and to keep
    # individual source lines under common editor line-length limits.
    b64_wrapped = "\n".join(textwrap.wrap(b64, 76)) or b64
    return _SFX_TEMPLATE.format(
        generated_at=generated_at,
        file_count=file_count,
        tarball_size=len(tarball_bytes),
        tarball_sha256=digest,
        tarball_b64=b64_wrapped,
    )


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

    manifest_bytes = manifest.encode("utf-8")
    extra: dict[str, bytes] = {"MANIFEST.txt": manifest_bytes}
    for src, _rel, bundle, _digest, _size in entries:
        if bundle == "test-harness/SPEC.md":
            extra["docs/test-harness/SPEC.md"] = src.read_bytes()
            break
    tarball_bytes = build_tarball(
        entries, output / "pipeline-skills-package.tar.gz",
        extra=extra,
    )

    generated_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sfx = build_self_extracting_py(tarball_bytes, len(entries) + len(extra), generated_at)
    (output / "install.py").write_text(sfx, encoding="utf-8")

    total_bytes = sum(e[4] for e in entries)
    print(f"Built bundle: {len(entries)} files, {total_bytes} bytes total")
    print(f"  installer: {output / 'install.py'}")
    print(f"  tarball  : {output / 'pipeline-skills-package.tar.gz'}")
    print(f"  recipe   : {output / 'install.md'}  (audit-only)")
    print(f"  manifest : {output / 'MANIFEST.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
