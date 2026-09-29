import Base
import ./syntax.bend as S
import ./literal.bend as L
import ./primitive-eval.bend as P
import ./primitive-op.bend as R
import ./machine-code.bend as A

law div_zero:
  for x: U32
  {P.div(x,0) == 0 : U32}

law rem_zero:
  for +x: U32
  {P.rem(x,0) == x : U32}

law shl_wide:
  for +x: U32
  for +n: U32
  for wide: {U32.is_ge(n,32) == True{} : Bool}
  {P.shl(x,n) == 0 : U32}

law shr_wide:
  for +x: U32
  for +n: U32
  for wide: {U32.is_ge(n,32) == True{} : Bool}
  {P.shr(x,n) == 0 : U32}

law wide_boundary:
  {U32.is_ge(32,32) == True{} : Bool}

law append_order:
  {P.apply(R.SAppend{},[P.Codes{[97,98]},P.Codes{[99]}]) == Done{P.Codes{[97,98,99]}} : Result<S.Error,P.Datum>}

law length_count:
  {P.apply(R.SLength{},[P.Codes{[97,98,99]}]) == Done{P.Count{3}} : Result<S.Error,P.Datum>}

law equal_length:
  {P.apply(R.SEq{},[P.Codes{[97]},P.Codes{[97,98]}]) == Done{P.Bits{0}} : Result<S.Error,P.Datum>}

law surrogate_code:
  for +token: S.Token
  {L.glyph("\\u{d83d}",token) == Done{L.Glyph{55357,"","\\u{d83d}"}} : Result<S.Error,L.Glyph>}

law escape_before_brace:
  for +token: S.Token
  {L.glyph("\\n{",token) == Done{L.Glyph{10,"{","\\n"}} : Result<S.Error,L.Glyph>}

law surrogate_sequence:
  for token: S.Token
  {L.quoted("\"\\u{d83d}\\u{de00}\"",token) == Done{L.Quoted{[55357,56832],"","\"\\u{d83d}\\u{de00}\""}} : Result<S.Error,L.Quoted>}

law scalar_sequence:
  for token: S.Token
  {L.quoted("\"\\u{1f600}\"",token) == Done{L.Quoted{[128512],"","\"\\u{1f600}\""}} : Result<S.Error,L.Quoted>}

law decimal_maximum:
  for token: S.Token
  {L.decimal("4294967295",0,token) == Done{4294967295} : Result<S.Error,U32>}

law decimal_overflow:
  for +token: S.Token
  {L.decimal("4294967296",0,token) == Fail{S.Invalid{"lex","literal-overflow",S.at(token)}} : Result<S.Error,U32>}

law signed_bits:
  {A.i32(4294967295) == [65,255,255,255,255,127] : List<&2,U32>}

law runs_are_bounded:
  {A.runs(2,[1,2,3,4,5]) == [[1,2],[3,4],[5]] : List<&2,List<&2,U32>>}

law seq_undoes_runs:
  {A.seq(A.runs(3,[1,2,3,4,5,6,7])) == [1,2,3,4,5,6,7] : List<&2,U32>}

law nul_is_a_character:
  for token: S.Token
  {L.quoted("\"\\0\"",token) == Done{L.Quoted{[0],"","\"\\0\""}} : Result<S.Error,L.Quoted>}

law legacy_literal_boundary:
  for +token: S.Token
  {L.legacy(1n,[S.Literal{token,0,7,Nil{}}]) ==
    Fail{S.Unsupported{"parse","term-form",S.at(token)}} : Result<S.Error,Unit>}

law char_literal_reads_back:
  for token: S.Token
  {L.quoted(P.quoted([39],39),token) == Done{L.Quoted{[39],"","'\\''"}} : Result<S.Error,L.Quoted>}

law text_literal_reads_back:
  for token: S.Token
  {L.quoted(P.quoted([0,9,10,13,34,39,92,127,55357,1114112],34),token) ==
    Done{L.Quoted{[0,9,10,13,34,39,92,127,55357,1114112],"","\"\\0\\t\\n\\r\\\"'\\\\\\u{7f}\\u{d83d}\\u{110000}\""}} : Result<S.Error,L.Quoted>}

law glyph_boundaries:
  {[P.glyph(31,34),P.glyph(32,34),P.glyph(55295,34),P.glyph(55296,34),P.glyph(57343,34),P.glyph(57344,34),P.glyph(1114111,34),P.glyph(1114112,34)] ==
    ["\\u{1f}"," ",SCon{Char.from_u32(55295),SNil{}},"\\u{d800}","\\u{dfff}",SCon{Char.from_u32(57344),SNil{}},SCon{Char.from_u32(1114111),SNil{}},"\\u{110000}"] : List<&2,String>}
