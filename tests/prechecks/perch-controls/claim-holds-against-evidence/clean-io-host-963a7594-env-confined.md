<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=io-host; head=963a7594af1b; base=ec4374702887; builder=scripts/prechecks/packets@3a2ef420dff1; sources: docs/compiler-campaign/IO-ABI.md@963a7594 sha256=0c5d8271a8fc0fcd2f969cb27ed5c1c922f675101853557e8a2d3377a06234c3; scripts/run-wasm-io.mjs@963a7594 sha256=4c0e1bc92c126289be756ee1c4b9543cea2bbda0ae0162b49d5b51d55ecae675; tests/compiler-io/host-check.py@963a7594 sha256=21df9ba4a3930d6ee755a1467240623a4ca16452e884a9d0aee7312d905cf746; tests/compiler-io/host/review.py@963a7594 sha256=415d372d28ae62cc8652c9db0e578896afe134015fb17d27bc3566d73622e72a -->
# Claim
docs/compiler-campaign/IO-ABI.md:146-148 (section: Sandbox and classification) - verbatim text:

> The host resolves one existing directory as its root. All guest paths must be
> relative, contain no `..` component, and contain no `.env` or `.env.*`
> component under a case-insensitive comparison.

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
`scripts/run-wasm-io.mjs:11-15` (added)
   11  const errors = Object.freeze({
   12    ENOENT: [2, 'No such file or directory'], EBADF: [9, 'Bad file descriptor'],
   13    ENOTDIR: [20, 'Not a directory'], EISDIR: [21, 'Is a directory'],
   14    EINVAL: [22, 'Invalid argument'], EILSEQ: [92, 'Illegal byte sequence'],
   15  });

