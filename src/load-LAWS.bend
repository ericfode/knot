import Base
import ./syntax.bend as S
import ./parse.bend as P
import ./imports.bend as I
import ./qualify.bend as Q
import ./base-load.bend as B
import ./load.bend as L
import ./path-host.bend as F

# Transition and path boundaries. These do not prove whole-book confluence.
law completed_module_is_not_read_again:
  for +tail: List<&2,L.Step>
  for +tree: List<&2,S.Node>
  for +symbols: Q.Symbols
  for +base: List<&2,B.Decl>
  for +loaded: Bool
  for bundle: String
  for characters: Nat
  for depth: Nat
  {L.plan(Con{L.Visit{"lib/shared.bend","lib/shared",False{}},tail},
    L.State{["lib/shared.bend"],Nil{},tree,symbols,base,loaded},bundle,characters,depth)
    == L.Advance{tail,L.State{["lib/shared.bend"],Nil{},tree,symbols,base,loaded}} : L.Action}

law active_module_is_a_cycle:
  for done: List<&2,String>
  for active: List<&2,String>
  for tree: List<&2,S.Node>
  for symbols: Q.Symbols
  for base: List<&2,B.Decl>
  for loaded: Bool
  for tail: List<&2,L.Step>
  {L.plan(Con{L.Visit{"a.bend","a",False{}},tail},
    L.State{done,Con{"a.bend",active},tree,symbols,base,loaded},"bundle",65536n,512n)
    == L.Stopped{S.Invalid{"load","cycle",S.At{0,0,0,0}}} : L.Action}

law source_failure_is_preserved:
  for +error: S.Error
  for path: String
  for namespace: String
  for characters: Nat
  for tail: List<&2,L.Step>
  for state: L.State
  {L.step_source(L.ReadError{error},path,namespace,characters,tail,state) == L.Stopped{error} : L.Action}

law raw_input_is_bounded_before_header_removal:
  for path: String
  for namespace: String
  for tail: List<&2,L.Step>
  for state: L.State
  {L.step_source(L.Contents{"import Base\n"},path,namespace,0n,tail,state)
    == L.Stopped{S.Exhausted{"lex",S.At{0,0,0,0}}} : L.Action}

law budget_counts_utf8_bytes:
  {(L.within("\u{E9}",1n),L.within("\u{E9}",2n),L.within("\u{1F600}",3n),L.within("\u{1F600}",4n))
    == (False{},True{},False{},True{}) : Bool & Bool & Bool & Bool}

law multibyte_source_is_bounded_by_bytes:
  for path: String
  for namespace: String
  for tail: List<&2,L.Step>
  for state: L.State
  {L.step_source(L.Contents{"import Base # \u{E9}\n"},path,namespace,16n,tail,state)
    == L.Stopped{S.Exhausted{"lex",S.At{0,0,0,0}}} : L.Action}

law empty_namespace_is_entry_relative:
  {I.resolve("source/main.bend","","bundle","./lib/flag.bend")
    == Done{I.Target{"source/lib/flag.bend","lib/flag"}} : Result<S.Error,I.Target>}

law nested_namespace_is_importer_relative:
  {I.resolve("source/lib/deep/twig.bend","lib/deep/twig","bundle","../flag.bend")
    == Done{I.Target{"source/lib/flag.bend","lib/flag"}} : Result<S.Error,I.Target>}

law parent_paths_have_one_identity:
  {I.resolve("source/main.bend","","bundle","../source/lib/flag.bend")
    == I.resolve("source/main.bend","","bundle","./lib/flag.bend") : Result<S.Error,I.Target>}

law hash_paths_use_the_bundle:
  {I.resolve("source/main.bend","","bundle","0xab/flag.bend")
    == Done{I.Target{"bundle/0xab/flag.bend","0xab/flag"}} : Result<S.Error,I.Target>}

law package_relative_paths_keep_identity:
  {I.resolve("bundle/0xab/board.bend","0xab/board","bundle","./mark.bend")
    == Done{I.Target{"bundle/0xab/mark.bend","0xab/mark"}} : Result<S.Error,I.Target>}

law bundle_identity_is_independent_of_import_spelling:
  {I.resolve("bundle/0xab/main.bend","","bundle","./mark.bend")
    == I.resolve("bundle/0xab/main.bend","","bundle","0xab/mark.bend") : Result<S.Error,I.Target>}

law absolute_import_is_unsupported:
  {I.header("import /lib/flag.bend as F\n")
    == Fail{S.Unsupported{"load","absolute-import",S.At{0,0,1,0}}} : Result<S.Error,I.Header>}

law mixed_path_roots_are_unsupported:
  {L.start("/source/main.bend","bundle")
    == L.Stopped{S.Unsupported{"load","mixed-path-roots",S.At{0,0,0,0}}} : L.Action}

law climbing_paths_have_no_identity:
  {(I.resolve("app/two.bend","","lib","../../w/app/m/flag.bend"),
    L.start("../w/app/ok.bend","lib"),L.start("app/plain.bend","../w/lib")) ==
    (Fail{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}},
     L.Stopped{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}},
     L.Stopped{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}})
    : Result<S.Error,I.Target> & L.Action & L.Action}

law working_directory_bundle_contains_local_paths:
  {I.resolve("main.bend","",I.normalize("."),"./extra/flag.bend")
    == Fail{S.Invalid{"load","import-path",S.At{0,0,0,0}}} : Result<S.Error,I.Target>}

