#!/usr/bin/env python3
"""Gate `image`: src/image.bend encodes a checked book to knot-image-1 bytes, and decodes them.

Every claim is checked against a lane that does not share Bend code with the encoder:
  * the reference (reference.py): the declarations read from source text, the core that main's own
    `check-cli` displays, and vm/serializer.py's layout. Its bytes for the books `check-cli` accepts were frozen in
    expectations.json before src/image.bend existed (commit 1aca8df3); five witness books, the profile's emitter depth
    and, in review round 1, the nine golden sources of vm-spec round 14 were added after (see REPORT.md). This gate
    recomputes the reference and requires every frozen image unchanged;
  * vm/serializer.py: `decode`, `validate` and canonical re-encoding of every image the compiler writes;
  * vm/evaluate.py: the golden sources' frozen expectations, run on the compiler's own images;
  * `image-cli`, whose decoder is checked against serializer.decode's plan (rendered by render.py) and
    whose re-encoding must reproduce every committed golden image byte for byte.
A source that `check-cli` refuses is not judged against a snapshot: the image profile must answer exactly as a
`check-cli` built from the same tree in the same run, so no merge that adds a fixture, or closes a D4 gap, moves an
expectation. The source list is explicit (expectations.json); seed-audit.json records which Invalid verdicts the
pinned seed contradicts (D4 gaps, recorded and not judged here).
The write pattern of the chunked path is observed from outside (a DYLD shim for the native lane, a Bun
preload for the JS lane). Mutants of src/image*.bend are killed by a wrong observation, never a crash. The open
round-trip law of src/image-OPEN.bend is instantiated at fuels that include the counterexamples of its first statement,
and 300 generated programs and 300 random record plans (fuzz.py) are held to the same independent reference.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TIMEOUT_SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # hang guard only; gates set it under load

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import freeze  # noqa: E402
import fuzz  # noqa: E402
import reference  # noqa: E402
import render  # noqa: E402
import synthetic  # noqa: E402

codec = reference.codec
evaluator = reference.load('knot_evaluate', ROOT / 'vm/evaluate.py')
BUILD = ROOT / '.local/compiler-image/gate'
RECEIPT = HERE / 'receipts/image.json'
SEED = ROOT / 'scripts/bend-reference'
PROFILE = '--profile=knot-image-1'
NAME_REFUSED = 'Unsupported\tcompile\timage-name\t0:0:0:0'
NONE = 0xFFFFFFFF
WORKERS = 8


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def toolchain() -> dict:
    """The seed's native lane probes $CC, then `clang`. On macOS /usr/bin/clang is an xcrun shim that
    intermittently prints nothing under parallel load, which the seed reports as "found no clang" (see
    docs/compiler-campaign/GATES.md). The runner passes the resolved compiler; a direct run does the same."""
    env = {}
    if sys.platform == 'darwin':
        for key, argv in (('CC', ['xcrun', '--find', 'clang']), ('SDKROOT', ['xcrun', '--show-sdk-path'])):
            if not os.environ.get(key):
                found = subprocess.run(argv, capture_output=True, text=True, timeout=60)
                if found.returncode == 0 and found.stdout.strip():
                    env[key] = found.stdout.strip()
    return env


TOOLCHAIN = toolchain()


def run(argv, timeout=60, env=None):
    argv = [str(x) for x in argv]
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout * TIMEOUT_SCALE,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1', **TOOLCHAIN, **(env or {})})
    except subprocess.TimeoutExpired:
        raise AssertionError(f'harness timeout: {argv[:3]}')
    return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def shown(result) -> dict:
    return {'exit': result['exit'], 'stdout': result['stdout'].decode('utf-8', 'replace')[:300],
            'stderr': result['stderr'].decode('utf-8', 'replace')[:300]}


def pmap(function, items):
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(function, items))


# ---------------------------------------------------------------- builds

def build(entry: Path, output: Path, timeout=900):
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run([SEED, entry, '-o', output], timeout)
    require(result['exit'] == 0 and output.exists(), ('build', entry, shown(result)))
    return {'entry': str(entry.relative_to(ROOT)), 'sha256': sha(output.read_bytes())}


def tool_set(tree: Path) -> dict:
    """The compiler, checker and codec driver of a source tree, natively and as Bun JS."""
    return {'compile': tree / 'compile', 'compile-js': tree / 'compile.js', 'image': tree / 'image',
            'image-js': tree / 'image.js'}


def build_tools(source_tree: Path, tree: Path) -> list:
    entries = [(source_tree / 'src/compile-cli.bend', tree / 'compile'),
               (source_tree / 'src/compile-cli.bend', tree / 'compile.js'),
               (source_tree / 'tests/compiler-image/image-cli.bend', tree / 'image'),
               (source_tree / 'tests/compiler-image/image-cli.bend', tree / 'image.js')]
    return pmap(lambda e: build(*e), entries)


# ---------------------------------------------------------------- the listed sources

def native(tools, *args):
    return run([tools['compile'], *args])


def bun(tools, *args):
    return run(['bun', tools['compile-js'], *args])


def image_of(tools, path, output, lane):
    output.unlink(missing_ok=True)
    return (native if lane == 'native' else bun)(tools, PROFILE, path, output)


def judge(frozen, seen) -> dict:
    """What each listed source is held to, from the frozen file and this run's own `check-cli`:
      frozen          check-cli accepts it and the reference image equals the frozen one (D7: byte identity);
      newly-accepted  check-cli accepts it, the frozen file did not: a gap closed. The live reference judges it;
      moved           the source text is not the frozen text, and check-cli accepts it: the live reference judges it;
      refused         check-cli refuses it (Invalid, Unsupported or Exhausted): the image profile must answer as
                      check-cli does, live. This includes the D4 gaps of seed-audit.json, which are not judged.
    A book accepted at the freeze that check-cli now refuses, and a host or internal failure, fail the gate."""
    rows = {}
    for path, entry in frozen['sources'].items():
        require((ROOT / path).is_file(), (path, 'a listed source is missing'))
        moved = sha((ROOT / path).read_bytes()) != entry['sha256']
        now = seen[path]
        if now['exit'] == 0:
            image = freeze.reference_image(path, now)
            live = {'sha256': sha(image), 'bytes': len(image)}
            if 'image' in entry and not moved:
                require(live == entry['image'], (path, 'the reference image drifted from the frozen one'))
                kind = 'frozen'
            else:
                kind = 'moved' if moved else 'newly-accepted'
            rows[path] = {'kind': kind, 'image': live}
        else:
            require(now['exit'] in (2, 3, 4), (path, 'check-cli failed as a host or internal failure', now['exit'], now['stderr']))
            require(moved or 'image' not in entry, (path, 'accepted at the freeze, refused by check-cli now', now['stderr']))
            rows[path] = {'kind': 'refused', 'moved': moved, 'check': {'exit': now['exit'], 'stderr': now['stderr']}}
    return rows


def accepted(rows) -> list:
    return sorted(p for p, r in rows.items() if r['kind'] != 'refused')


def refuses(function) -> bool:
    try:
        function()
    except AssertionError:
        return True
    return False


def judge_controls(frozen, seen) -> dict:
    """Judging keeps the gate off the merge path, so each promise is a control on a real row with one thing altered:
    a book whose image is frozen, a gap that closes, a source that moves, a checker that regresses or fails, a drifted
    reference, and a book that the seed rejects and check-cli accepts."""
    good = 'vm/golden/let.bend'
    bad = 'tests/compiler-checker/fixtures/branch-duplicate.bend'
    require(seen[good]['exit'] == 0 and seen[bad]['exit'] == 2, 'the judging controls need one accepted and one Invalid source')
    entry = frozen['sources'][good]
    refused = {'sha256': frozen['sources'][bad]['sha256']}

    def judged(path, held, now):
        return judge({'sources': {path: held}}, {path: now})[path]['kind']
    controls = {
        'frozen': judged(good, entry, seen[good]) == 'frozen',
        'gap-closed': judged(good, {'sha256': entry['sha256']}, seen[good]) == 'newly-accepted',
        'source-moved': judged(good, {**entry, 'sha256': '0' * 64}, seen[good]) == 'moved',
        'refused-stays-refused': judged(bad, refused, seen[bad]) == 'refused',
        'regression': refuses(lambda: judge({'sources': {bad: {**refused, 'image': entry['image']}}}, {bad: seen[bad]})),
        'drift': refuses(lambda: judge({'sources': {good: {**entry, 'image': {**entry['image'], 'bytes': entry['image']['bytes'] + 4}}}}, {good: seen[good]})),
        'host-failure': refuses(lambda: judge({'sources': {bad: refused}}, {bad: {**seen[bad], 'exit': 5}})),
        'missing-source': refuses(lambda: judge({'sources': {'tests/compiler-image/missing.bend': refused}}, {'tests/compiler-image/missing.bend': seen[bad]})),
    }
    audit = json.loads((HERE / 'seed-audit.json').read_text())
    rejected = audit['seed_rejects'][0]
    rows = judge({'sources': {p: frozen['sources'][p] for p in audit['rows']}}, {p: seen[p] for p in audit['rows']})
    controls['seed-rejected-accepted'] = refuses(lambda: audit_summary({**rows, rejected: {'kind': 'newly-accepted'}}, seen))
    require(all(controls.values()), ('a judging control failed', controls))
    return controls


def source_case(tools, rows, path):
    row = rows[path]
    out = BUILD / 'images' / (path.replace('/', '__') + '.kimg')
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = {}
    for lane in ('native', 'bun'):
        result = image_of(tools, ROOT / path, out.with_suffix(f'.{lane}.kimg'), lane)
        target = out.with_suffix(f'.{lane}.kimg')
        if row['kind'] != 'refused':
            data = target.read_bytes() if target.exists() else b''
            require(result['exit'] == 0 and result['stdout'] == f'Built\t{len(data)}\n'.encode() and result['stderr'] == b'',
                    (path, lane, shown(result)))
            require(sha(data) == row['image']['sha256'] and len(data) == row['image']['bytes'],
                    (path, lane, 'image bytes differ from the reference'))
            seen[lane] = data
        else:
            want = row['check']
            require(result['exit'] == want['exit'] and result['stderr'].decode() == want['stderr'] and result['stdout'] == b''
                    and not target.exists(), (path, lane, 'the image profile answers otherwise than check-cli', shown(result), want))
            seen[lane] = None
    require(seen['native'] == seen['bun'], (path, 'native and Bun images differ'))
    if seen['native'] is not None:
        plan = codec.decode(seen['native'], reference.DIGEST)
        require(codec.validate(plan, reference.REGISTRY) == [], (path, 'the codec refuses the image'))
        require(codec.encode(plan, reference.DIGEST) == seen['native'], (path, 'the image is not canonical'))
        out.write_bytes(seen['native'])
    return path


def audit_summary(rows, seen) -> dict:
    """The seed's recorded verdict on each Invalid source (audit.py). The seed is not run here. A source the seed
    rejects that check-cli accepts is a soundness fault; a source the seed accepts and check-cli calls Invalid is a
    D4 gap, recorded and not judged; an Invalid source the audit does not cover, or covers under other text, is reported."""
    audit = json.loads((HERE / 'seed-audit.json').read_text())
    covered = set(audit['seed_rejects']) | set(audit['d4_gaps'])
    require(len(covered) == len(audit['seed_rejects']) + len(audit['d4_gaps']) == audit['invalid_sources'] == len(audit['rows'])
            and covered == set(audit['rows']) and covered <= set(rows), 'seed-audit.json is not consistent')
    stale = sorted(p for p in covered if sha((ROOT / p).read_bytes()) != audit['rows'][p]['sha256'])
    live = sorted(p for p in rows if seen[p]['exit'] == 2)
    accepted_against_the_seed = sorted(p for p in audit['seed_rejects'] if p not in stale and rows[p]['kind'] != 'refused')
    require(not accepted_against_the_seed, ('check-cli accepts sources that the pinned seed rejects', accepted_against_the_seed))
    return {'invalid_now': len(live), 'seed_rejects': len(audit['seed_rejects']), 'd4_gaps': audit['d4_gaps'],
            'd4_gaps_closed': sorted(p for p in audit['d4_gaps'] if p not in stale and rows[p]['kind'] != 'refused'),
            'unaudited_invalid': sorted(set(live) - covered), 'stale': stale}


# ---------------------------------------------------------------- goldens under the reference evaluation

def golden_case(vm_expected, path):
    name = Path(path).stem
    data = (BUILD / 'images' / (path.replace('/', '__') + '.kimg')).read_bytes()
    require(data == Path(path).with_suffix('.kimg').read_bytes() == (ROOT / path).with_suffix('.kimg').read_bytes(),
            (name, 'the image differs from the committed golden image'))
    plan = codec.decode(data, reference.DIGEST)
    expected = vm_expected['cases'][name]
    got = evaluator.book(plan, 'main', [], 1_000_000)
    require(got.get('exit') == expected['exit'] and got.get('stdout') == expected['stdout'], (name, got, expected))
    invoked = 0
    for row in vm_expected['invocations'].get(name, []):
        words = row['argv'][1:]
        verdict = codec.invocation(plan, words)
        if verdict:
            outcome, cause = verdict.split(' ', 1)
            require((row['outcome'], row['cause']) == (outcome, cause), (name, words, verdict, row))
        else:
            result = evaluator.book(plan, words[0], [codec.decimal(w) for w in words[2:]], codec.decimal(words[1]))
            require(result.get('exit') == row['exit'] and result.get('stdout') == row['stdout'], (name, words, result, row))
        invoked += 1
    return {'name': name, 'invocations': invoked}


# ---------------------------------------------------------------- the codec driver

def codec_case(tools, path: Path):
    """decode prints serializer.decode's plan in render.py's text, and recode re-encodes it byte for byte."""
    data = path.read_bytes()
    want = (render.render(codec.decode(data, reference.DIGEST)) + '\n').encode()
    for lane, command in (('native', [tools['image']]), ('bun', ['bun', tools['image-js']])):
        shown_plan = run([*command, 'decode', path])
        require(shown_plan['exit'] == 0 and shown_plan['stdout'] == want, (str(path), lane, 'decode', shown(shown_plan)))
        again = BUILD / 'recode' / f'{path.name}.{lane}'
        again.parent.mkdir(exist_ok=True)
        again.unlink(missing_ok=True)
        result = run([*command, 'recode', path, again])
        require(result['exit'] == 0 and again.exists() and again.read_bytes() == data
                and result['stdout'] == f'Built\t{len(data)}\n'.encode(), (str(path), lane, 'recode', shown(result)))
    return path.name


def book_case(tools, rows, path):
    """decode(encode(b)) = erase_tokens(b), observed on one book: the Bend `erase_tokens` of the checked book
    prints as serializer.decode of the image the compiler wrote (both lanes), and `roundtrip` compares Bend's own
    decode-of-encode with its erase_tokens (native lane)."""
    image = (BUILD / 'images' / (path.replace('/', '__') + '.kimg')).read_bytes()
    require(sha(image) == rows[path]['image']['sha256'], (path, 'image'))
    want = (render.render(codec.decode(image, reference.DIGEST)) + '\n').encode()
    for lane, command in (('native', [tools['image']]), ('bun', ['bun', tools['image-js']])):
        plan = run([*command, 'plan', ROOT / path])
        require(plan['exit'] == 0 and plan['stdout'] == want, (path, lane, 'plan', shown(plan)))
    # `roundtrip` renders two plans and decodes one; on the Bun lane that overflows the machine stack for the
    # deepest fixtures (the seed's documented bound), so the native lane, the reference, observes it.
    trip = run([tools['image'], 'roundtrip', ROOT / path])
    require(trip['exit'] == 0 and trip['stdout'] == b'Roundtrip\tequal\n', (path, 'roundtrip', shown(trip)))
    return path


# ---------------------------------------------------------------- refusals of the decoder

def words_of(data: bytes) -> list:
    return list(struct.unpack(f'<{len(data) // 4}I', data))


def bytes_of(words: list) -> bytes:
    return struct.pack(f'<{len(words)}I', *words)


def records(words: list, section: int) -> list:
    """Offsets of a section's records, from the header's section offset."""
    start = words[5 + section]
    at, out = start + 1, []
    for _ in range(words[start]):
        out.append(at)
        at += words[at]
    return out


def crafted() -> list:
    """Images that break one rule of the format, with the reason the Bend decoder must give."""
    flat = words_of((ROOT / 'vm/golden/recursion-map.kimg').read_bytes())
    keyed = words_of((ROOT / 'vm/golden/default-hit.kimg').read_bytes())
    out = []

    def edit(base, index, delta):
        w = list(base)
        w[index] = (w[index] + delta) & 0xFFFFFFFF
        return bytes_of(w)

    out.append(('magic', edit(flat, 0, 1), 'HostFailure\timage\tmagic'))
    out.append(('registry-digest', edit(flat, 24, 1), 'HostFailure\timage\tregistry digest'))
    out.append(('total-truncated', bytes_of(flat[:-1]), 'HostFailure\timage\ttotal'))
    out.append(('not-whole-words', bytes_of(flat) + b'\0', 'HostFailure\timage\tlength'))
    out.append(('section-offset', edit(flat, 6, 1), 'HostFailure\timage\tsection offset'))
    construct = next(r for r in records(flat, 4) if flat[r + 1] == 4)               # a `con` node
    out.append(('child-offset', edit(flat, construct + 5, 1), 'HostFailure\timage\tchild offset'))
    out.append(('function-root', edit(flat, records(flat, 2)[0] + 5, 1), 'HostFailure\timage\tfunction root'))
    case = next(r for r in records(keyed, 4) if keyed[r + 1] == 8)                  # the keys-mode Case
    out.append(('case-key', edit(keyed, case + 7, 1), 'HostFailure\timage\tcase key'))          # a row's key
    out.append(('case-arm-offset', edit(keyed, case + 8, 1), 'HostFailure\timage\tcase key'))     # a row's arm
    out.append(('image-size', bytes(4 * (4 * 1024 * 1024 + 1)), 'Exhausted\tcompile\tbudget\t0:0:0:0'))
    # A name record is [length, byte length, packed bytes...]: byte length 0, a zero byte, and a wide (valid UTF-8) name.
    name = records(flat, 5)[0]
    low = flat[name + 2] & 255
    out.append(('name-length', edit(flat, name + 1, -flat[name + 1]), 'HostFailure\timage\tname length'))
    out.append(('name-padding', edit(flat, name + 2, -low), 'HostFailure\timage\tname padding'))
    out.append(('name-wide', edit(flat, name + 2, 0xC3 - low), 'Unsupported\tcompile\timage-name\t0:0:0:0'))
    return out


def refusal_case(tools, name, data, message):
    path = BUILD / 'crafted' / f'{name}.kimg'
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(data)
    for lane, command in (('native', [tools['image']]), ('bun', ['bun', tools['image-js']])):
        result = run([*command, 'decode', path])
        require(result['stdout'] == b'' and result['stderr'].decode() == message + '\n'
                and result['exit'] == {'Exhausted': 4, 'Unsupported': 3}.get(message.split('\t')[0], 5), (name, lane, shown(result)))
    return name


# ---------------------------------------------------------------- the profile: budgets, caps, outputs

def profile_controls(tools, rows, spec) -> list:
    """Each control: an argument list, the exit and the exact stderr, checked on both seed lanes."""
    padded = BUILD / 'padded.bend'
    text = (ROOT / spec['character_cap']['book']).read_text()
    padded_chars = spec['character_cap']['padded_characters']
    padded.write_text(text + '#' + 'x' * (padded_chars - len(text) - 2) + '\n')
    require(len(padded.read_text()) == padded_chars, 'padded source length')
    tiny = BUILD / 'tiny.bend'
    tiny.write_text(text)
    stale = BUILD / 'stale.kimg'
    good = ROOT / 'vm/golden/let.bend'
    bad = ROOT / 'vm/golden/nat-add.bend'                                           # Unsupported parse declaration-form
    out = BUILD / 'controls.kimg'
    usage = 'HostFailure\targuments\t'
    budgets = spec['profile']['maximum_overrides']
    default_usage = usage + 'expected ' + spec['profile']['default_arguments_unchanged']
    line = padded.read_text()[:65536].count('\n') + 1
    column = 65536 - (padded.read_text()[:65536].rfind('\n') + 1)
    # The profile's own character maximum: a book of exactly 4,194,304 characters is admitted at that
    # budget, and one character more is exhausted by the lexer at the last admitted offset.
    ceiling = budgets['characters']
    at_ceiling, over_ceiling = BUILD / 'ceiling.bend', BUILD / 'over-ceiling.bend'
    at_ceiling.write_text(text + '#' + 'x' * (ceiling - len(text) - 2) + '\n')
    over_ceiling.write_text(text + '#' + 'x' * (ceiling + 1 - len(text) - 2) + '\n')
    cut = over_ceiling.read_text()[:ceiling]
    ceiling_line, ceiling_column = cut.count('\n') + 1, ceiling - (cut.rfind('\n') + 1)
    controls = [
        # (label, argv, exit, stderr, stdout)
        ('default-profile-usage', [good], 5, default_usage, ''),
        ('default-profile-three-arguments', [good, out, '1'], 5, default_usage, ''),
        ('unknown-profile', ['--profile=knot-fields-wasm-1', good, out], 5, usage + 'unknown-profile', ''),
        ('image-profile-usage', [PROFILE, good], 5, usage + 'expected ' + spec['profile']['arguments'], ''),
        ('image-profile-six-arguments', [PROFILE, good, out, '1', '2', '3'], 5, usage + 'expected ' + spec['profile']['arguments'], ''),
        ('source-is-output', [PROFILE, good, good], 5, usage + 'source-is-output', ''),
        ('characters-over-maximum', [PROFILE, good, out, str(budgets['characters'] + 1), '512', '512', '1048576', '16777216'], 5, usage + 'budget-out-of-range', ''),
        ('parser-over-maximum', [PROFILE, good, out, '65536', str(budgets['parser_depth'] + 1), '512', '1048576', '16777216'], 5, usage + 'budget-out-of-range', ''),
        ('checker-over-maximum', [PROFILE, good, out, '65536', '512', str(budgets['checker_depth'] + 1), '1048576', '16777216'], 5, usage + 'budget-out-of-range', ''),
        ('emitter-over-maximum', [PROFILE, good, out, '65536', '512', '512', str(budgets['emitter_depth'] + 1), '16777216'], 5, usage + 'budget-out-of-range', ''),
        ('output-over-maximum', [PROFILE, good, out, '65536', '512', '512', '1048576', str(budgets['output_bytes'] + 1)], 5, usage + 'budget-out-of-range', ''),
        ('budget-not-a-number', [PROFILE, good, out, '65536', '512', '512', 'many', '16777216'], 5, usage + 'expected-u32', ''),
        ('emitter-depth-zero', [PROFILE, good, out, '65536', '512', '512', '0', '16777216'], 4, 'Exhausted\tcompile\tbudget\t0:0:0:0', ''),
        ('output-too-small', [PROFILE, good, out, '65536', '512', '512', '1048576', '16'], 4, 'Exhausted\tcompile\tbudget\t0:0:0:0', ''),
        ('invalid-source-leaves-output', [PROFILE, ROOT / 'tests/compiler-checker/fixtures/branch-duplicate.bend', out], 2, None, ''),
        ('unsupported-source-leaves-output', [PROFILE, bad, out], 3, 'Unsupported\tparse\tdeclaration-form\t0:6:1:0', ''),
        # The default profile keeps its caps: the same 67,190-character source is exhausted at 65,536.
        ('default-profile-cap-unchanged', [padded, out], 4, f'Exhausted\tlex\tbudget\t65536:65536:{line}:{column}', ''),
        ('default-profile-cap-override-unchanged', [padded, out, '65537', '512', '512', '4096', '65536'], 5, usage + 'budget-out-of-range', ''),
        ('characters-at-budget', [PROFILE, tiny, out, str(len(text)), '512', '512', '1048576', '16777216'], 0, '', f'Built\t{rows[spec["character_cap"]["book"]]["image"]["bytes"]}'),
        ('characters-over-budget', [PROFILE, tiny, out, str(len(text) - 1), '512', '512', '1048576', '16777216'], 4, None, ''),
        ('characters-at-maximum', [PROFILE, at_ceiling, out, str(ceiling), '512', '512', '1048576', '16777216'], 0, '', f'Built\t{rows[spec["character_cap"]["book"]]["image"]["bytes"]}'),
        ('characters-over-maximum-source', [PROFILE, over_ceiling, out, str(ceiling), '512', '512', '1048576', '16777216'], 4,
         f'Exhausted\tlex\tbudget\t{ceiling}:{ceiling}:{ceiling_line}:{ceiling_column}', ''),
    ]
    results = []
    for label, argv, code, message, printed in controls:
        for lane in ('native', 'bun'):
            stale.write_bytes(b'stale')
            out.write_bytes(b'stale')
            result = (native if lane == 'native' else bun)(tools, *argv)
            got = result['stderr'].decode()
            require(result['exit'] == code, (label, lane, shown(result)))
            if message is not None:
                require(got == (message + '\n' if message else ''), (label, lane, shown(result)))
            else:
                require(got.startswith(('Invalid\t', 'Exhausted\t', 'Unsupported\t')), (label, lane, shown(result)))
            require(result['stdout'].decode() == (printed + '\n' if printed else ''), (label, lane, shown(result)))
            if code:
                require(out.read_bytes() == b'stale', (label, lane, 'a failed compile touched the output'))
        results.append(label)
    # The padded book is admitted by the image profile at its default characters budget, unchanged.
    for lane in ('native', 'bun'):
        result = image_of(tools, padded, out, lane)
        want = rows[spec['character_cap']['book']]['image']
        require(result['exit'] == 0 and sha(out.read_bytes()) == want['sha256'], ('padded', lane, shown(result)))
    results.append('padded-source-admitted')
    return results


def default_hashes(tools, expectations) -> int:
    """The default profile's modules are unchanged: 25 frozen hashes, in both lanes."""
    baseline = expectations['default_module_hashes']
    require(len(baseline) == 25, 'frozen enum corpus')

    def compiled(item):
        source, expected = item
        for lane in ('native', 'bun'):
            output = BUILD / 'default' / f'{Path(source).stem}.{lane}.wasm'
            output.parent.mkdir(exist_ok=True)
            output.unlink(missing_ok=True)
            result = (native if lane == 'native' else bun)(tools, ROOT / source, output)
            require(result['exit'] == 0 and sha(output.read_bytes()) == expected, ('default module changed', source, lane, shown(result)))
        return source
    return len(pmap(compiled, baseline.items()))


