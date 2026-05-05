"""Shared helpers for the ``batch-job`` skill scripts.

Re-exports the central :mod:`.agent.scripts.common` symbols by
ensuring the repo root is on ``sys.path`` first, then loading the
module by file path. This keeps the skill scripts runnable both as
package-style imports and as standalone CLI scripts.
"""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _locate_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".agent" / "config.json").exists():
            return parent
    raise RuntimeError("could not locate repo root (no .agent/config.json found)")


REPO_ROOT = _locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_common():
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    path = REPO_ROOT / ".agent" / "scripts" / "common.py"
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = module_from_spec(spec)
    sys.modules[name] = mod  # register before exec so dataclass works
    spec.loader.exec_module(mod)
    return mod


_common = _load_common()

GitHubClient = _common.GitHubClient
InMemoryGitHubClient = _common.InMemoryGitHubClient
iso_now = _common.iso_now
load_config = _common.load_config
load_schema = _common.load_schema
validate = _common.validate
parse_agent_meta = _common.parse_agent_meta
b64_encode = _common.b64_encode
b64_decode = _common.b64_decode
new_uuid = _common.new_uuid
is_terminal_run_status = _common.is_terminal_run_status
has_protocol_markers = _common.has_protocol_markers


def repo_root() -> Path:
    return REPO_ROOT


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "iso_now",
    "load_config",
    "load_schema",
    "validate",
    "parse_agent_meta",
    "b64_encode",
    "b64_decode",
    "new_uuid",
    "is_terminal_run_status",
    "has_protocol_markers",
    "repo_root",
]