law package_escape_is_invalid:
  {I.resolve("bundle/0xab/board.bend","0xab/board","bundle","../outside.bend")
    == Fail{S.Invalid{"load","package-escape",S.At{0,0,0,0}}} : Result<S.Error,I.Target>}

law namespace_is_lexically_canonical:
  {I.normalize("source/./lib/../lib/flag.bend") == "source/lib/flag.bend" : String}

law glued_hash_stays_in_the_path:
  {(I.header("import Base#c\n"),I.header("import Base #c\n")) ==
    (Fail{S.Invalid{"load","import-alias",S.At{0,0,1,0}}},Done{I.Header{[I.Import{"Base",""}],"\n"}})
    : Result<S.Error,I.Header> & Result<S.Error,I.Header>}

law glued_hash_ends_an_alias:
  {I.header("import ./a.bend as A#x y\n") == Done{I.Header{[I.Import{"./a.bend","A"}],"\n"}}
    : Result<S.Error,I.Header>}

law header_separator_outside_ascii_is_unsupported:
  {(I.header("\u{FEFF}import ./a.bend as A\nimport ./b.bend as B\n"),
    I.header("import\u{C}./a.bend as A\nimport ./b.bend as B\n")) ==
    (Fail{S.Unsupported{"load","header-character",S.At{0,0,1,0}}},
     Fail{S.Unsupported{"load","header-character",S.At{0,0,1,0}}})
    : Result<S.Error,I.Header> & Result<S.Error,I.Header>}

law duplicate_alias_is_invalid:
  {I.header("import ./a.bend as A\nimport ./b.bend as A\n")
    == Fail{S.Invalid{"load","duplicate-alias",S.At{0,0,0,0}}} : Result<S.Error,I.Header>}

law parent_import_is_recognized_without_loading:
  for +at: S.At
  for +rest: List<&2,S.Token>
  {P.run(1n,P.Header{S.Token{"import",at},S.Token{"..",at}},Con{S.Token{"/",at},rest})
    == Fail{S.Unsupported{"parse","import",at}} : Result<S.Error,P.Parsed>}

law base_term_collision_is_invalid:
  {L.install_base("def Bool.not(b: Bool) -> Bool:\n  b\n",
    L.State{Nil{},Nil{},Nil{},Q.Symbols{["Bool.not"],Nil{}},Nil{},False{}}) ==
    Fail{S.Invalid{"load","duplicate-global",S.At{0,0,0,0}}} : Result<S.Error,L.State>}

law base_constructor_collision_is_invalid:
  {L.install_base("type Bool is Data:\n  False{}\n  True{}\n",
    L.State{Nil{},Nil{},Nil{},Q.Symbols{Nil{},["True"]},Nil{},False{}}) ==
    Fail{S.Invalid{"load","duplicate-global",S.At{0,0,0,0}}} : Result<S.Error,L.State>}

law column_zero_foreign_body_is_unsupported:
  {I.header("def tick() -> IO(Unit):\nimport \"tick.js\"\n") ==
    Fail{S.Unsupported{"check","foreign-definition",S.At{0,0,2,0}}} : Result<S.Error,I.Header>}

law module_import_after_declaration_is_invalid:
  {I.header("type Flag is Type:\n  Off{}\nimport ./m.bend as M\n") ==
    Fail{S.Invalid{"load","import-after-declaration",S.At{0,0,3,0}}} : Result<S.Error,I.Header>}

law quoted_body_leaves_imports_to_the_lexer:
  {I.header("def text() -> String:\n  \"a\nimport ./x.bend as X\"\n") ==
    Done{I.Header{Nil{},"def text() -> String:\n  \"a\nimport ./x.bend as X\"\n"}} : Result<S.Error,I.Header>}

law output_names_no_file_the_load_read:
  for +tree: S.Node
  for +checked: List<&2,String>
  for +unchecked: List<&2,String>
  {(L.written("./lib/../lib/flag.bend",L.Receipt{tree,["main.bend","lib/flag.bend"],checked,unchecked}),
    L.written("/w/main.bend",L.Receipt{tree,["main.bend"],checked,unchecked}),
    L.written("/w/.toolchain/bend-2.0.29-574b6d3/bend2/base.bend",L.Receipt{tree,["/w/main.bend"],checked,unchecked}),
    L.written("fresh.wasm",L.Receipt{tree,["main.bend","lib/flag.bend"],checked,unchecked})) ==
    (Fail{S.Host{"arguments","source-is-output"}},Fail{S.Host{"arguments","source-is-output"}},
     Fail{S.Host{"arguments","source-is-output"}},Done{Unit{}})
    : Result<S.Error,Unit> & Result<S.Error,Unit> & Result<S.Error,Unit> & Result<S.Error,Unit>}

law uncanonical_output_is_refused:
  {(L.written("../w/lib/flag.bend",L.Receipt{S.Sequence{Nil{}},["main.bend"],Nil{},Nil{}}),
    L.canonical_output(Fail{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}})) ==
    (Fail{S.Host{"arguments","output-path"}},Fail{S.Host{"arguments","output-path"}})
    : Result<S.Error,Unit> & Result<S.Error,Unit>}

law ambiguous_host_path_is_unsupported:
  {F.classified(Done{False{}}) ==
    Fail{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}} : Result<S.Error,Unit>}

law canonical_host_path_can_load:
  {F.classified(Done{True{}}) == Done{Unit{}} : Result<S.Error,Unit>}

law path_query_failure_is_a_host_failure:
  for +message: String
  {F.classified(Fail{(13,message)}) ==
    Fail{S.Host{"path-identity",String.append("13\t",message)}} : Result<S.Error,Unit>}