# ---------------------------------------------------------------- the chunked path, observed from outside

def write_log(command, source, output, budgets, env):
    log = BUILD / 'writes.log'
    log.unlink(missing_ok=True)
    output.unlink(missing_ok=True)
    result = run([*command, PROFILE, source, output, *budgets], 300, {**env, 'KNOT_WRITE_LOG': str(log)})
    lines = [tuple(map(int, l.split())) for l in log.read_text().splitlines()] if log.exists() else []
    return result, lines


def chunk_evidence(tools, spec) -> dict:
    """The synthetic book's image passes 4 MiB and reaches the file in chunks of at most 65,536 bytes."""
    sample = BUILD / 'synthetic.bend'
    sample.write_text(synthetic.source())
    require(sha(sample.read_bytes()) == spec['source_sha256'], 'synthetic source drifted')
    budgets = ['1048576', '4096', '4096', '1048576', '16777216']
    shim = BUILD / 'writes.dylib'
    shim_run = run([TOOLCHAIN.get('CC') or os.environ.get('CC') or 'clang', '-dynamiclib', '-o', shim, HERE / 'writes.c'])
    require(shim_run['exit'] == 0, ('shim', shown(shim_run)))
    record = {}
    for lane, command, env in (('native', [tools['compile']], {'DYLD_INSERT_LIBRARIES': str(shim)}),
                               ('bun', ['bun', '--preload', HERE / 'writes.js', tools['compile-js']], {})):
        out = BUILD / f'synthetic.{lane}.kimg'
        result, writes = write_log(command, sample, out, budgets, env)
        data = out.read_bytes()
        require(result['exit'] == 0 and result['stdout'] == f'Built\t{len(data)}\n'.encode(), (lane, shown(result)))
        require(len(data) >= spec['minimum_image_bytes'] and len(data) == spec['image_bytes']
                and sha(data) == spec['image_sha256'], (lane, 'synthetic image'))
        sizes = [done for _, done in writes]
        require(len(sizes) >= 2 and sum(sizes) == len(data) and max(sizes) <= 65536 and all(n == c for c, n in writes),
                (lane, 'the image was not written in bounded chunks', len(sizes), max(sizes or [0])))
        plan = codec.decode(data, reference.DIGEST)
        require(codec.validate(plan, reference.REGISTRY) == [] and codec.encode(plan, reference.DIGEST) == data,
                (lane, 'the codec refuses the synthetic image'))
        record[lane] = {'writes': len(sizes), 'largest': max(sizes), 'bytes': len(data)}
    # Above the image ceiling the compile is exhausted before the output is opened.
    heavy = BUILD / 'over-limit.bend'
    saved = synthetic.LETS
    synthetic.LETS = 14
    try:
        heavy.write_text(synthetic.source())
        words = len(codec.encode(synthetic.plan(), reference.DIGEST)) // 4
    finally:
        synthetic.LETS = saved
    require(words > 4 * 1024 * 1024, ('over-limit book is over the ceiling', words))
    stale = BUILD / 'over-limit.kimg'
    for lane, command in (('native', [tools['compile']]), ('bun', ['bun', tools['compile-js']])):
        stale.write_bytes(b'stale')
        result = run([*command, PROFILE, heavy, stale, '4194304', *budgets[1:]], 300)
        require(result['exit'] == 4 and result['stderr'] == b'Exhausted\tcompile\tbudget\t0:0:0:0\n' and stale.read_bytes() == b'stale',
                (lane, 'over the image ceiling', shown(result)))
    record['over_limit_words'] = words
    # The same book, past the size limit, is the first statement's counterexample on a checked book: erasure answers,
    # and the image is refused. `answers` prints both (native lane: the Bun lane would erase the book twice in 2 GB).
    over = run([tools['image'], 'answers', heavy], 300)
    require(over['exit'] == 0 and over['stdout'] == b'erase_tokens\tDone\nrecoded\tExhausted\tcompile\tbudget\t0:0:0:0\n', ('over the image ceiling', shown(over)))
    within = run([tools['image'], 'answers', ROOT / 'vm/golden/let.bend'])
    require(within['exit'] == 0 and within['stdout'] == b'erase_tokens\tDone\nrecoded\tDone\n', ('within the image ceiling', shown(within)))
    # The output cap admits at least 8 MiB: an image of that size is observed through the chunked path
    # (native lane; Bun would need about 2 GB for it).
    saved = synthetic.LETS
    synthetic.LETS = 6
    try:
        big = BUILD / 'eight-mib.bend'
        big.write_text(synthetic.source())
        expected = codec.encode(synthetic.plan(), reference.DIGEST)
    finally:
        synthetic.LETS = saved
    require(len(expected) >= 8 * 1024 * 1024, ('eight-MiB book', len(expected)))
    out = BUILD / 'eight-mib.kimg'
    result, writes = write_log([tools['compile']], big, out, ['4194304', *budgets[1:]], {'DYLD_INSERT_LIBRARIES': str(shim)})
    require(result['exit'] == 0 and out.read_bytes() == expected and result['stdout'] == f'Built\t{len(expected)}\n'.encode(), ('eight MiB', shown(result)))
    sizes = [done for _, done in writes]
    require(len(sizes) > 2 and sum(sizes) == len(expected) and max(sizes) <= 65536, ('eight MiB chunks', len(sizes)))
    record['eight_mib'] = {'bytes': len(expected), 'writes': len(sizes), 'largest': max(sizes)}
    return record


