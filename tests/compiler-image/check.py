#!/usr/bin/env python3
"""Gate `image`: src/image.bend encodes a checked book to knot-image-1 bytes, and decodes them.

Every claim is checked against a lane that does not share Bend code with the encoder:
  * the reference (reference.py): the declarations read from source text, the core that main's own
    `check-cli` displays, and vm/serializer.py's layout. Its bytes were frozen in expectations.json
    before src/image.bend existed, and this gate recomputes them and requires the file unchanged;
  * vm/serializer.py: `decode`, `validate` and canonical re-encoding of every image the compiler writes;
  * vm/evaluate.py: the golden sources' frozen expectations, run on the compiler's own images;
  * `image-cli`, whose decoder is checked against serializer.decode's plan (rendered by render.py) and
    whose re-encoding must reproduce every committed golden image byte for byte.
The write pattern of the chunked path is observed from outside (a DYLD shim for the native lane, a Bun
preload for the JS lane). Mutants of src/image.bend are killed by a wrong observation, never a crash.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
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
import reference  # noqa: E402
import render  # noqa: E402
import synthetic  # noqa: E402

codec = reference.codec
evaluator = reference.load('knot_evaluate', ROOT / 'vm/evaluate.py')
BUILD = ROOT / '.local/compiler-image/gate'
RECEIPT = HERE / 'receipts/image.json'
SEED = ROOT / 'scripts/bend-reference'
PROFILE = '--profile=knot-image-1'
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


# ---------------------------------------------------------------- the frozen sources

def native(tools, *args):
    return run([tools['compile'], *args])


def bun(tools, *args):
    return run(['bun', tools['compile-js'], *args])


def image_of(tools, path, output, lane):
    output.unlink(missing_ok=True)
    return (native if lane == 'native' else bun)(tools, PROFILE, path, output)


def source_case(tools, expectations, path):
    entry = expectations['sources'][path]
    out = BUILD / 'images' / (path.replace('/', '__') + '.kimg')
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = {}
    for lane in ('native', 'bun'):
        result = image_of(tools, ROOT / path, out.with_suffix(f'.{lane}.kimg'), lane)
        target = out.with_suffix(f'.{lane}.kimg')
        if 'image' in entry:
            data = target.read_bytes() if target.exists() else b''
            require(result['exit'] == 0 and result['stdout'] == f'Built\t{len(data)}\n'.encode() and result['stderr'] == b'',
                    (path, lane, shown(result)))
            require(sha(data) == entry['image']['sha256'] and len(data) == entry['image']['bytes'],
                    (path, lane, 'image bytes differ from the frozen reference'))
            seen[lane] = data
        else:
            want = entry['check']
            require(result['exit'] == want['exit'] and result['stderr'].decode() == want['stderr'] and result['stdout'] == b''
                    and not target.exists(), (path, lane, shown(result), want))
            seen[lane] = None
    require(seen['native'] == seen['bun'], (path, 'native and Bun images differ'))
    if seen['native'] is not None:
        plan = codec.decode(seen['native'], reference.DIGEST)
        require(codec.validate(plan, reference.REGISTRY) == [], (path, 'the codec refuses the image'))
        require(codec.encode(plan, reference.DIGEST) == seen['native'], (path, 'the image is not canonical'))
        out.write_bytes(seen['native'])
    return path


# ---------------------------------------------------------------- goldens under the reference evaluation

def golden_case(expectations, vm_expected, path):
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
    return out


def refusal_case(tools, name, data, message):
    path = BUILD / 'crafted' / f'{name}.kimg'
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(data)
    for lane, command in (('native', [tools['image']]), ('bun', ['bun', tools['image-js']])):
        result = run([*command, 'decode', path])
        require(result['stdout'] == b'' and result['stderr'].decode() == message + '\n'
                and result['exit'] == (4 if message.startswith('Exhausted') else 5), (name, lane, shown(result)))
    return name


# ---------------------------------------------------------------- the profile: budgets, caps, outputs

def profile_controls(tools, expectations, spec) -> list:
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
        ('characters-at-budget', [PROFILE, tiny, out, str(len(text)), '512', '512', '1048576', '16777216'], 0, '', f'Built\t{expectations["sources"][spec["character_cap"]["book"]]["image"]["bytes"]}'),
        ('characters-over-budget', [PROFILE, tiny, out, str(len(text) - 1), '512', '512', '1048576', '16777216'], 4, None, ''),
        ('characters-at-maximum', [PROFILE, at_ceiling, out, str(ceiling), '512', '512', '1048576', '16777216'], 0, '', f'Built\t{expectations["sources"][spec["character_cap"]["book"]]["image"]["bytes"]}'),
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
        want = expectations['sources'][spec['character_cap']['book']]['image']
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
    return record


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


# ---------------------------------------------------------------- mutants of src/image.bend

# (name, [(old, new)], driver, witnesses). A driver is `compile` (witness: a source), `recode` (a
# committed image) or `refuse` (a crafted image), or `writes` (the synthetic book).
MUTANTS = [
    ('wrong-construct-tag', [('placed => counted(placed,4,type_id,tag))', 'placed => counted(placed,4,type_id,U32.add(tag,1)))')],
     'compile', ['vm/golden/construct.bend']),
    ('swapped-let-fields', [('pushed(state,7,type_id,[slot,initial,result])', 'pushed(state,7,type_id,[initial,slot,result])')],
     'compile', ['vm/golden/let.bend']),
    ('let-typed-by-value', [('Lowered{Con{initial,Nil{}},Nil{},+a} Lowered{Con{+result,Nil{}},Nil{},+b}:\n      Done{one(Let{type_of(result),slot,initial,result},max_depth(a,b))}',
                             'Lowered{Con{+initial,Nil{}},Nil{},+a} Lowered{Con{+result,Nil{}},Nil{},+b}:\n      Done{one(Let{type_of(initial),slot,initial,result},max_depth(a,b))}')],
     'compile', ['tests/compiler-image/witnesses/let-changes-type.bend']),
    ('erased-operand-kept', [('S.choose(Result<S.Error,Lowered>,U32.is_eq(q,0),u => lower(n,Operands{tail,rest}', 'S.choose(Result<S.Error,Lowered>,U32.is_eq(q,4294967295),u => lower(n,Operands{tail,rest}')],
     'compile', ['vm/golden/erased-argument.bend', 'vm/golden/erased-construct.bend']),
    ('erased-constructor-not-a-value', [('case Lowered{Nil{},rows,deepest}: Done{one(Value{type_id,tag},deepest)}', 'case Lowered{Nil{},rows,deepest}: Done{one(Construct{type_id,tag,Nil{}},deepest)}')],
     'compile', ['tests/compiler-fields/fixtures/all-erased-return.bend']),
    ('arms-not-in-tag-order', [('S.choose(Maybe<&2,C.Term>,U32.is_eq(pattern,tag),u => Some{head}', 'S.choose(Maybe<&2,C.Term>,True{},u => Some{head}')],
     'compile', ['tests/compiler-image/witnesses/reordered-arms.bend']),
    ('slots-not-maximal', [('Bool.pick(U32,U32.is_ge(a,b),a,b)', 'Bool.pick(U32,U32.is_ge(a,b),b,a)')],
     'compile', ['tests/compiler-image/witnesses/many-slots.bend', 'vm/golden/recursion-map.bend']),
    ('names-not-shared', [('S.choose(Maybe<&2,U32>,String.eq(head,text),u => Some{top}', 'S.choose(Maybe<&2,U32>,Bool.and(False{},String.eq(head,text)),u => Some{top}')],
     'compile', ['tests/compiler-image/witnesses/shared-name.bend', 'vm/golden/unpack.bend']),
    ('section-count-off-by-one', [('Con{[count_records(rows,0)],List.append(&2,List<&2,U32>,rows,tail)}', 'Con{[U32.add(1,count_records(rows,0))],List.append(&2,List<&2,U32>,rows,tail)}')],
     'compile', ['vm/golden/unpack.bend']),
    ('node-offsets-shifted', [('Nodes{Nil{},U32.add(off_nodes,1),Nil{},0,0,0}', 'Nodes{Nil{},off_nodes,Nil{},0,0,0}')],
     'compile', ['vm/golden/unpack.bend']),
    ('digest-word', [('[967372322,1597628945,', '[967372323,1597628945,')], 'compile', ['vm/golden/let.bend']),
    ('constant-dropped', [('    case Con{head,tail}: constant_records(tail,Con{constant_record(head),acc})', '    case Con{head,tail}: constant_records(tail,acc)')],
     'recode', ['vm/golden/default-hit.kimg', 'vm/golden/string-append.kimg']),
    ('key-row-swapped', [('Con{key,Con{at,Nil{}}}),state}', 'Con{at,Con{key,Nil{}}}),state}')], 'recode', ['vm/golden/default-hit.kimg']),
    ('closure-sites-not-numbered', [('pushed(Nodes{records,next,pool,pooled,U32.add(sites,1),nodes},10,type_id,Con{sites,', 'pushed(Nodes{records,next,pool,pooled,U32.add(sites,1),nodes},10,type_id,Con{0,')],
     'recode', ['vm/golden/closure-nested.kimg']),
    ('decode-default-count', [('Bool.pick(U32,U32.is_eq(default,none()),0,1)', 'Bool.pick(U32,U32.is_eq(default,none()),1,0)')],
     'recode', ['vm/golden/recursion-map.kimg', 'vm/golden/default-hit.kimg']),
    ('decode-case-key-unchecked', [('Bool.and(U32.is_eq(at,w),U32.is_eq(k,key))', 'U32.is_eq(at,w)')], 'refuse', ['case-key']),
    ('decode-function-root-unchecked', [('S.choose(Result<S.Error,List<&2,Function>>,U32.is_eq(at,root),u =>', 'S.choose(Result<S.Error,List<&2,Function>>,True{},u =>')], 'refuse', ['function-root']),
    ('decode-digest-unchecked', [('same_words([d0,d1,d2,d3,d4,d5,d6,d7],digest())', 'True{}')], 'refuse', ['registry-digest']),
    ('unchunked-write', [('def chunk_steps() -> Nat:\n  16384n', 'def chunk_steps() -> Nat:\n  100000000n')], 'writes', ['synthetic']),
]

# The exhaustive match over C.Term: deleting any of its eight forms must fail the seed's own check.
FORMS = ('Value', 'Construct', 'Reference', 'Application', 'Let', 'Case', 'Branch', 'Sequence')


def mutant_tree(name, replacements):
    tree = BUILD / 'mutants' / name
    if tree.exists():
        shutil.rmtree(tree)
    (tree / 'src').mkdir(parents=True)
    (tree / 'tests/compiler-image').mkdir(parents=True)
    for source in (ROOT / 'src').glob('*.bend'):
        shutil.copy2(source, tree / 'src' / source.name)
    shutil.copy2(HERE / 'image-cli.bend', tree / 'tests/compiler-image/image-cli.bend')
    target = tree / 'src/image.bend'
    text = target.read_text()
    for old, new in replacements:
        require(text.count(old) == 1, (name, 'the mutation site must be unique', old[:60]))
        text = text.replace(old, new)
    target.write_text(text)
    return tree


def mutant_case(expectations, crafted_images, item):
    name, replacements, driver, witnesses = item
    tree = mutant_tree(name, replacements)
    checked = run([SEED, tree / 'src/image.bend', '--check-only'], 300)
    require(checked['exit'] == 0 and checked['stdout'].strip() == b'All terms check.', (name, 'a mutant must type-check', shown(checked)))
    wanted = {'compile': ('compile-cli', 'compile'), 'recode': ('image-cli', 'image'), 'refuse': ('image-cli', 'image'),
              'writes': ('compile-cli', 'compile')}[driver]
    entry = tree / ('src/compile-cli.bend' if wanted[0] == 'compile-cli' else 'tests/compiler-image/image-cli.bend')
    binary = tree / wanted[1]
    build(entry, binary)
    outcomes = []
    for witness in witnesses:
        if driver == 'compile':
            out = tree / 'witness.kimg'
            out.unlink(missing_ok=True)
            result = run([binary, PROFILE, ROOT / witness, out])
            good = expectations['sources'][witness]['image']['sha256']
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
        else:
            sample = BUILD / 'synthetic.bend'
            out = tree / 'witness.kimg'
            shim = BUILD / 'writes.dylib'
            result, writes = write_log([binary], sample, out, ['1048576', '4096', '4096', '1048576', '16777216'],
                                       {'DYLD_INSERT_LIBRARIES': str(shim)})
            killed = not (len(writes) >= 2 and max(n for _, n in writes) <= 65536)
        require(result['exit'] is not None and result['exit'] >= 0, (name, witness, 'a mutant crashed instead of misbehaving', shown(result)))
        require(killed, (name, witness, 'mutant survived', shown(result)))
        outcomes.append({'witness': witness, 'exit': result['exit'], 'outcome': 'semantic-kill'})
    # The laws are a second, independent way to kill it: does the seed's checker still accept the proofs?
    proved = run([SEED, tree / 'src/image-PROOF.bend'], 300)
    return {'name': name, 'driver': driver, 'replacements': len(replacements), 'witnesses': outcomes,
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
    require(result['exit'] != 0 and b'All terms check.' not in result['stdout'], (form, 'a missing arm must fail the check', shown(result)))
    return form


# ---------------------------------------------------------------- the proofs

def proof() -> dict:
    result = run([SEED, ROOT / 'src/image-PROOF.bend'], 300)
    require(result['exit'] == 0 and result['stdout'].strip() == b'All terms check.', ('proof', shown(result)))
    laws = (ROOT / 'src/image-LAWS.bend').read_text().count('\nlaw ')
    for entry in ('src/image.bend', 'src/compile-cli.bend', 'tests/compiler-image/image-cli.bend'):
        checked = run([SEED, ROOT / entry, '--check-only'], 300)
        require(checked['exit'] == 0 and checked['stdout'].strip() == b'All terms check.', (entry, shown(checked)))
    return {'laws': laws}


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

        # The reference is recomputed and must equal the file frozen before implementation.
        recomputed = freeze.document(check_cli)
        require(recomputed == frozen, 'expectations.json drifted from the independent reference')
        table = frozen['sources']
        record['sources'] = {'frozen': len(table), 'accepted': sum('image' in e for e in table.values())}
        pmap(lambda p: source_case(tools, frozen, p), sorted(table))
        goldens = sorted(p for p, e in table.items() if e.get('golden'))
        record['goldens'] = pmap(lambda p: golden_case(frozen, vm_expected, p), goldens)

        images = sorted((BUILD / 'images').glob('*.kimg'))
        images = [p for p in images if p.name.count('.') == 2 and 'native' not in p.name and 'bun' not in p.name]
        accepted = [BUILD / 'images' / (p.replace('/', '__') + '.kimg') for p, e in table.items() if 'image' in e]
        committed = sorted((ROOT / 'vm/golden').glob('*.kimg'))
        codec_inputs = committed + accepted
        record['codec'] = {'images': len(codec_inputs), 'golden': len(committed), 'compiled': len(accepted)}
        pmap(lambda p: codec_case(tools, p), codec_inputs)
        refusals = crafted()
        crafted_images = {name: (data, message) for name, data, message in refusals}
        record['refusals'] = pmap(lambda r: refusal_case(tools, *r), refusals)

        record['default_profile_modules'] = default_hashes(tools, frozen)
        record['profile'] = profile_controls(tools, frozen, frozen)
        record['synthetic'] = chunk_evidence(tools, frozen['synthetic'])
        record['synthetic_plan'] = deep_reference(frozen)
        record['exhaustive'] = pmap(exhaustive_case, FORMS)
        record['mutants'] = pmap(lambda m: mutant_case(frozen, crafted_images, m), MUTANTS)
        require(all(digest_inputs()[p] == h for p, h in record['inputs'].items()), 'inputs changed during the gate')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2, default=str) + '\n')
    print(f"Image gate passed: {record['sources']['frozen']} frozen sources ({record['sources']['accepted']} encoded and matched "
          f"to the independent reference, the rest answering as check-cli does), {len(record['goldens'])} golden images "
          f"byte-identical and evaluated, {record['codec']['images']} images through the Bend codec in 2 lanes, "
          f"{len(record['refusals'])} decoder refusals, {record['default_profile_modules']} default module hashes unchanged, "
          f"{len(record['profile'])} profile controls, synthetic {record['synthetic']['native']['bytes']}-byte image in "
          f"{record['synthetic']['native']['writes']} chunked writes, {len(record['exhaustive'])} exhaustiveness controls, "
          f"{len(record['mutants'])} mutants killed ({sum(m['laws_refuse'] for m in record['mutants'])} also refused by the laws); "
          f"{record['proof']['laws']} checked laws. {RECEIPT}")


if __name__ == '__main__':
    main()
