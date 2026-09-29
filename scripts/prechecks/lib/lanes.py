"""Knot's own CLIs as lanes: parse-cli, check-cli and eval-cli built from a tree with the pinned seed's JS lane.

A build takes 0.15-0.5 s and a run about 0.03 s. Builds are cached by tree, and every run happens in a scratch
directory of programs, so a `.env` file can never be in the working directory of a tool that loads one.
"""
from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .context import tool_env

CLIS = {'parse': 'src/parse-cli.bend', 'check': 'src/check-cli.bend', 'eval': 'src/eval-cli.bend'}
EXIT_CLASS = {0: 'Checked', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure'}
DIAGNOSTIC = re.compile(r'^(Invalid|Unsupported|Exhausted|HostFailure|InternalFailure)\t([a-z]+)\t([a-z0-9-]+)\t(\d+):(\d+):(\d+):(\d+)$')
SHAPE = re.compile(r'^(Invalid|Unsupported|Exhausted|HostFailure|InternalFailure)\t[a-z]+\t[a-z0-9-]+\t\d+:\d+:\d+:\d+$')


@dataclass(frozen=True)
class Outcome:
    exit: int | None
    kind: str                # Checked | Invalid | Unsupported | Exhausted | HostFailure | InternalFailure | crash | timeout
    line: str                # the first diagnostic line (stderr), '' when none
    begin: int | None        # span start offset of an Invalid/Unsupported diagnostic
    stdout: str = ''

    @property
    def accepted(self) -> bool:
        return self.kind == 'Checked'

    def to_json(self) -> list:
        return [self.exit, self.kind, self.line, self.begin, self.stdout]

    @classmethod
    def from_json(cls, row) -> 'Outcome':
        return cls(row[0], row[1], row[2], row[3], row[4])


def classify(exit_code, stdout: str, stderr: str) -> Outcome:
    if exit_code is None:
        return Outcome(None, 'timeout', '', None)
    line = next((l for l in stderr.split('\n') if l.strip()), '')
    match = DIAGNOSTIC.match(line)
    begin = int(match.group(4)) if match else None
    kind = EXIT_CLASS.get(exit_code, 'crash')
    if kind != 'Checked' and match and match.group(1) != kind:
        kind = 'crash'                                   # the exit code and the diagnostic class disagree
    return Outcome(exit_code, kind, line, begin, stdout if exit_code == 0 else '')


class Lanes:
    """The three CLIs of one tree, built lazily into `cache` and run on programs in `programs`."""

    def __init__(self, ctx, tree, label: str, programs: Path):
        self.ctx, self.tree, self.label = ctx, tree, label
        self.cache = ctx.scratch / 'cache' / 'lanes' / tree.treeish
        self.programs = programs
        self.built: dict[str, Path | None] = {}
        self.errors: dict[str, str] = {}

    def build(self, names=('parse', 'check', 'eval')) -> dict:
        seed = self.ctx.root / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
        self.cache.mkdir(parents=True, exist_ok=True)
        source = self.cache / 'source'
        if not source.exists():
            self.tree.export(source, only=['src'])

        def one(name):
            out = self.cache / f'{name}.js'
            if out.is_file() and out.stat().st_size:
                return name, out, ''
            entry = source / CLIS[name]
            if not entry.is_file():
                return name, None, f'{CLIS[name]} does not exist in {self.label}'
            proc = subprocess.run(['bun', str(seed.resolve()), str(entry), '-o', str(out)], cwd=source, env=tool_env(),
                                  capture_output=True, timeout=240)
            if proc.returncode != 0 or not out.is_file():
                return name, None, proc.stderr.decode('utf-8', 'replace').strip().splitlines()[-1][:160] if proc.stderr.strip() else 'build failed'
            return name, out, ''

        with ThreadPoolExecutor(max_workers=3) as pool:
            for name, path, error in pool.map(one, [n for n in names if n not in self.built]):
                self.built[name] = path
                if error:
                    self.errors[name] = error
        return self.built

    def run(self, lane: str, program: Path, *args: str, timeout: float = 60) -> Outcome:
        binary = self.built.get(lane)
        if binary is None:
            return Outcome(None, 'timeout', 'lane unavailable', None)
        try:
            proc = subprocess.run(['bun', str(binary), str(program), *args], cwd=self.programs, env=tool_env(),
                                  capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return Outcome(None, 'timeout', '', None)
        return classify(proc.returncode, proc.stdout.decode('utf-8', 'replace'), proc.stderr.decode('utf-8', 'replace'))