def name_controls(tools, check_cli) -> dict:
    """An identifier names an image; any other name is refused by layout as `Unsupported compile image-name`, before
    any word exists (`image-cli named` encodes the one-function book whose datatype has the given name)."""
    source = 'type Flag is Data:\n  Off{}\n  On{}\n\ndef main() -> Flag:\n  On{}\n'
    path = BUILD / 'named-flag.bend'
    path.write_text(source)
    core = run([check_cli, path])
    require(core['exit'] == 0, shown(core))
    words = len(reference.image(source, core['stdout'].decode())) // 4
    controls = (('Flag', 0, f'Encoded\t{words}\n', ''), ('\u00e9', 3, '', NAME_REFUSED + '\n'), ('', 3, '', NAME_REFUSED + '\n'))
    for lane, command in (('native', [tools['image']]), ('bun', ['bun', tools['image-js']])):
        for name, code, printed, refused in controls:
            result = run([*command, 'named', name])
            require(result['exit'] == code and result['stdout'].decode() == printed and result['stderr'].decode() == refused,
                    (lane, name, shown(result)))
    return {'words': words, 'refused': ['\u00e9', '']}


def deep_reference(spec_tree: Path) -> dict:
    """The synthetic plan generator agrees with the checker: a small instance, checked by a check-cli whose
    parser depth is raised (the shipped one stops at 512, below a 256-field constructor)."""
    tree = BUILD / 'deep'
    (tree / 'src').mkdir(parents=True, exist_ok=True)
    for source in (ROOT / 'src').glob('*.bend'):
        shutil.copy2(source, tree / 'src' / source.name)
    target = tree / 'src/check-cli.bend'
    text = target.read_text()
    require(text.count('P.parse(512n') == 1, 'parser depth site')
    target.write_text(text.replace('P.parse(512n', 'P.parse(4096n'))
    binary = tree / 'check-cli'
    build(target, binary)
    saved = synthetic.FUNCTIONS
    synthetic.FUNCTIONS = 3
    try:
        source, plan = synthetic.source(), synthetic.plan()
    finally:
        synthetic.FUNCTIONS = saved
    path = BUILD / 'synthetic-small.bend'
    path.write_text(source)
    shown_core = run([binary, path, '65536', '4096'])
    require(shown_core['exit'] == 0, shown(shown_core))
    require(reference.plan(source, shown_core['stdout'].decode()) == plan, 'synthetic plan differs from the checked core')
    return {'functions': 3, 'source_bytes': len(source)}


