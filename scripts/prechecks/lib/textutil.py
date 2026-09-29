"""Text helpers for the prose checks: paragraphs with their headings, number-noun claims, backticked paths."""
from __future__ import annotations

import re
from dataclasses import dataclass

NUMBER_WORDS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen '
    'eighteen nineteen twenty'.split())}
NUMBER = r'(?:\d[\d,]*|' + '|'.join(w for w in NUMBER_WORDS if w != 'zero') + r')'
HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
SKIP_SECTIONS = re.compile(r'verification|baseline|history|review|measured at|changelog|decision record', re.I)
PATH_TOKEN = re.compile(r'`((?:vm|src|docs|tests|scripts|tools|research|packages|bench)/[A-Za-z0-9_./@+-]+)`')


@dataclass
class Paragraph:
    line: int          # 1-based first line
    text: str
    heading: str       # nearest heading text ('' before the first)


def to_int(token: str) -> int | None:
    token = token.lower().replace(',', '')
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token)


def paragraphs(text: str) -> list[Paragraph]:
    result, current, start, heading, in_fence = [], [], 0, '', False
    for number, line in enumerate(text.split('\n'), 1):
        if line.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if match:
            if current:
                result.append(Paragraph(start, '\n'.join(current), heading))
                current = []
            heading = match.group(2).strip()
            continue
        if not line.strip():
            if current:
                result.append(Paragraph(start, '\n'.join(current), heading))
                current = []
            continue
        if not current:
            start = number
        current.append(line)
    if current:
        result.append(Paragraph(start, '\n'.join(current), heading))
    return result


def claim_pairs(text: str, nouns: dict[str, str], *, gap: int = 2):
    """Yield (number, noun key, matched text) for `<number> [up to `gap` words] <noun>` without a clause break between."""
    alternation = '|'.join(sorted(nouns, key=len, reverse=True))
    pattern = re.compile(rf'\b({NUMBER})\s+((?:[A-Za-z][\w-]*\s+){{0,{gap}}}?)({alternation})\b', re.I)
    for match in pattern.finditer(text):
        number = to_int(match.group(1))
        if number is None:
            continue
        between = match.group(2)
        if re.search(r'[;:,]', match.group(0)):
            continue
        key = nouns[next(n for n in nouns if re.fullmatch(n, match.group(3), re.I))]
        yield number, key, match.group(0)


def added_lines(patch_hunks) -> list[str]:
    return [line for hunk in patch_hunks for line in hunk.added]
