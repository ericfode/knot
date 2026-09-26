import Base
import ./main.bend as S
import ./types.bend as T
import ./observations.bend as O
import ./proof_observations.bend as P

# Universal over file IDs, fixed inhabited text shapes. Not a theorem for all strings.
law content_identity:
  for id: U32
  {P.text(S.Source.new(id,"a😀\nβ")) == Done{"a😀\nβ"} : Result<T.Error,String>}

law file_identity:
  for id: U32
  {P.file(S.Source.new(id,"a😀\nβ")) == Done{id} : Result<T.Error,U32>}

law empty_content:
  for id: U32
  {P.text(S.Source.bounded(id,"",0)) == Done{""} : Result<T.Error,String>}

law empty_lines:
  for id: U32
  {P.lines(S.Source.new(id,"")) == Done{1} : Result<T.Error,U32>}

law scalar_units:
  for id: U32
  {P.length(S.Source.new(id,"a😀\nβ")) == Done{4} : Result<T.Error,U32>}

# Concrete normalization theorems through public observations and independent model.
law indexed_value:
  {O.get("a😀\nβ",1) == True{} : Bool}
law peek_codepoint:
  {O.peek("a😀",T.Cursor{7,1},Done{Some{'😀'}}) == True{} : Bool}
law bump_restore_content:
  {O.bump("a😀",T.Cursor{7,1},T.Cursor{7,2},Some{'😀'}) == True{} : Bool}
law eof_fixed_point:
  {O.bump("a😀",T.Cursor{7,2},T.Cursor{7,2},None{}) == True{} : Bool}
law span_order:
  {O.extract("a😀\nβ",T.Span{7,1,3},Done{"😀\n"}) == True{} : Bool}
law empty_eof_span:
  {O.span("a😀",2,2) == True{} : Bool}
law newline_location:
  {O.locate("a😀\nβ",3) == True{} : Bool}
law newline_roundtrip:
  {O.roundtrip("a😀\nβ",3) == True{} : Bool}
law cr_is_content:
  {O.locate("a\rb",2) == True{} : Bool}
law crlf_location:
  {O.locate("a\r\nb",3) == True{} : Bool}
law trailing_line:
  {O.metadata("\n",2) == True{} : Bool}
law canonical_location:
  {O.offset("a\nb",T.Location{0,2}) == True{} : Bool}
law foreign_cursor:
  {O.restore("a",T.Cursor{8,0},Fail{T.ForeignFile{}}) == True{} : Bool}
law foreign_span:
  {O.extract("a",T.Span{8,0,1},Fail{T.ForeignFile{}}) == True{} : Bool}
law rejected_span:
  {O.span_reject("ab",2,1) == True{} : Bool}
law rejected_offset:
  {O.cursor("a",2,Fail{T.Bounds{}}) == True{} : Bool}
law exhausted_limit:
  {O.rejected(T.Limit{},S.Source.bounded(7,"abc",2)) == True{} : Bool}
law invalid_scalar:
  {O.rejected(T.InvalidScalar{},S.Source.new(7,SCon{Chr{55296},""})) == True{} : Bool}

# Auxiliary helper normalization over arbitrary source and candidate cursor.
# Public conditional wrapper theorems below establish bounds and state preservation.
law checked_cursor:
  for s: S.Source
  for id: U32
  for i: U32
  {S.cursor_if(s,T.Cursor{id,i},True{}) == (s,Done{T.Cursor{id,i}}) : S.Source & Result<T.Error,T.Cursor>}

law accepted_cursor:
  for s: S.Source
  for i: U32
  for valid: {U32.is_le(i,P.size(s)) == True{} : Bool}
  {S.Source.cursor(s,i) == (s,Done{T.Cursor{P.identity(s),i}}) : S.Source & Result<T.Error,T.Cursor>}

law rejected_cursor:
  for s: S.Source
  for i: U32
  for invalid: {U32.is_le(i,P.size(s)) == False{} : Bool}
  {S.Source.cursor(s,i) == (s,Fail{T.Bounds{}}) : S.Source & Result<T.Error,T.Cursor>}

law accepted_span:
  for s: S.Source
  for a: U32
  for b: U32
  for valid: {Bool.and(U32.is_le(a,b),U32.is_le(b,P.size(s))) == True{} : Bool}
  {S.Source.span(s,a,b) == (s,Done{T.Span{P.identity(s),a,b}}) : S.Source & Result<T.Error,T.Span>}

law rejected_span_universal:
  for s: S.Source
  for a: U32
  for b: U32
  for invalid: {Bool.and(U32.is_le(a,b),U32.is_le(b,P.size(s))) == False{} : Bool}
  {S.Source.span(s,a,b) == (s,Fail{T.InvalidRange{}}) : S.Source & Result<T.Error,T.Span>}

law foreign_restore:
  for s: S.Source
  for foreign: U32
  for i: U32
  for different: {U32.is_eq(foreign,P.identity(s)) == False{} : Bool}
  {S.Source.restore(s,T.Cursor{foreign,i}) == (s,Fail{T.ForeignFile{}}) : S.Source & Result<T.Error,T.Cursor>}

law inhabited_cursor_domain:
  {O.cursor("ab",1,Done{T.Cursor{7,1}}) == True{} : Bool}
law inhabited_span_domain:
  {O.span("ab",0,2) == True{} : Bool}

law maximum_policy:
  {S.Source.maximum() == 16777215 : U32}
