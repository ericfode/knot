"""The implementer's own gate run: the newest `.local/gates/run-*/summary.json` whose snapshot equals this tree."""
from __future__ import annotations

import glob
import json
from pathlib import Path

RUNNER_TOP_EXCLUDED = ('.toolchain', 'node_modules', '.local', 'build')


def runner_excluded(name: str) -> bool:
    """The runner's own export exclusions (run.py `excluded`): dotenv files, .git, and four top-level directories."""
    parts = name.split('/')
    return (any(p.lower() == '.env' or p.lower().startswith('.env.') or p == '.git' for p in parts)
            or parts[0] in RUNNER_TOP_EXCLUDED)


def find(ctx, limit: int = 6) -> tuple[dict | None, str | None, str]:
    """(summary, path, reason). A summary matches when its recorded snapshot has exactly this tree's files and hashes."""
    root = ctx.root / '.local/gates'
    summaries = sorted(glob.glob(str(root / 'run-*/summary.json')), key=lambda p: Path(p).stat().st_mtime, reverse=True)
    if not summaries:
        return None, None, 'no .local/gates/run-*/summary.json (run `npm run -s gates` first)'
    wanted = {n: ctx.head.sha256(n) for n in ctx.head.files() if not runner_excluded(n)}
    note = ''
    for index, path in enumerate(summaries[:limit]):
        snap_path = Path(path).with_name('snapshot.json')
        if not snap_path.is_file():
            continue
        try:
            snapshot = json.loads(snap_path.read_text())
        except ValueError:
            continue
        have = {n: (v or {}).get('sha256') for n, v in snapshot.items() if isinstance(v, dict) and 'sha256' in v}
        links = {n for n, v in snapshot.items() if isinstance(v, dict) and 'link' in v}
        have_names = {n for n in have if n not in links}
        if have_names == set(wanted) and all(have[n] == wanted[n] for n in wanted):
            return json.loads(Path(path).read_text()), path, ''
        if index == 0:
            differing = sorted({n for n in set(have) | set(wanted) if have.get(n) != wanted.get(n)})
            note = f'newest gate run predates this tree ({len(differing)} file(s) differ, e.g. {differing[:3]})'
    return None, None, note or 'no gate run matches this tree'