# ---------------------------------------------------------------- mutants of src/image*.bend

# (name, file, [(old, new)], driver, witnesses). A driver is `compile` (witness: a source), `recode` (a
# committed image), `refuse` (a crafted image) or `writes` (the synthetic book). The file is the module
# of src/ that holds the mutation site: the plan (image-plan), the encoder (image), the layout
# (image-layout) or the decoder (image-decode).
MUTANTS = [
    ('wrong-construct-tag', 'image-layout', [('placed => counted(placed,4,type_id,tag))', 'placed => counted(placed,4,type_id,U32.add(tag,1)))')],
     'compile', ['vm/golden/construct.bend']),
    ('swapped-let-fields', 'image-layout', [('pushed(state,7,type_id,[slot,initial,result])', 'pushed(state,7,type_id,[initial,slot,result])')],
     'compile', ['vm/golden/let.bend']),
    ('let-typed-by-value', 'image', [('Lowered{Con{initial,Nil{}},Nil{},+a} Lowered{Con{+result,Nil{}},Nil{},+b}:\n      Done{one(P.Let{P.type_of(result),slot,initial,result},max_depth(a,b))}',
                                     'Lowered{Con{+initial,Nil{}},Nil{},+a} Lowered{Con{+result,Nil{}},Nil{},+b}:\n      Done{one(P.Let{P.type_of(initial),slot,initial,result},max_depth(a,b))}')],
     'compile', ['tests/compiler-image/witnesses/let-changes-type.bend']),
    ('erased-operand-kept', 'image', [('S.choose(Result<S.Error,Lowered>,U32.is_eq(q,0),u => lower(n,Operands{tail,rest}', 'S.choose(Result<S.Error,Lowered>,U32.is_eq(q,4294967295),u => lower(n,Operands{tail,rest}')],
     'compile', ['vm/golden/erased-argument.bend', 'vm/golden/erased-construct.bend']),
    ('erased-constructor-not-a-value', 'image', [('case Lowered{Nil{},rows,deepest}: Done{one(P.Value{type_id,tag},deepest)}', 'case Lowered{Nil{},rows,deepest}: Done{one(P.Construct{type_id,tag,Nil{}},deepest)}')],
     'compile', ['tests/compiler-fields/fixtures/all-erased-return.bend']),
    ('arms-not-in-tag-order', 'image', [('S.choose(Maybe<&2,C.Term>,U32.is_eq(pattern,tag),u => Some{head}', 'S.choose(Maybe<&2,C.Term>,True{},u => Some{head}')],
     'compile', ['tests/compiler-image/witnesses/reordered-arms.bend']),
    ('slots-not-maximal', 'image', [('Bool.pick(U32,U32.is_ge(a,b),a,b)', 'Bool.pick(U32,U32.is_ge(a,b),b,a)')],
     'compile', ['tests/compiler-image/witnesses/many-slots.bend', 'vm/golden/recursion-map.bend']),
    ('names-not-shared', 'image-layout', [('S.choose(Maybe<&2,U32>,String.eq(head,text),u => Some{top}', 'S.choose(Maybe<&2,U32>,Bool.and(False{},String.eq(head,text)),u => Some{top}')],
     'compile', ['tests/compiler-image/witnesses/shared-name.bend', 'vm/golden/unpack.bend']),
    ('section-count-off-by-one', 'image-layout', [('Con{[count_records(rows,0)],List.append(&2,List<&2,U32>,rows,tail)}', 'Con{[U32.add(1,count_records(rows,0))],List.append(&2,List<&2,U32>,rows,tail)}')],
     'compile', ['vm/golden/unpack.bend']),
    ('node-offsets-shifted', 'image-layout', [('Nodes{Nil{},U32.add(off_nodes,1),Nil{},0,0,0}', 'Nodes{Nil{},off_nodes,Nil{},0,0,0}')],
     'compile', ['vm/golden/unpack.bend']),
    ('digest-word', 'image-plan', [('[967372322,1597628945,', '[967372323,1597628945,')], 'compile', ['vm/golden/let.bend']),
    ('constant-dropped', 'image-layout', [('    case Con{head,tail}: constant_records(tail,Con{constant_record(head),acc})', '    case Con{head,tail}: constant_records(tail,acc)')],
     'recode', ['vm/golden/default-hit.kimg', 'vm/golden/string-append.kimg']),
    ('key-row-swapped', 'image-layout', [('Con{key,Con{at,Nil{}}}),state}', 'Con{at,Con{key,Nil{}}}),state}')], 'recode', ['vm/golden/default-hit.kimg']),
    ('closure-sites-not-numbered', 'image-layout', [('pushed(Nodes{records,next,pool,pooled,U32.add(sites,1),nodes},10,type_id,Con{sites,', 'pushed(Nodes{records,next,pool,pooled,U32.add(sites,1),nodes},10,type_id,Con{0,')],
     'recode', ['vm/golden/closure-nested.kimg']),
    ('decode-default-count', 'image-decode', [('Bool.pick(U32,U32.is_eq(default,P.none()),0,1)', 'Bool.pick(U32,U32.is_eq(default,P.none()),1,0)')],
     'recode', ['vm/golden/recursion-map.kimg', 'vm/golden/default-hit.kimg']),
    ('decode-case-key-unchecked', 'image-decode', [('Bool.and(U32.is_eq(at,w),U32.is_eq(k,key))', 'U32.is_eq(at,w)')], 'refuse', ['case-key']),
    ('decode-function-root-unchecked', 'image-decode', [('S.choose(Result<S.Error,List<&2,P.Function>>,U32.is_eq(at,root),u =>', 'S.choose(Result<S.Error,List<&2,P.Function>>,True{},u =>')], 'refuse', ['function-root']),
    ('decode-digest-unchecked', 'image-decode', [('P.same_words([d0,d1,d2,d3,d4,d5,d6,d7],P.digest())', 'True{}')], 'refuse', ['registry-digest']),
    ('unchunked-write', 'image-layout', [('def chunk_steps() -> Nat:\n  16384n', 'def chunk_steps() -> Nat:\n  100000000n')], 'writes', ['synthetic']),
    ('layout-writes-any-name', 'image-layout', [('S.choose(Result<S.Error,Encoded>,P.plan_spelled(shapes,functions),u =>', 'S.choose(Result<S.Error,Encoded>,True{},u =>')],
     'name', ['\u00e9', '']),
    ('name-alphabet-widened', 'image-plan', [('Bool.and(U32.is_gt(code,0),U32.is_lt(code,128))', 'Bool.and(U32.is_gt(code,0),U32.is_lt(code,256))')],
     'refuse', ['name-wide']),
]

