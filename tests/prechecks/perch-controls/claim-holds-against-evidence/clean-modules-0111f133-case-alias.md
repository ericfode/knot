<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=modules; head=0111f13352e0; base=aa2c86a9dab8; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/base-load-LAWS.bend@0111f133 sha256=bc474ba56a21d9bba54c413d6543325e6596f2ae7469b426adcf02af0810a009; src/base-load-PROOF.bend@0111f133 sha256=ee43281f8668b287cab6b7eb415f748533392fe98e40c30c94433529c55031df; src/host/path-identity.js@0111f133 sha256=6150ae6b016d20f2e380b6f50110e654509d5b1b822bce78c03b4c5c640d7ee2; src/imports.bend@0111f133 sha256=830dbdf122e0af757229052ae066c96f61da0167d13302f126cd95d850efb3e2; src/load-LAWS.bend@0111f133 sha256=933219d33bf7be3e99b4df26921be47b1e55c86e51fd1f9631dfa510400df4f1; src/load-PROOF.bend@0111f133 sha256=3438774c25a32823bbc162e8edde4419068830987aecf6c4fad2e3c81b5cd94e; src/load.bend@0111f133 sha256=07e57ed03bfb6019843f4bc9036ab11f9d926dc59c5c2a0ed6fc1274cc59be02; src/qualify-LAWS.bend@0111f133 sha256=f1aeafd31dc3a51fde89a007ea6275df6c13da6578a2577b89781e90023b2d51; tests/compiler-modules/README.md@0111f133 sha256=8994dce8823fa298a3779bb3faaa227355b473621b34df1c901d249fa1f397e2 -->
# Claim
tests/compiler-modules/README.md:60-61 (section: Independent verification) - verbatim text:

> The case-alias probe explicitly requires a
> case-insensitive filesystem.

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
`src/base-load-LAWS.bend:85-94` (added)
   85  law pending_work_requires_budget:
   86    for parser: Nat
   87    for name: String
   88    for tail: List<&2,String>
   89    for book: List<&2,B.Decl>
   90    for seen: List<&2,String>
   91    for items: List<&2,B.Selected>
   92    {B.visit(0n,parser,Con{name,tail},book,seen,items) ==
   93      Fail{S.Exhausted{"base-slice",S.At{0,0,0,0}}} : Result<S.Error,B.Slice>}
   94  

`src/base-load-PROOF.bend:22-22` (added)
   22  def L.pending_work_requires_budget(parser,name,tail,book,seen,items): {==}

`src/host/path-identity.js:2-35` (added)
    2  function knot_path_identity(path) {
    3    const bytes = io_bytes(path);
    4    if (bytes.includes(0)) return io_fail(process.platform === "darwin" ? 92 : 84);
    5    const fs = require("fs");
    6    // The compiler's path/source profile is ASCII. Buffer comparison also keeps
    7    // directory-entry case and normalization exact on insensitive filesystems.
    8    const parts = Buffer.from(bytes).toString("utf8").split("/");
    9    let current = path.startsWith("/") ? "/" : process.cwd();
   10    try {
   11      for (const part of parts) {
   12        if (part === "" || part === ".") continue;
   13        if (part === "..") {
   14          current = current.slice(0, current.lastIndexOf("/")) || "/";
   15          continue;
   16        }
   17        const next = current.replace(/\/$/, "") + "/" + part;
   18        const stat = fs.lstatSync(next);
   19        if (stat.isSymbolicLink()) return io_done(false);
   20        const exact = fs.readdirSync(current, { encoding: "buffer" })
   21          .some(name => Buffer.from(name).equals(Buffer.from(part)));
   22        if (!exact) return io_done(false);
   23        current = next;
   24      }
   25      return io_done(true);
   26    } catch (error) {
   27      if (error.code === "ENOENT" || error.code === "ENOTDIR") {
   28        return io_done(true);
   29      }
   30      return io_fail(typeof error.errno === "number" ? -error.errno : 5);
   31    }
   32  }
   33  
   34  io_eff(CID(inspect), knot_path_identity);
   35  

`src/imports.bend:4-6` (added)
    4  type Import is Data:
    5    Import{path: String, alias: String}
    6  

`src/imports.bend:153-167` (added)
  153  def import_words(parts: List<&2,String>, +at: S.At) -> Result<S.Error,Import>:
  154    match parts:
  155      case Con{word,Con{+path,Nil{}}}:
  156        S.choose(Result<S.Error,Import>,String.eq(path,"Base"),u => Done{Import{"Base",""}},u =>
  157          Fail{S.Invalid{"load","import-alias",at}})
  158      case Con{word,Con{+path,Con{+as,Con{+alias,Nil{}}}}}:
  159        S.choose(Result<S.Error,Import>,Bool.and(String.eq(as,"as"),plain(alias,False{})),u =>
  160        S.choose(Result<S.Error,Import>,String.contains(first(split(path,'/')),"@"),u =>
  161          Fail{S.Unsupported{"load","named-package",at}},u =>
  162        S.choose(Result<S.Error,Import>,String.starts_with(path,"/"),u =>
  163          Fail{S.Unsupported{"load","absolute-import",at}},u =>
  164        S.choose(Result<S.Error,Import>,valid(path),u => Done{Import{path,alias}},u =>
  165          Fail{S.Invalid{"load","import-path",at}}))),u => Fail{S.Invalid{"load","import-alias",at}})
  166      case _: Fail{S.Invalid{"load","import-syntax",at}}
  167  

