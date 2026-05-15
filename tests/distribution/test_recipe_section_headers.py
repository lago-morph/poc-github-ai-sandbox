"""test_recipe_section_headers — recipe install.md has well-formed top-level headers.

Guards against the duplicate-Section-N bug that earlier versions of
`build.py` produced: the build script used to wrap an inline copy of
`bootstrap/install.md` (which has its own `## Section N` headers)
with another `## Section 1 — install instructions` wrapper, and then
append a final `## Section 4 — bundled files (inlined)`. The result
had two Section 1s and two Section 4s.

We assert: among `^## ` headers that exist OUTSIDE of fenced code
blocks at the recipe's top level, no Section number appears more than
once. (Inlined files in Appendix A may contain their own section
headers; those are inside fences and don't count.)
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+Section\s+(\d+)\b", re.MULTILINE)


def _strip_fences(text: str) -> str:
    """Drop everything between matched fence-pairs.

    Fences are runs of >=3 backticks at the start of a line; a fence
    of length N closes only on a matching run of length N. This is the
    same algorithm `build.py:_pick_fence` follows when emitting blocks.
    """
    out_lines: list[str] = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("```"):
            # Determine fence length (run of backticks at start of stripped line).
            j = 0
            while j < len(stripped) and stripped[j] == "`":
                j += 1
            fence = "`" * j
            # Skip until a closing line with the same fence length (exact prefix).
            i += 1
            while i < n:
                close = lines[i].lstrip()
                if close.startswith(fence) and close[len(fence):len(fence)+1] in ("", " ", "\t"):
                    # Closing fence — but only if it doesn't open a longer fence.
                    j2 = 0
                    while j2 < len(close) and close[j2] == "`":
                        j2 += 1
                    if j2 == len(fence):
                        break
                i += 1
            i += 1
            continue
        out_lines.append(line)
        i += 1
    return "\n".join(out_lines)


def test_recipe_section_numbers_are_unique(recipe_path: Path):
    text = recipe_path.read_text(encoding="utf-8")
    outside_fences = _strip_fences(text)
    section_numbers = SECTION_RE.findall(outside_fences)
    counts = Counter(section_numbers)
    dupes = {n: c for n, c in counts.items() if c > 1}
    assert not dupes, (
        f"Recipe has duplicate Section headers at top level: {dupes}. "
        f"build.py is probably wrapping the embedded install.md with another "
        f"## Section header, or the source install.md has its own placeholder "
        f"Section that collides."
    )


def test_recipe_has_appendix_a(recipe_path: Path):
    """The actual file payload lives under Appendix A, never under Section N
    (which would collide with install.md's own numbered sections)."""
    text = recipe_path.read_text(encoding="utf-8")
    outside_fences = _strip_fences(text)
    assert re.search(r"^##\s+Appendix\s+A", outside_fences, re.MULTILINE), (
        "Recipe is missing the `## Appendix A — bundled files (inlined)` header"
    )