# The exhaustive match over C.Term: deleting any of its eight forms must fail the seed's own check.
FORMS = ('Value', 'Construct', 'Reference', 'Application', 'Let', 'Case', 'Branch', 'Sequence')


def mutant_tree(name, module, replacements):
    tree = BUILD / 'mutants' / name
    if tree.exists():
        shutil.rmtree(tree)
    (tree / 'src').mkdir(parents=True)
    (tree / 'tests/compiler-image').mkdir(parents=True)
    for source in (ROOT / 'src').glob('*.bend'):
        shutil.copy2(source, tree / 'src' / source.name)
    shutil.copy2(HERE / 'image-cli.bend', tree / 'tests/compiler-image/image-cli.bend')
    target = tree / f'src/{module}.bend'
    text = target.read_text()
    for old, new in replacements:
        require(text.count(old) == 1, (name, 'the mutation site must be unique', old[:60]))
        text = text.replace(old, new)
    target.write_text(text)
    return tree


def categorized(result) -> bool:
    """A run that ended as the compiler's own outcome: exit 0, or one of the five failure exits with its
    category on stderr. A seed fail-stop (exit 1) or a signal is a crash, and never a kill."""
    if result['exit'] == 0:
        return True
    prefix = {2: 'Invalid\t', 3: 'Unsupported\t', 4: 'Exhausted\t', 5: 'HostFailure\t', 6: 'InternalFailure\t'}.get(result['exit'])
    return prefix is not None and result['stderr'].decode('utf-8', 'replace').startswith(prefix)