`src/imports.bend:168-171` (added)
  168  def alias(item: Import) -> String:
  169    match item:
  170      case Import{path,name}: name
  171  

`src/imports.bend:172-178` (added)
  172  def push_import(result: Result<S.Error,Import>, +seen: List<&2,String>, next: Import -> Result<S.Error,Header>) -> Result<S.Error,Header>:
  173    match result:
  174      case Fail{error}: Fail{error}
  175      case Done{+item}:
  176        S.choose(Result<S.Error,Header>,Bool.and(Bool.not(String.eq(alias(item),"")),member(alias(item),seen)),u =>
  177          Fail{S.Invalid{"load","duplicate-alias",S.At{0,0,0,0}}},u => next(item))
  178  

`src/imports.bend:194-210` (added)
  194  def header_lines(lines: List<&2,String>, +open: Bool, +row: U32,
  195    +imports: List<&2,Import>, +seen: List<&2,String>, +body: List<&2,String>) -> Result<S.Error,Header>:
  196    match lines:
  197      case Nil{}: Done{Header{List.reverse(&2,Import,imports),body_lines(body)}}
  198      case Con{+line,+tail}:
  199        +clean = String.trim(first(split(line,'#')))
  200        +parts = words(clean,"",Nil{})
  201        +is_import = String.eq(first(parts),"import")
  202        S.choose(Result<S.Error,Header>,Bool.and(open,is_import),u =>
  203          push_import(import_words(parts,S.At{0,0,row,0}),seen,+item =>
  204            header_lines(tail,True{},U32.add(row,1),Con{item,imports},Con{alias(item),seen},Con{"",body})),u =>
  205        S.choose(Result<S.Error,Header>,Bool.and(Bool.not(open),is_import),u =>
  206          S.choose(Result<S.Error,Header>,foreign(parts),u =>
  207            Fail{S.Unsupported{"check","foreign-definition",S.At{0,0,row,0}}},u =>
  208            Fail{S.Invalid{"load","import-after-declaration",S.At{0,0,row,0}}}),u =>
  209          header_lines(tail,Bool.and(open,String.eq(clean,"")),U32.add(row,1),imports,seen,Con{line,body})))
  210  

`src/load-LAWS.bend:92-95` (added)
   92  law duplicate_alias_is_invalid:
   93    {I.header("import ./a.bend as A\nimport ./b.bend as A\n")
   94      == Fail{S.Invalid{"load","duplicate-alias",S.At{0,0,0,0}}} : Result<S.Error,I.Header>}
   95  

`src/load-PROOF.bend:46-48` (added)
   46  def L.duplicate_alias_is_invalid():
   47    {==}
   48  

`src/load.bend:21-26` (added)
   21  type Step is Data:
   22    Visit{path: String, namespace: String, entry: Bool}
   23    Imports{path: String, namespace: String, remaining: List<&2,I.Import>, aliases: List<&2,Q.Alias>, body: String}
   24    Source{path: String, namespace: String, result: Input}
   25    BaseSource{result: Input}
   26  

`src/load.bend:98-102` (added)
   98  def body(+characters: Nat, +depth: Nat, +namespace: String, +aliases: List<&2,Q.Alias>,
   99    +globals: Q.Symbols, text: String) -> Result<S.Error,S.Node>:
  100    S.bind(List<&2,S.Token>,S.Node,L.tokenize(characters,text),tokens =>
  101      S.bind(P.Parsed,S.Node,P.parse(depth,tokens),tree => Q.qualify(namespace,aliases,globals,parsed(tree))))
  102  

`src/load.bend:202-209` (added)
  202  def step_target(result: Result<S.Error,I.Target>, +alias: String, +path: String, +namespace: String,
  203    +remaining: List<&2,I.Import>, +aliases: List<&2,Q.Alias>, +text: String,
  204    tail: List<&2,Step>, state: State) -> Action:
  205    match result:
  206      case Fail{error}: Stopped{error}
  207      case Done{I.Target{target,+space}}:
  208        Advance{Con{Visit{target,space,False{}},Con{Imports{path,namespace,remaining,Con{Q.Alias{alias,space},aliases},text},tail}},state}
  209  