`scripts/run-wasm-io.mjs:110-318` (added)
  110  export async function runIO({modulePath, sandbox, args = []}) {
  111    let instance, allocating = false, nextHandle = 1, root;
  112    // A guest may catch a thrown Halt or Fault (Wasm exception handling); termination stays sticky.
  113    let stopped = null;
  114    const handles = new Map();
  115    function ready() {
  116      if (!instance || allocating) bad('abi', 'effect outside guest invocation');
  117    }
  118    function memory() {
  119      ready();
  120      return instance.exports.memory;
  121    }
  122    function range(pointer, length) {
  123      const p = pointer >>> 0, n = length >>> 0, buffer = memory().buffer;
  124      if (n > buffer.byteLength || p > buffer.byteLength - n) bad('abi', 'range out of bounds');
  125      return Buffer.from(buffer, p, n);
  126    }
  127    function resultRange(out) {
  128      if ((out & 3) !== 0) bad('abi', 'unaligned result');
  129      range(out, 16);
  130    }
  131    function text(p, n) {
  132      try { return strictDecoder.decode(range(p, n)); }
  133      catch (error) { if (error instanceof Fault) throw error; bad('abi', 'non-scalar UTF-8'); }
  134    }
  135    function allocate(bytes) {
  136      if (bytes.length > MAX_TRANSFER) exhausted('memory');
  137      allocating = true;
  138      let p;
  139      try { p = instance.exports.knot_alloc(bytes.length); }
  140      finally { allocating = false; }
  141      if (stopped) throw stopped;
  142      range(p, bytes.length).set(bytes);
  143      return p >>> 0;
  144    }
  145    function result(out, errno = 0, value = 0, data = Buffer.alloc(0)) {
  146      const p = data.length ? allocate(data) : 0;
  147      // Allocation may grow memory and detach prior views.
  148      const words = range(out, 16);
  149      [errno, value, p, data.length].forEach((v, i) => words.writeUInt32LE(v >>> 0, i * 4));
  150    }
  151    function fail(out, code, handle = 0) {
  152      const pair = errors[code];
  153      if (!pair) bad('os', 'unmodeled OS failure');
  154      result(out, pair[0], handle, Buffer.from(pair[1]));
  155    }
  156    function handle(id) {
  157      const h = handles.get(id >>> 0);
  158      if (!h) bad('handle', 'unknown or closed handle');
  159      return h;
  160    }
  161    function confined(name) {
  162      const parts = name.split('/');
  163      if (path.isAbsolute(name) || parts.includes('..') ||
  164          parts.some(p => {
  165            const q = p.toLowerCase();
  166            return q === '.env' || q.startsWith('.env.');
  167          })) bad('sandbox', 'path refused');
  168      let current = root;
  169      for (const part of parts.filter(p => p && p !== '.')) {
  170        current = path.join(current, part);
  171        try {
  172          const st = fs.lstatSync(current);
  173          if (st.isSymbolicLink() || (!st.isDirectory() && (!st.isFile() || st.nlink !== 1)))
  174            bad('sandbox', 'link or special file refused');
  175        } catch (error) {
  176          if (error.code === 'ENOENT' || error.code === 'ENOTDIR') break;
  177          throw error;
  178        }
  179      }
  180      return root + '/' + name;
  181    }
  182    const io = {
  183      args(out) {
  184        resultRange(out);
  185        const strings = args.map(a => {
  186          if (typeof a !== 'string' && !Buffer.isBuffer(a) && !(a instanceof Uint8Array))
  187            bad('arguments', 'expected strings or raw bytes');
  188          const bytes = normalize(typeof a === 'string' ? Buffer.from(a) : a);
  189          return [allocate(bytes), bytes.length];
  190        });
  191        const table = Buffer.alloc(strings.length * 8);
  192        strings.forEach(([p, n], i) => { table.writeUInt32LE(p, i * 8); table.writeUInt32LE(n, i * 8 + 4); });
  193        result(out, 0, strings.length, table);
  194      },
  195      print(p, n) {
  196        const bytes = Buffer.from(text(p, n));
  197        writeAll(1, Buffer.concat([bytes, Buffer.from('\n')]));
  198      },
  199      die(code, p, n) {
  200        writeAll(2, Buffer.from(text(p, n) + '\n'));
  201        throw new Halt((code >>> 0) % 256);
  202      },
  203      open(p, n, m, count, out) {
  204        resultRange(out);
  205        const name = text(p, n);
  206        if (name.includes('\0')) return fail(out, 'EILSEQ');
  207        const mode = text(m, count);
  208        if (!['r', 'w', 'a'].includes(mode)) return fail(out, 'EINVAL');
  209        if (name === '') return fail(out, 'ENOENT');
  210        const target = confined(name);
  211        let fd;
  212        try {
  213          const c = fs.constants;
  214          const flags = {r: c.O_RDONLY, w: c.O_WRONLY | c.O_CREAT | c.O_TRUNC,
  215            a: c.O_WRONLY | c.O_CREAT | c.O_APPEND};
  216          fd = fs.openSync(target, flags[mode] | c.O_NOFOLLOW, 0o644);
  217          const stat = fs.fstatSync(fd);
  218          if (!stat.isDirectory() && (!stat.isFile() || stat.nlink !== 1)) bad('sandbox', 'special file refused');
  219          if (nextHandle > 0x7fffffff) exhausted('handles');
  220          const id = nextHandle++;
  221          handles.set(id, {fd, mode, directory: stat.isDirectory(), position: 0});
  222          fd = undefined;
  223          result(out, 0, id);
  224        } catch (error) {
  225          if (fd !== undefined) fs.closeSync(fd);
  226          if (error instanceof Fault) throw error;
  227          fail(out, error.code);
  228        }
  229      },
  230      read(id, maximum, out) {
  231        resultRange(out);
  232        const h = handle(id);
  233        if (h.mode !== 'r') return fail(out, 'EBADF', id);
  234        if (h.directory) return fail(out, 'EISDIR', id);
  235        let bytes;
  236        try {
  237          const remaining = Math.max(0, fs.fstatSync(h.fd).size - h.position);
  238          const size = Math.min(maximum >>> 0, remaining);
  239          if (size > MAX_TRANSFER) exhausted('memory');
  240          bytes = Buffer.alloc(size);
  241          const count = fs.readSync(h.fd, bytes, 0, size, null);
  242          h.position += count;
  243          bytes = normalize(bytes.subarray(0, count));
  244        } catch (error) {
  245          if (error instanceof Fault) throw error;
  246          return fail(out, error.code, id);
  247        }
  248        result(out, 0, id, bytes);
  249      },
  250      write_bytes(id, p, n, invalid, out) {
  251        resultRange(out);
  252        const h = handle(id);
  253        // The guest scans all U32 elements before narrowing; invalid is its OR of high bits.
  254        if (invalid !== 0) return fail(out, 'EINVAL', id);
  255        const bytes = range(p, n);
  256        if (bytes.length > MAX_TRANSFER) exhausted('memory');
  257        if (h.mode === 'r' && bytes.length > 0) return fail(out, 'EBADF', id);
  258        try { writeAll(h.fd, bytes); }
  259        catch (error) {
  260          if (error instanceof Fault) throw error;
  261          return fail(out, error.code, id);
  262        }
  263        result(out, 0, id);
  264      },
  265      close(id) {
  266        ready();
  267        const h = handle(id);
  268        handles.delete(id >>> 0);
  269        try { fs.closeSync(h.fd); } catch { /* Base ignores close errors. */ }
  270      },
  271      exhausted(kind) {
  272        if (kind === 1) exhausted('steps');
  273        if (kind === 2) exhausted('memory');
  274        bad('abi', 'unknown exhaustion reason');
  275      },
  276    };
  277    try {
  278      root = fs.realpathSync(sandbox);
  279      if (!fs.statSync(root).isDirectory()) bad('sandbox', 'working directory required');
  280      let bytes;
  281      try { bytes = fs.readFileSync(modulePath); } catch { bad('module', 'module unreadable'); }
  282      if (!WebAssembly.validate(bytes)) bad('module', 'Wasm validation failed');
  283      abi(bytes);
  284      const module = await WebAssembly.compile(bytes);
  285      const sticky = f => (...values) => {
  286        if (stopped) throw stopped;
  287        try { return f(...values); }
  288        catch (error) { if (error instanceof Halt || error instanceof Fault) stopped = error; throw error; }
  289      };
  290      const imports = Object.fromEntries(Object.entries(io).map(([name, f]) => [name, sticky(f)]));
  291      instance = await WebAssembly.instantiate(module, {knot_io: imports});
  292      instance.exports.knot_main();
  293      if (stopped) throw stopped;
  294      return {status: 'Completed', exit: 0};
  295    } catch (error) {
  296      if (error instanceof Halt) return {status: 'Halted', exit: error.exit};
  297      if (error instanceof RangeError && /maximum call stack size exceeded/i.test(error.message))
  298        error = new Fault('Exhausted', 'call-stack', 4);
  299      if (!(error instanceof Fault)) error = new Fault('HostFailure',
  300        error instanceof WebAssembly.RuntimeError ? 'trap' : 'host', 5);
  301      writeAll(2, Buffer.from(`${error.status}\tio\t${error.code}\n`));
  302      return {status: error.status, code: error.code, exit: error.exit};
  303    } finally {
  304      for (const h of handles.values()) { try { fs.closeSync(h.fd); } catch {} }
  305    }
  306  }
  307  
  308  if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  309    process.exitCode = 5;
  310    const [modulePath, sandbox, separator, ...args] = process.argv.slice(2);
  311    if (!modulePath || !sandbox || (separator !== undefined && separator !== '--')) {
  312      fs.writeSync(2, 'HostFailure\tio\tusage: module sandbox [-- arguments...]\n');
  313    } else {
  314      try { process.exitCode = (await runIO({modulePath, sandbox, args})).exit; }
  315      catch { fs.writeSync(2, 'HostFailure\tio\thost\n'); }
  316    }
  317  }
  318  