def mutant_case(rows, crafted_images, item):
    name, module, replacements, driver, witnesses = item
    tree = mutant_tree(name, module, replacements)
    checked = run([SEED, tree / 'src/image.bend', '--check-only'], 300)
    require(checked['exit'] == 0 and checked['stdout'].strip() == b'All terms check.', (name, 'a mutant must type-check', shown(checked)))
    wanted = {'compile': ('compile-cli', 'compile'), 'recode': ('image-cli', 'image'), 'refuse': ('image-cli', 'image'),
              'name': ('image-cli', 'image'), 'writes': ('compile-cli', 'compile')}[driver]
    entry = tree / ('src/compile-cli.bend' if wanted[0] == 'compile-cli' else 'tests/compiler-image/image-cli.bend')
    binary = tree / wanted[1]
    build(entry, binary)
    outcomes = []
    for witness in witnesses:
        if driver == 'compile':
            out = tree / 'witness.kimg'
            out.unlink(missing_ok=True)
            result = run([binary, PROFILE, ROOT / witness, out])
            good = rows[witness]['image']['sha256']
            got = sha(out.read_bytes()) if result['exit'] == 0 and out.exists() else None
            killed = got != good
        elif driver == 'recode':
            out = tree / 'witness.kimg'
            out.unlink(missing_ok=True)
            result = run([binary, 'recode', ROOT / witness, out])
            killed = not (result['exit'] == 0 and out.exists() and out.read_bytes() == (ROOT / witness).read_bytes())
        elif driver == 'refuse':
            path = tree / 'crafted.kimg'
            path.write_bytes(crafted_images[witness][0])
            result = run([binary, 'decode', path])
            killed = result['stderr'].decode() != crafted_images[witness][1] + '\n'
        elif driver == 'name':
            result = run([binary, 'named', witness])
            killed = result['stderr'].decode() != NAME_REFUSED + '\n'
        else:
            sample = BUILD / 'synthetic.bend'
            out = tree / 'witness.kimg'
            shim = BUILD / 'writes.dylib'
            result, writes = write_log([binary], sample, out, ['1048576', '4096', '4096', '1048576', '16777216'],
                                       {'DYLD_INSERT_LIBRARIES': str(shim)})
            killed = not (len(writes) >= 2 and max(n for _, n in writes) <= 65536)
        require(categorized(result), (name, witness, 'a mutant crashed instead of misbehaving', shown(result)))
        require(killed, (name, witness, 'mutant survived', shown(result)))
        outcomes.append({'witness': witness, 'exit': result['exit'], 'outcome': 'semantic-kill'})
    # The laws are a second, independent way to kill it: does the seed's checker still accept the proofs?
    proved = run([SEED, tree / 'src/image-PROOF.bend'], 300)
    return {'name': name, 'module': module, 'driver': driver, 'replacements': len(replacements), 'witnesses': outcomes,
            'laws_refuse': not (proved['exit'] == 0 and proved['stdout'].strip() == b'All terms check.')}


def exhaustive_case(form):
    text = (ROOT / 'src/image.bend').read_text()
    marker = f'    case 1n+ +n Term{{C.{form}{{'
    require(text.count(marker) == 1, (form, 'arm site'))
    start = text.index(marker)
    end = text.index('\n    case ', start + 1) + 1
    tree = BUILD / 'exhaustive' / form
    (tree / 'src').mkdir(parents=True, exist_ok=True)
    for source in (ROOT / 'src').glob('*.bend'):
        shutil.copy2(source, tree / 'src' / source.name)
    (tree / 'src/image.bend').write_text(text[:start] + text[end:])
    result = run([SEED, tree / 'src/image.bend', '--check-only'], 120)
    # The seed names the missing constructor: the failure is the match, not a broken edit.
    require(result['exit'] != 0 and f'cases for core.{form}'.encode() in result['stdout'] + result['stderr'], (form, 'a missing arm must fail the check', shown(result)))
    return form


# ---------------------------------------------------------------- generated books

FUZZ_PROGRAMS = 300


def fuzz_case(tools, check_cli, seed):
    """One generated program: refused by check-cli, or its image is the reference's and it round-trips."""
    source = fuzz.program(seed)
    path = BUILD / 'fuzz' / f'p{seed}.bend'
    path.write_text(source)
    core = run([check_cli, path])
    if core['exit'] != 0:
        require(core['exit'] in (2, 3), (seed, 'check-cli failed on a generated program', shown(core)))
        return {'seed': seed, 'accepted': False}
    want = reference.image(source, core['stdout'].decode())
    out = path.with_suffix('.kimg')
    for lane in ('native', 'bun') if seed % 25 == 0 else ('native',):
        result = image_of(tools, path, out, lane)
        require(result['exit'] == 0 and out.exists() and out.read_bytes() == want, (seed, lane, 'the image differs from the reference', shown(result)))
    plan = codec.decode(want, reference.DIGEST)
    require(codec.validate(plan, reference.REGISTRY) == [] and codec.encode(plan, reference.DIGEST) == want, (seed, 'the codec refuses the reference image'))
    trip = run([tools['image'], 'roundtrip', path])
    require(trip['exit'] == 0 and trip['stdout'] == b'Roundtrip\tequal\n', (seed, 'roundtrip', shown(trip)))
    return {'seed': seed, 'accepted': True, **fuzz.features(source)}


def fuzz_books(tools, check_cli) -> dict:
    """Seeded programs beyond the frozen suites: each that check-cli accepts must encode to the independent reference's
    bytes and round-trip through Bend's own decoder (D21 evidence for the open law, on books nobody hand-picked)."""
    (BUILD / 'fuzz').mkdir(exist_ok=True)
    cases = pmap(lambda seed: fuzz_case(tools, check_cli, seed), range(FUZZ_PROGRAMS))
    taken = [c for c in cases if c['accepted']]
    totals = {k: sum(c[k] for c in taken) for k in ('functions', 'erased_fields', 'erased_parameters', 'lets', 'erased_lets', 'matches', 'nested_matches')}
    require(len(taken) >= 0.8 * FUZZ_PROGRAMS and all(totals.values()), ('the generator no longer produces checked programs that exercise the encoder', len(taken), totals))
    return {'programs': FUZZ_PROGRAMS, 'accepted': len(taken), 'refused': FUZZ_PROGRAMS - len(taken), 'features': totals}


FUZZ_PLANS = 300