`src/load.bend:218-235` (added)
  218  def plan(tasks: List<&2,Step>, +state: State, +bundle: String, +characters: Nat, +depth: Nat) -> Action:
  219    match tasks:
  220      case Nil{}: stopped(finish(depth,state))
  221      case Con{Visit{+path,+namespace,+entry},+tail}:
  222        S.choose(Action,cyclic(path,state),u => Stopped{S.Invalid{"load","cycle",S.At{0,0,0,0}}},u =>
  223        S.choose(Action,known(path,state),u => Advance{tail,state},u =>
  224          Read{path,65537,Bool.not(entry),UserSource{path,namespace},tail,enter(path,state)}))
  225      case Con{Source{path,namespace,result},tail}: step_source(result,path,namespace,characters,tail,state)
  226      case Con{BaseSource{result},tail}: step_base(result,tail,state)
  227      case Con{Imports{+path,+namespace,Nil{},aliases,text},+tail}:
  228        step_body(body(characters,depth,namespace,aliases,base_names(state),text),path,state,tail)
  229      case Con{Imports{+path,+namespace,Con{I.Import{+target,+alias},+rest},+aliases,+text},+tail}:
  230        +resume : Step = Imports{path,namespace,rest,aliases,text}
  231        S.choose(Action,String.eq(target,"Base"),u =>
  232          S.choose(Action,has_base(state),u => Advance{Con{resume,tail},state},u =>
  233            Read{base_path(),131073,False{},PinnedBase{},Con{resume,tail},state}),u =>
  234          step_target(I.resolve(path,namespace,bundle,target),alias,path,namespace,rest,aliases,text,tail,state))
  235  

`src/qualify-LAWS.bend:10-16` (added)
   10  law empty_module:
   11    for namespace: String
   12    for aliases: List<&2,Q.Alias>
   13    for terms: List<&2,String>
   14    for constructors: List<&2,String>
   15    {Q.qualify(namespace,aliases,Q.Symbols{terms,constructors},S.Sequence{Nil{}}) == Done{S.Sequence{Nil{}}} : Result<S.Error,S.Node>}
   16  

`src/qualify-LAWS.bend:52-61` (added)
   52  law alias_expands_one_component:
   53    for +at: S.At
   54    {Q.qualify("",[Q.Alias{"L","lib/left"}],Q.Symbols{["lib/flag.Flag","lib/left.left"],Nil{}},S.Sequence{[
   55      S.Function{S.Token{"keep",at},[S.Parameter{S.Token{"x",at},1,S.Token{"L.F.Flag",at}}],
   56        S.Token{"L.F.Flag",at},S.Variable{S.Token{"x",at}}}]}) ==
   57      Done{S.Sequence{[
   58        S.Function{S.Token{"keep",at},[S.Parameter{S.Token{"x",at},1,S.Token{"lib/left.F.Flag",at}}],
   59          S.Token{"lib/left.F.Flag",at},S.Variable{S.Token{"x",at}}}]}}
   60      : Result<S.Error,S.Node>}
   61  

`src/qualify-LAWS.bend:62-68` (added)
   62  law alias_member_cannot_be_declared:
   63    for +at: S.At
   64    for body: S.Node
   65    {Q.qualify("m",[Q.Alias{"A","lib/a"}],Q.Symbols{Nil{},Nil{}},S.Sequence{[
   66      S.Function{S.Token{"A.keep",at},Nil{},S.Token{"Flag",at},body}]}) ==
   67      Fail{S.Invalid{"load","alias-member",at}} : Result<S.Error,S.Node>}
   68  

`src/qualify-PROOF.bend:10-10` (added)
   10  def L.alias_expands_one_component(at): {==}

`tests/compiler-modules/check.py:170-206` (added)
  170  def review_reference(manifest):
  171      supplement = json.loads((HERE / 'review-round2.json').read_text())
  172      require(supplement['seed'] == manifest['seed'], 'Review seed identity differs')
  173      source = HERE / 'review-round2'
  174      files = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
  175      require(files == set(supplement['sources']), 'Review source set differs from freeze')
  176      require(all(digest(source / name) == identity for name, identity in supplement['sources'].items()),
  177              'Review fixture changed after expectation freeze')
  178      target = BUILD / 'review-round2'
  179      shutil.copytree(source, target, dirs_exist_ok=True)
  180      for name, relative in supplement['symlinks'].items():
  181          link = target / name
  182          if link.is_symlink():
  183              link.unlink()
  184          require(not link.exists(), ('Review link path is occupied', name))
  185          link.symlink_to(relative, target_is_directory=True)
  186      case = supplement['case_alias']
  187      require((target / case['alias']).exists()
  188              and os.path.samefile(target / case['canonical'], target / case['alias']),
  189              'Review case-alias probe requires a case-insensitive filesystem')
  190      records, fixtures = [], []
  191      for frozen in supplement['fixtures']:
  192          fixture = json.loads(json.dumps(frozen))
  193          fixture['file'] = os.path.relpath(target / frozen['file'], HERE)
  194          if 'loaded_files' in fixture:
  195              fixture['loaded_files'] = [os.path.relpath(target / name, HERE)
  196                                         for name in fixture['loaded_files']]
  197          for call in fixture['calls']:
  198              entry = target / call['run']
  199              result = run([*SEED, entry])
  200              normalized = {**result, **{key: result[key].replace(str(ROOT), '<ROOT>')
  201                                        for key in ('stdout', 'stderr')}}
  202              require(observation(normalized) == observation(call), (call, result))
  203              records.append({'name': fixture['name'], 'run': call['run'], 'result': result})
  204              call['run'] = os.path.relpath(entry, HERE)
  205          fixtures.append(fixture)
  206      return fixtures, records
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
