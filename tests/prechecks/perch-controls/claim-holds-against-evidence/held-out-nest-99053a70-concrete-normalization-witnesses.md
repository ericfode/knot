<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=nest; head=99053a70a68b; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/matrix-LAWS.bend@99053a70 sha256=905f77100e8337b040f01de1bab6f78d6720c18db3e4b3f58387467b1d6b71cd; src/matrix-LAWS.bend@99053a70 sha256=905f77100e8337b040f01de1bab6f78d6720c18db3e4b3f58387467b1d6b71cd; src/matrix-LAWS.bend@99053a70 sha256=905f77100e8337b040f01de1bab6f78d6720c18db3e4b3f58387467b1d6b71cd; tests/compiler-nest/SPEC.md@99053a70 sha256=804f734b646e70c5f0def9707a90b08acc008386a3f8acc475eba7125140dba1 -->
# Claim
tests/compiler-nest/SPEC.md:112-114 (section: Pattern matrices and recursive tree execution) - verbatim text:

> Two complete checker normalizations exercise an overlapping
> irrefutable row and an exhaustive 2-by-2 matrix; `irrefutable_lowering_witness`,
> `irrefutable_first_row_witness` and `exhaustive_matrix_witness` are concrete.

# Evidence
Evidence: the declarations the claim names, at head.

`src/matrix-LAWS.bend:119-124` (declaration naming `exhaustive_matrix_witness`)
```
  119  law exhaustive_matrix_witness:
  120    {lower([row(ctor("Off"),ctor("Off"),"Off"),row(ctor("Off"),ctor("On"),"On"),
  121            row(ctor("On"),ctor("Off"),"On"),row(ctor("On"),ctor("On"),"Off")]) ==
  122      Done{C.Checked{C.Case{token("match"),0,0,[
  123        C.Branch{0,Nil{},C.Case{token("match"),1,0,[C.Branch{0,Nil{},C.Value{token("Off"),0,0}},C.Branch{1,Nil{},C.Value{token("On"),0,1}}]}},
  124        C.Branch{1,Nil{},C.Case{token("match"),1,0,[C.Branch{0,Nil{},C.Value{token("On"),0,1}},C.Branch{1,Nil{},C.Value{token("Off"),0,0}}]}}]},0,[0,1]}} : Result<S.Error,C.Checked>}
```

`src/matrix-LAWS.bend:114-117` (declaration naming `irrefutable_first_row_witness`)
```
  114  law irrefutable_first_row_witness:
  115    {M.expand(64n,S.Matrix{token("match"),[S.Variable{token("x")},S.Variable{token("y")}],
  116        [row(wild(),wild(),"On"),row(ctor("Off"),ctor("Off"),"Off")],4096},[flag()],parameters(),4096) ==
  117      Done{M.Expansion{off("x",off("y",bound(ctor("On")),bound(ctor("On"))),bound(ctor("On"))),4088}} : Result<S.Error,M.Expansion>}
```

`src/matrix-LAWS.bend:101-109` (declaration naming `irrefutable_lowering_witness`)
```
  101  law irrefutable_lowering_witness:
  102    {lower([row(S.Variable{token("_")},S.Variable{token("_")},"On"),
  103            row(ctor("Off"),ctor("Off"),"Off")]) ==
  104      Done{C.Checked{C.Case{token("match"),0,0,[
  105        C.Branch{0,Nil{},C.Case{token("match"),1,0,[C.Branch{0,Nil{},C.Value{token("On"),0,1}},C.Branch{1,Nil{},C.Value{token("On"),0,1}}]}},
  106        C.Branch{1,Nil{},C.Value{token("On"),0,1}}]},0,[0,1]}} : Result<S.Error,C.Checked>}
  107  
  108  # Inhabits lowering-LAWS irrefutable_first_row_selected: the overlapping
  109  # Off/Off row is shadowed at every leaf of the two-level lowering.
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