def plan_case(tools, seed):
    """One random plan: the reference encodes it, the Bend decoder must print the plan the reference decodes, and the Bend
    layout must write those words back byte for byte, so decode(layout(plan)) = plan and layout agrees with the reference."""
    data = codec.encode(fuzz.plan(seed), reference.DIGEST)
    decoded = codec.decode(data, reference.DIGEST)
    require(codec.encode(decoded, reference.DIGEST) == data, (seed, 'the reference image is not canonical'))
    path = BUILD / 'fuzz' / f'plan{seed}.kimg'
    path.write_bytes(data)
    want = (render.render(decoded) + '\n').encode()
    for lane, command in (('native', [tools['image']]), ('bun', ['bun', tools['image-js']])):
        if lane == 'bun' and seed % 50:
            continue
        printed = run([*command, 'decode', path])
        require(printed['exit'] == 0 and printed['stdout'] == want, (seed, lane, 'decode', shown(printed)))
        again = BUILD / 'fuzz' / f'plan{seed}.{lane}.out'
        again.unlink(missing_ok=True)
        result = run([*command, 'recode', path, again])
        require(result['exit'] == 0 and again.exists() and again.read_bytes() == data, (seed, lane, 'recode', shown(result)))
    return fuzz.forms(decoded)


def fuzz_plans(tools) -> dict:
    """Random plans beyond what this base's core produces (D21 evidence for the codec half of the open law, and for the forms
    that the merge wave's encoders add): every node form of SPEC section 3 must occur."""
    (BUILD / 'fuzz').mkdir(exist_ok=True)
    seen = pmap(lambda seed: plan_case(tools, seed), range(FUZZ_PLANS))
    forms = set().union(*seen)
    require(forms == set(codec.OPCODES), ('the generated plans miss node forms', sorted(set(codec.OPCODES) - forms)))
    return {'plans': FUZZ_PLANS, 'forms': sorted(forms), 'plans_with_form': {f: sum(f in s for s in seen) for f in sorted(forms)}}


# ---------------------------------------------------------------- the proofs and the open claim

OPEN = ROOT / 'src/image-OPEN.bend'
SHAPES = ('equal', 'refused')
# The books of src/image-LAWS.bend, and the fuels at which the claim is instantiated. The first statement of the round
# trip (`recoded == erase_tokens`) was false at fuels 1 and 2 on flag_book and 13 to 18 on mixed_book, and on a book that
# layout refuses however much fuel it has (an arity past the limit, a name that is not an identifier).
CLAIM_INSTANCES = (
    [('flag', 'B.flag_book(at)', n) for n in (0, 1, 2, 3, 64)]
    + [('mixed', 'B.mixed_book(at)', n) for n in (0, 12, 13, 18, 19, 64)]
    + [('wide', 'B.wide_book(at)', 64), ('accent', 'B.named_book(B.accent(),at)', 64)])
FIRST_STATEMENT = (('flag', 'B.flag_book(at)', 1), ('flag', 'B.flag_book(at)', 2), ('mixed', 'B.mixed_book(at)', 13),
                   ('mixed', 'B.mixed_book(at)', 18))


def open_statement() -> dict:
    """`law round_trip` of src/image-OPEN.bend as written: its clauses and its body. The gate instantiates what the
    file says; a statement it cannot read is a failure, never a skipped check."""
    found = re.search(r'^law round_trip:\n((?:  for [^\n]+\n)+)  (\{[^\n]+\})\n', OPEN.read_text(), re.M)
    require(found, 'src/image-OPEN.bend: `law round_trip` is not in the form the gate reads')
    clauses = [c.strip() for c in found.group(1).splitlines()]
    names = [re.fullmatch(r'for \+?(\w+): .+', c) for c in clauses]
    require(all(names) and [m.group(1) for m in names] == ['fuel', 'book', 'words', 'done'], ('the open law quantifies fuel, book, words, done', clauses))
    answers = re.fullmatch(r'for done: \{(.+) == Done\{words\} : Result<S\.Error,Y\.Encoded>\}', clauses[3])
    require(answers, ('the last hypothesis of the open law is that encoding answers', clauses[3]))
    return {'clauses': clauses, 'body': found.group(2), 'encode': answers.group(1)}


def books_module(directory: Path) -> None:
    """The fixed books of src/image-LAWS.bend without its laws. An entry that imports that file itself would inherit
    its unfilled laws, which only image-PROOF.bend fills."""
    kept, skipping = [], False
    for line in (ROOT / 'src/image-LAWS.bend').read_text().split('\n'):
        skipping = line.startswith('law ') or (skipping and line.strip() != '')
        if not skipping:
            kept.append(line)
    text = '\n'.join(kept).replace('import ./', f'import {os.path.relpath(ROOT / "src", directory)}/')
    (directory / 'books.bend').write_text(text)


def claim_instance(directory: Path, label: str, statement: dict, fuel: str, book: str, shape: str) -> Path:
    """The claim at one fuel and book, and a proof of it. `equal`: the conclusion holds by evaluation, whatever the
    hypothesis (the encoder answers and decodes to the erased plan, or both refuse alike). `refused`: the encoder
    does not answer, so the hypothesis is refuted and the conclusion is not needed."""
    src = os.path.relpath(ROOT / 'src', directory)
    imports = ''.join(f'import {src}/{m}.bend as {a}\n' for m, a in (('syntax', 'S'), ('core', 'C'), ('image', 'I'), ('image-plan', 'P'), ('image-layout', 'Y')))

    def at(text):
        return re.sub(r'\bbook\b', book, re.sub(r'\bfuel\b', fuel, text))
    binders = statement['clauses'][2:]
    names = ', '.join(['at'] + [re.fullmatch(r'for \+?(\w+):.*', c).group(1) for c in binders])
    body = at(statement['body'])
    laws = (f'import Base\n{imports}import ./books.bend as B\n\n'
            '# a refusal is not an answer: `answers` is inhabited by a Fail, and empty on a Done.\n'
            'def answers(result: Result<S.Error,Y.Encoded>) -> Type:\n  match result:\n    case Fail{e}: Unit\n    case Done{w}: Empty\n\n'
            'def refuted(e: Result<S.Error,Y.Encoded>, words: Y.Encoded, done: {e == Done{words} : Result<S.Error,Y.Encoded>}, unit: answers(e)) -> Empty:\n'
            '  %done : answers(_)\n  unit\n\n'
            f'law claim:\n  for +at: S.At\n' + ''.join(f'  {at(c)}\n' for c in binders) + f'  {body}\n')
    if shape == 'equal':
        proof_body = '{==}'
    else:
        require(binders, 'the refused shape needs the hypothesis of the open law')
        proof_body = f'Empty.absurd({body}, N.refuted({at(statement["encode"])}, words, done, Unit{{}}))'
    entry = f'import Base\nimport ./{label}-LAWS.bend as N\n{imports}import ./books.bend as B\n\ndef N.claim({names}):\n  {proof_body}\n'
    (directory / f'{label}-LAWS.bend').write_text(laws)
    (directory / f'{label}-PROOF.bend').write_text(entry)
    return directory / f'{label}-PROOF.bend'


def claim_shape(directory: Path, label: str, statement: dict, fuel: str, book: str, shapes=SHAPES):
    """The shape in which the instance checks, or None when none of `shapes` proves it."""
    for shape in shapes:
        if shape == 'refused' and len(statement['clauses']) < 3:
            continue
        entry = claim_instance(directory, f'{label}-{shape}', statement, fuel, book, shape)
        result = run([SEED, entry], 300)
        if result['exit'] == 0 and result['stdout'].strip() == b'All terms check.':
            return shape
    return None


def claim_case(directory: Path, statement: dict, item):
    name, book, n = item
    return {'book': name, 'fuel': n, 'shape': claim_shape(directory, f'{name}-{n}', statement, f'{n}n', book)}