`tests/compiler-io/host-check.py:46-52` (added)
   46  def fresh(name):
   47      directory = WORK / name
   48      assert directory.is_relative_to(WORK) and directory != WORK
   49      if directory.exists():
   50          shutil.rmtree(directory)
   51      directory.mkdir(parents=True)
   52      return directory

`tests/compiler-io/host-check.py:68-87` (added)
   68  def observe(name, run, module, host=HOST, cli=False):
   69      directory = fresh('runs/' + name + '/' + run['name'])
   70      box = directory / 'sandbox'
   71      box.mkdir()
   72      for dest, source in run['inputs'].items():
   73          shutil.copyfile(frozen.INPUTS / source, box / dest)
   74      if cli:
   75          argv = [a if isinstance(a, str) else bytes.fromhex(a['hex']) for a in run['argv']]
   76          r = command(['node', str(host), str(module), str(box), '--', *argv])
   77          outcome = None
   78      else:
   79          r, outcome = invoke(module, box, run['argv'], run['streams'] == 'merged', host)
   80      record = {'exit': r.returncode}
   81      if run['streams'] == 'merged':
   82          record['output'] = frozen.blob(r.stdout, frozen.STREAM_LIMIT)
   83      else:
   84          record['stdout'] = frozen.blob(r.stdout, frozen.STREAM_LIMIT)
   85          record['stderr'] = frozen.blob(r.stderr, frozen.STREAM_LIMIT)
   86      record['files'] = frozen.snapshot(box, run['inputs'])
   87      return record, outcome

`tests/compiler-io/host/review.py:16-19` (added)
   16  def contents(box):
   17      paths = sorted(box.rglob('*'))
   18      return {'files': {p.relative_to(box).as_posix(): p.read_text() for p in paths if p.is_file()},
   19              'directories': [p.relative_to(box).as_posix() for p in paths if p.is_dir()]}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
