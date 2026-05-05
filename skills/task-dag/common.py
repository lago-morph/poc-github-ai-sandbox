"""Shared helpers for the ``task-dag`` skill.

Loads the central :mod:`.agent.scripts.common` and re-exports the
symbols the skill scripts need.
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
    raise RuntimeError("could not locate repo root")


REPO_ROOT = _locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_common():
    name = "agent_protocol_common"
    if name in sys.modules:
        return sys.modules[name]
    spec = spec_from_file_location(
        name,
        REPO_ROOT / ".agent" / "scripts" / "common.py",
    )
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
parse_agent_meta = _common.parse_agent_meta
render_agent_meta = _common.render_agent_meta
new_uuid = _common.new_uuid
slugify = _common.slugify
is_terminal_run_status = _common.is_terminal_run_status


def repo_root() -> Path:
    return REPO_ROOT


__all__ = [
    "GitHubClient",
    "InMemoryGitHubClient",
    "iso_now",
    "load_config",
    "parse_agent_meta",
    "render_agent_meta",
    "new_uuid",
    "slugify",
    "is_terminal_run_status",
    "repo_root",
]