def open_claim() -> dict:
    """The open law is required (D21), and it must not be false. It is read as written and instantiated at fuels that
    include the counterexamples of the first statement: each instance must be proved, either by evaluation where the
    encoder answers or by refuting the hypothesis where it does not. Two false statements, the first statement itself
    and the same law with a wrong conclusion, must not be provable at the same fuels."""
    directory = BUILD / 'open'
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True)
    books_module(directory)
    statement = open_statement()
    instances = pmap(lambda item: claim_case(directory, statement, item), CLAIM_INSTANCES)
    require(all(i['shape'] for i in instances), ('the open law is false at an instance', [i for i in instances if not i['shape']]))
    for name, book in (('flag', 'B.flag_book(at)'), ('mixed', 'B.mixed_book(at)')):
        shapes = {i['fuel']: i['shape'] for i in instances if i['book'] == name}
        require(shapes[64] == 'equal', (name, 'the conclusion holds by evaluation at fuel 64', shapes))
        # The instance at 64 is not vacuous: the hypothesis cannot be refuted there, so the encoder answers.
        require(claim_shape(directory, f'{name}-answers', statement, '64n', book, ('refused',)) is None,
                (name, 'the encoder must answer at fuel 64: the equality above would hold vacuously'))
    first = {**statement, 'clauses': statement['clauses'][:2], 'body': statement['body']}
    refused = pmap(lambda item: claim_case(directory, first, (f'first-{item[0]}', item[1], item[2])), FIRST_STATEMENT)
    require(all(r['shape'] is None for r in refused), ('the first statement was proved at a counterexample', refused))
    wrong = {**statement, 'body': re.sub(r'== I\.erase_tokens\(fuel,book\)', '== Fail{S.Exhausted{"compile",S.At{0,0,0,0}}}', statement['body'])}
    require(wrong['body'] != statement['body'], 'the wrong-conclusion control must change the body')
    unproved = claim_case(directory, wrong, ('wrong', 'B.flag_book(at)', 64))
    require(unproved['shape'] is None, ('a wrong conclusion was proved', unproved))
    return {'instances': instances, 'first_statement_refused': [(r['book'], r['fuel']) for r in refused], 'wrong_conclusion_refused': True}


def proof() -> dict:
    result = run([SEED, ROOT / 'src/image-PROOF.bend'], 300)
    require(result['exit'] == 0 and result['stdout'].strip() == b'All terms check.', ('proof', shown(result)))
    laws = (ROOT / 'src/image-LAWS.bend').read_text().count('\nlaw ')
    # The law over every book stays required and open (D21): it must type-check and be exactly one open claim.
    open_law = run([SEED, OPEN, '--check-only'], 300)
    seen = (open_law['stdout'] + open_law['stderr']).decode()
    require(open_law['exit'] != 0 and seen.startswith('Error: 1 TODO found.'), ('the general law must be one open claim', seen[:300]))
    require(OPEN.read_text().count('\nlaw ') == 1, 'one law in image-OPEN.bend')
    for entry in ('src/image-plan.bend', 'src/image-layout.bend', 'src/image-decode.bend', 'src/image.bend',
                  'src/compile-cli.bend', 'tests/compiler-image/image-cli.bend'):
        checked = run([SEED, ROOT / entry, '--check-only'], 300)
        require(checked['exit'] == 0 and checked['stdout'].strip() == b'All terms check.', (entry, shown(checked)))
    return {'laws': laws, 'open_obligations': 1, 'open_claim': open_claim()}


# ---------------------------------------------------------------- main

def digest_inputs() -> dict:
    paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
             *sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.bend')), *sorted(HERE.glob('*.json')), HERE / 'writes.c',
             HERE / 'writes.js', *sorted((HERE / 'witnesses').glob('*.bend')), ROOT / 'vm/serializer.py',
             ROOT / 'vm/evaluate.py', ROOT / 'vm/check-spec.py', ROOT / 'vm/registry.json']
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}


def main():
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    frozen = json.loads((HERE / 'expectations.json').read_text())
    vm_expected = json.loads((ROOT / 'vm/golden/vm-expected.json').read_text())
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete'}
    try:
        record['inputs'] = digest_inputs()
        record['seed'] = {f: sha((ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / f).read_bytes())
                          for f in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')}
        require(record['seed']['base.bend'] == frozen['base_sha256'] == reference.REGISTRY['base']['sha256'],
                'the pinned base.bend is not the header digest')
        record['tools'] = {t: run([t, '--version'])['stdout'].decode().strip() for t in ('bun', 'node', 'python3')}
        record['proof'] = proof()
        tree = BUILD / 'tools'
        record['builds'] = build_tools(ROOT, tree)
        check_cli = BUILD / 'check-cli'
        record['builds'].append(build(ROOT / 'src/check-cli.bend', check_cli))
        tools = tool_set(tree)

        # The contract is recomputed and must equal the file frozen before implementation. Each listed source is judged
        # by this run's own check-cli: the reference image of a book it accepts against the frozen one, and the
        # answer of the image profile on any other against check-cli's.
        require(all(frozen[k] == v for k, v in freeze.contract().items()), 'expectations.json drifted from its independent computation')
        paths = sorted(frozen['sources'])
        seen = freeze.observe_all(check_cli, paths)
        rows = judge(frozen, seen)
        kinds = {k: sum(r['kind'] == k for r in rows.values()) for k in ('frozen', 'newly-accepted', 'moved', 'refused')}
        record['sources'] = {'frozen': len(rows), 'accepted': len(accepted(rows)), 'by_kind': kinds,
                             'moved': sorted(p for p, r in rows.items() if r['kind'] == 'moved' or r.get('moved')),
                             'refused_by_exit': {str(c): sum(r['kind'] == 'refused' and r['check']['exit'] == c for r in rows.values()) for c in (2, 3, 4)}}
        record['judging'] = judge_controls(frozen, seen)
        record['seed_audit'] = audit_summary(rows, seen)
        pmap(lambda p: source_case(tools, rows, p), paths)
        goldens = [p for p in accepted(rows) if p.startswith('vm/golden/')]
        record['goldens'] = pmap(lambda p: golden_case(vm_expected, p), goldens)

        compiled = [BUILD / 'images' / (p.replace('/', '__') + '.kimg') for p in accepted(rows)]
        committed = [ROOT / p for p in frozen['golden_images']]
        codec_inputs = committed + compiled
        record['codec'] = {'images': len(codec_inputs), 'golden': len(committed), 'compiled': len(compiled)}
        pmap(lambda p: codec_case(tools, p), codec_inputs)
        refusals = crafted()
        record['round_trip_books'] = len(pmap(lambda p: book_case(tools, rows, p), accepted(rows)))
        crafted_images = {name: (data, message) for name, data, message in refusals}
        record['refusals'] = pmap(lambda r: refusal_case(tools, *r), refusals)

        record['default_profile_modules'] = default_hashes(tools, frozen)
        record['profile'] = profile_controls(tools, rows, frozen)
        record['names'] = name_controls(tools, check_cli)
        record['fuzz'] = fuzz_books(tools, check_cli)
        record['fuzz_plans'] = fuzz_plans(tools)
        record['synthetic'] = chunk_evidence(tools, frozen['synthetic'])
        record['synthetic_plan'] = deep_reference(frozen)
        record['exhaustive'] = pmap(exhaustive_case, FORMS)
        record['mutants'] = pmap(lambda m: mutant_case(rows, crafted_images, m), MUTANTS)
        require(all(digest_inputs()[p] == h for p, h in record['inputs'].items()), 'inputs changed during the gate')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2, default=str) + '\n')
    claim = record['proof']['open_claim']
    print(f"Image gate passed: {record['sources']['frozen']} listed sources ({record['sources']['accepted']} encoded and matched "
          f"to the independent reference, the rest answering as a live check-cli does; {len(record['seed_audit']['d4_gaps'])} recorded D4 gaps "
          f"not judged), {len(record['goldens'])} golden images byte-identical and evaluated, {record['round_trip_books']} books with "
          f"decode(encode(b)) = erase_tokens(b) observed, {record['codec']['images']} images through the Bend codec in 2 lanes, "
          f"{len(record['refusals'])} decoder refusals, {record['default_profile_modules']} default module hashes unchanged, "
          f"{len(record['profile'])} profile controls, {len(record['names']['refused'])} refused names, {record['fuzz']['accepted']} of "
          f"{record['fuzz']['programs']} generated programs encoded to the reference and round-tripped, {record['fuzz_plans']['plans']} random "
          f"plans of all {len(record['fuzz_plans']['forms'])} forms decoded and re-laid-out as the reference does, synthetic "
          f"{record['synthetic']['native']['bytes']}-byte image in {record['synthetic']['native']['writes']} chunked writes, a "
          f"{record['synthetic']['eight_mib']['bytes']}-byte image in {record['synthetic']['eight_mib']['writes']}, "
          f"{len(record['exhaustive'])} exhaustiveness controls, {len(record['mutants'])} mutants killed "
          f"({sum(m['laws_refuse'] for m in record['mutants'])} also refused by the laws); {record['proof']['laws']} checked laws and "
          f"{record['proof']['open_obligations']} open D21 obligation, instantiated at {len(claim['instances'])} fuels and books "
          f"with {len(claim['first_statement_refused'])} of the first statement's counterexamples refused. {RECEIPT}")


if __name__ == '__main__':
    main()
