"""Self-contained Markdown packets for the advisory Perch rules (`.perch/rules/prechecks.yaml`).

A packet quotes text; it never refers to the working tree, so a packet built from any commit can be
checked from any checkout. Builders read only git objects (never the working copy) and emit nothing
host-specific, so rebuilding is byte-identical. Every evidence block is capped, hashed and marked when
truncated; a packet whose evidence cannot be resolved is reported `unavailable`, never sent.
"""
from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

VERSION = 1
PACKET_LIMIT = 48 * 1024
EVIDENCE_LIMIT = 12 * 1024
PER_RULE_LIMIT = 40
HERE = Path(__file__).resolve().parent
CODE_SUFFIXES = ('*.py', '*.mjs', '*.ts', '*.js', '*.bend')


@dataclass
class Source:
    path: str
    rev: str
    sha256: str


@dataclass
class Packet:
    rule: str
    key: str                       # stable subject key: orders and de-duplicates packets
    claim: str
    evidence: str
    sources: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


@dataclass
class Unavailable:
    rule: str
    key: str
    reason: str


def builder_id() -> str:
    """Identity of the builder code: changes when any packet module changes, never with a checkout path."""
    digest = hashlib.sha256()
    for path in sorted(HERE.glob('*.py')):
        digest.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()[:12]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def cap(text: str, limit: int = EVIDENCE_LIMIT) -> tuple[str, str]:
    """(text within `limit` bytes, truncation marker or '')."""
    data = text.encode('utf-8')
    if len(data) <= limit:
        return text, ''
    kept = data[:limit].decode('utf-8', 'ignore')
    return kept, f'[truncated after {limit:,} bytes; {len(data) - len(kept.encode("utf-8")):,} bytes omitted]'


def fence(text: str, lang: str = '') -> str:
    ticks = '```'
    while ticks in text:
        ticks += '`'
    return f'{ticks}{lang}\n{text.rstrip(chr(10))}\n{ticks}'


def render(packet: Packet, *, inc: str | None, head: str | None, base: str | None) -> str:
    sources = '; '.join(f'{s.path}@{s.rev[:8]} sha256={s.sha256}' for s in sorted(packet.sources, key=lambda s: (s.path, s.rev)))
    header = (f'<!-- prechecks packet v{VERSION}; rule={packet.rule}; increment={inc or "none"}; head={(head or "none")[:12]}; '
              f'base={(base or "none")[:12]}; builder=scripts/prechecks/packets@{builder_id()}; sources: {sources or "none"} -->')
    return '\n'.join([header, '# Claim', packet.claim.rstrip('\n'), '', '# Evidence', packet.evidence.rstrip('\n'), '',
                      '# Scope',
                      'Only the text above is evidence. Anything not shown is missing evidence, not a pass.', ''])


# ---- Markdown structure -------------------------------------------------------------
HEADING = re.compile(r'^(#{1,6})\s+(.*\S)\s*$')


def sections(text: str) -> list[tuple[int, int, str]]:
    """(line, level, heading) for every ATX heading outside a code fence."""
    out, fenced = [], False
    for number, line in enumerate(text.split('\n'), 1):
        if line.strip().startswith('```'):
            fenced = not fenced
        elif not fenced:
            match = HEADING.match(line)
            if match:
                out.append((number, len(match.group(1)), match.group(2)))
    return out


def section_at(text: str, line: int) -> str:
    current = ''
    for number, _level, heading in sections(text):
        if number > line:
            break
        current = heading
    return current


def paragraph_at(text: str, line: int) -> tuple[int, int, str]:
    """(first line, last line, text) of the blank-line-delimited block containing `line` (1-based)."""
    lines = text.split('\n')
    start = min(max(line, 1), len(lines)) - 1
    while start > 0 and lines[start - 1].strip():
        start -= 1
    end = min(max(line, 1), len(lines)) - 1
    while end + 1 < len(lines) and lines[end + 1].strip():
        end += 1
    return start + 1, end + 1, '\n'.join(lines[start:end + 1])


