"""The run context handed to every check: two trees, the diff between them, and shared helpers."""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import effbase as effbase_mod
from . import ledger as ledger_mod
from . import manifest as manifest_mod
from . import proc as proc_mod
from .gitx import Change, Commit, Repo
from .tree import Tree

TOOL_ENV_KEYS = ('PATH', 'HOME', 'TMPDIR', 'USER', 'LANG', 'SYSTEMROOT', 'DEVELOPER_DIR', 'SDKROOT', 'CC',
                 'KNOT_GATE_TIMEOUT_SCALE', 'BEND_LIB')


def timeout_scale() -> float:
    try:
        return float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '4'))
    except ValueError:
        return 4.0


def tool_timeout_scale() -> float:
    """Hang guards for tools the suite runs scale with KNOT_GATE_TIMEOUT_SCALE, as every gate's do (default 1)."""
    try:
        return max(float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1')), 1.0)
    except ValueError:
        return 1.0


def tool_env(extra: dict | None = None) -> dict:
    """An allowlisted child environment: tool discovery only, no credentials, offline seed and Perch."""
    env = {k: os.environ[k] for k in TOOL_ENV_KEYS if k in os.environ}
    env.update(BEND_NO_TELEMETRY='1', BEND_HUB='offline://disabled', BEND_ORIGIN='offline://disabled',
               LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', npm_config_offline='true')
    if extra:
        env.update(extra)
    return env


@dataclass
class Context:
    repo: Repo
    head: Tree
    base: Tree | None
    head_commit: str | None            # the commit whose history is judged (HEAD, or --head)
    base_commit: str | None            # the effective base commit (None when there is no base)
    main_ref: str | None
    main_tree: Tree | None
    manifest: manifest_mod.Manifest
    ledger: ledger_mod.Ledger
    inc: str | None = None
    tier: str = 'fast'
    jobs: int = 4
    worktree: bool = False             # head is a snapshot of the working copy
    dirty: bool = False
    effective: effbase_mod.EffectiveBase | None = None
    scratch: Path = field(default_factory=lambda: Path('.local/prechecks'))
    options: dict = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    cancel: threading.Event = field(default_factory=threading.Event)   # a check's hang guard raises its own (runner.CheckContext)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _changes: list | None = None
    _commits: list | None = None
    started: float = field(default_factory=time.monotonic)

    # ---- diff between the trees ------------------------------------------
    def changes(self) -> list[Change]:
        with self._lock:
            if self._changes is None:
                if self.base is None:
                    self._changes = []
                else:
                    self._changes = self.repo.name_status(self.base.treeish, self.head.treeish)
            return self._changes

    def changed_paths(self, *, statuses: str = 'AMRCT') -> list[str]:
        return sorted({c.path for c in self.changes() if c.status in statuses})

    def deleted_paths(self) -> list[str]:
        return sorted({c.path for c in self.changes() if c.status == 'D'})

    def added_paths(self) -> list[str]:
        return sorted({c.path for c in self.changes() if c.status == 'A'})

    def modified_paths(self) -> list[str]:
        """Paths present in both trees whose bytes differ (renames count as a modification of the new path)."""
        return sorted({c.path for c in self.changes() if c.status in 'MTRC'})

    def commits(self) -> list[Commit]:
        """Commits in base..head (oldest first); empty in identity mode or without a base."""
        with self._lock:
            if self._commits is None:
                if self.base_commit is None or self.head_commit is None or self.base_commit == self.head_commit:
                    self._commits = []
                else:
                    self._commits = self.repo.commits(self.base_commit, self.head_commit)
            return self._commits

    @property
    def identity(self) -> bool:
        return self.base is None or self.base.treeish == self.head.treeish

    # ---- files on disk -----------------------------------------------------
    @property
    def root(self) -> Path:
        return self.repo.root

    def exports_dir(self) -> Path:
        directory = self.scratch / 'exports'
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def export(self, tree: Tree) -> Path:
        """A content-addressed export of `tree` (never contains `.env*`); shared by every check."""
        links = {}
        for name in ('.toolchain', 'node_modules'):
            target = self.root / name
            if target.exists():
                links[name] = target.resolve()
        with self._lock:
            return tree.export(self.exports_dir() / tree.treeish, links=links)

    def run(self, argv, *, cwd=None, timeout: float = 120, env: dict | None = None, input: bytes | None = None,
            cancel: threading.Event | None = None):
        """Run a tool with the allowlisted environment; returns (code, stdout, stderr) and never raises on timeout.
        The tool gets its own process group, which is killed on timeout or when `cancel` is raised (lib/proc.py)."""
        return proc_mod.run(argv, cwd=cwd, env=tool_env(env), input=input, timeout=timeout * tool_timeout_scale(),
                            cancel=cancel or self.cancel)

    def publish(self, key: str, value) -> None:
        with self._lock:
            self.facts[key] = value


def detect_main_ref(repo: Repo, explicit: str | None) -> str | None:
    for ref in ([explicit] if explicit else []) + ['main', 'origin/main', 'master']:
        if ref and repo.rev_parse(ref):
            return ref
    return None


def inc_from_branch(branch: str | None) -> str | None:
    if branch and branch.startswith('campaign/'):
        return branch.split('/', 1)[1] or None
    return None


def campaign_id(ref: str) -> str | None:
    """`campaign/<id>` inside a ref name (`refs/heads/campaign/x`, `origin/campaign/x`, `campaign/x`)."""
    parts = ref.split('/')
    if 'campaign' in parts and parts.index('campaign') + 1 < len(parts):
        return '/'.join(parts[parts.index('campaign') + 1:]) or None
    return None


def inc_for_head(repo: Repo, head: str, commit: str) -> str | None:
    """The increment a `--head` revision belongs to, from ref names alone: the argument itself when it names a
    campaign ref, else the one campaign ref whose tip is exactly that commit. The invoking checkout's branch is never
    consulted: the same commit must get the same verdict from every checkout."""
    named = campaign_id(head)
    if named:
        return named
    found = {campaign_id(ref) for ref in repo.refs_at(commit)} - {None}
    return found.pop() if len(found) == 1 else None


def build(repo: Repo, *, head: str | None = None, base: str | None = None, inc: str | None = None,
          main_ref: str | None = None, manifest_path: str | None = None, ledger_path: str | None = None,
          tier: str = 'fast', jobs: int = 4, upstream: list[str] | None = None, options: dict | None = None,
          scratch: Path | None = None) -> Context:
    explicit_none = inc == 'none'
    if inc == 'none':
        inc = None                          # an explicit "no increment" (a replay of main, or of a commit no campaign ref names)
    elif inc is None and not head:
        inc = inc_from_branch(repo.branch())
    main = detect_main_ref(repo, main_ref)
    main_commit = repo.rev_parse(main) if main else None
    if head:
        head_commit = repo.rev_parse(head)
        if head_commit is None:
            raise SystemExit(f'prechecks: unknown --head {head!r}')
        head_tree = Tree(repo, repo.tree_sha(head_commit), label=head_commit[:10])
        worktree, dirty = False, False
        if inc is None and not explicit_none:
            inc = inc_for_head(repo, head, head_commit)
    else:
        head_commit = repo.rev_parse('HEAD')
        dirty = repo.worktree_dirty()
        tree_sha = repo.snapshot_worktree() if dirty else (repo.tree_sha('HEAD') if head_commit else repo.snapshot_worktree())
        head_tree = Tree(repo, tree_sha, label='worktree' if dirty else (head_commit or 'worktree')[:10])
        worktree = dirty
    main_tree = Tree(repo, repo.tree_sha(main_commit), label=main) if main_commit else None
    # The manifest and ledger come from main when it has them: a branch cannot grant itself authority.
    manifest = manifest_mod.load(inc, main_tree, manifest_path)
    if manifest.source == 'defaults' and inc:
        manifest = manifest_mod.load(inc, head_tree, None)
        manifest.raw['authorized'] = []          # authority is never read from the branch
    if upstream:
        manifest.raw['upstream'] = [{'id': u.split('=')[0], 'ref': u.split('=', 1)[1] if '=' in u else f'campaign/{u}'}
                                    for u in upstream]
    effective = None
    if base:
        base_commit = repo.rev_parse(base)
        if base_commit is None:
            raise SystemExit(f'prechecks: unknown --base {base!r}')
        base_tree = Tree(repo, repo.tree_sha(base_commit), label=base_commit[:10])
    elif head_commit and main:
        effective = effbase_mod.compute(repo, head_commit, main, manifest.upstream)
        base_commit = effective.commit
        base_tree = Tree(repo, effective.treeish() and (repo.tree_sha(effective.treeish()) or effective.treeish()),
                         label=(base_commit or 'none')[:10]) if base_commit else None
    else:
        base_commit, base_tree = None, None
    ledger = ledger_mod.load(main_tree or base_tree, ledger_path)
    return Context(repo=repo, head=head_tree, base=base_tree, head_commit=head_commit, base_commit=base_commit,
                   main_ref=main, main_tree=main_tree, manifest=manifest, ledger=ledger, inc=inc, tier=tier, jobs=jobs,
                   worktree=worktree, dirty=dirty, effective=effective, scratch=scratch or (repo.root / '.local/prechecks'),
                   options=options or {})
