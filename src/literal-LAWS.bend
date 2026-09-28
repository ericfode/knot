import Base
import ./syntax.bend as S
import ./literal.bend as L
import ./primitive-eval.bend as P
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

law surrogate_code:
  for +token: S.Token
  {L.glyph("\\u{d83d}",token) == Done{L.Glyph{55357,"","\\u{d83d}"}} : Result<S.Error,L.Glyph>}

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

law nul_is_a_character:
  for token: S.Token
  {L.quoted("\"\\0\"",token) == Done{L.Quoted{[0],"","\"\\0\""}} : Result<S.Error,L.Quoted>}

law legacy_literal_boundary:
  for +token: S.Token
  {L.legacy(1n,[S.Literal{token,0,7,Nil{}}]) ==
    Fail{S.Unsupported{"parse","term-form",S.at(token)}} : Result<S.Error,Unit>}