BULLET = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+')


def unit_at(text: str, line: int) -> tuple[int, int, str, str]:
    """(first, last, text, lead) of the claim unit holding `line`: a list item with its continuation lines, else the
    sentence of the paragraph that covers the line. `lead` is the item's paragraph lead-in (empty for a sentence)."""
    lines = text.split('\n')
    i = min(max(line, 1), len(lines)) - 1
    start = i
    while start > 0 and lines[start].strip() and not BULLET.match(lines[start]) and lines[start][:1] in ' \t':
        start -= 1
    if BULLET.match(lines[start]):
        end = start
        while end + 1 < len(lines) and lines[end + 1].strip() and not BULLET.match(lines[end + 1]) and lines[end + 1][:1] in ' \t':
            end += 1
        first, _last, _p = paragraph_at(text, start + 1)
        lead = lines[first - 1].strip() if first - 1 < start else ''
        return start + 1, end + 1, '\n'.join(lines[start:end + 1]), lead
    first, last, paragraph = paragraph_at(text, line)
    begin = sum(len(l) + 1 for l in lines[first - 1:i])
    finish = begin + len(lines[i])
    # Pieces: a list item starts a piece of its own; prose between items is split into sentences.
    pieces, position, current = [], 0, []
    for raw in paragraph.split('\n'):
        if BULLET.match(raw) and current:
            pieces.append((current[0], position - 1))
            current = []
        if not current:
            current = [position]
        position += len(raw) + 1
    if current:
        pieces.append((current[0], len(paragraph)))
    spans = []
    for lo, hi in pieces:
        chunk = paragraph[lo:hi]
        cursor = 0
        for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z`(\[|])', chunk):
            found = chunk.find(sentence, cursor)
            found = cursor if found < 0 else found
            cursor = found + len(sentence)
            span = (lo + found, lo + cursor)
            if span[0] < finish and span[1] > begin:
                spans.append(span)
    if not spans:
        return first, last, paragraph, ''
    lo, hi = spans[0][0], spans[-1][1]
    before = paragraph[:lo].count('\n')
    return first + before, first + paragraph[:hi].count('\n'), paragraph[lo:hi], ''


def sentences_of(paragraph: str) -> list[str]:
    flat = re.sub(r'\s+', ' ', paragraph).strip()
    return [s for s in re.split(r'(?<=[.!?])\s+(?=[A-Z`(\[|])', flat) if s]


# ---- code blocks ----------------------------------------------------------------------
def python_block(source: str, line: int) -> tuple[int, int, str] | None:
    try:
        module = ast.parse(source)
    except SyntaxError:
        return None
    best = None
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            if start <= line <= node.end_lineno and (best is None or start >= best[0]):
                best = (start, node.end_lineno)
    if best is None:
        return None
    lines = source.split('\n')
    return best[0], best[1], '\n'.join(lines[best[0] - 1:best[1]])


TOP = re.compile(r'^(?:def|law|type|import|export|function|async function|class)\b|^(?:const|let|var)\s+\w+\s*=')


def block_at(path: str, source: str, line: int) -> tuple[int, int, str]:
    """The enclosing declaration: a Python def by ast, a top-level Bend/JS block by indentation, else +-20 lines."""
    if path.endswith('.py'):
        found = python_block(source, line)
        if found:
            return found
    lines = source.split('\n')
    if path.endswith(('.bend', '.mjs', '.js', '.ts')):
        start = min(line, len(lines)) - 1
        while start > 0 and not TOP.match(lines[start]):
            start -= 1
        end = start + 1
        while end < len(lines) and not TOP.match(lines[end]):
            end += 1
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        return start + 1, end, '\n'.join(lines[start:end])
    lo, hi = max(line - 20, 1), min(line + 20, len(lines))
    return lo, hi, '\n'.join(lines[lo - 1:hi])


def numbered(text: str, first: int) -> str:
    return '\n'.join(f'{first + i:>5}  {line}' for i, line in enumerate(text.split('\n')))
