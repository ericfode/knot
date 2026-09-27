import Base
import ./main.bend as S
import ./types.bend as T
import ./observations.bend as O

# Exhaustive positions and valid half-open spans within each concrete text.
def span_ends(fuel: Nat, +text: String, +a: U32, +b: U32) -> Bool:
  match fuel:
    case 0n: True{}
    case 1n+f: Bool.and(O.span(text,a,b),span_ends(f,text,a,(b + 1 : U32)))

def positions(fuel: Nat, +text: String, +i: U32, +n: U32) -> Bool:
  match fuel:
    case 0n: True{}
    case 1n+f:
      Bool.and(O.get(text,i),Bool.and(O.locate(text,i),Bool.and(O.roundtrip(text,i),Bool.and(O.cursor(text,i,Done{T.Cursor{7,i}}),Bool.and(span_ends(U32.to_nat((n - i + 1 : U32)),text,i,i),positions(f,text,(i + 1 : U32),n))))))

def columns(fuel: Nat, +text: String, +line: U32, +col: U32) -> Bool:
  match fuel:
    case 0n: True{}
    case 1n+f: Bool.and(O.offset(text,T.Location{line,col}),columns(f,text,line,(col + 1 : U32)))

def locations(fuel: Nat, +text: String, +line: U32, +n: U32) -> Bool:
  match fuel:
    case 0n: True{}
    case 1n+f: Bool.and(columns(U32.to_nat((n + 2 : U32)),text,line,0),locations(f,text,(line + 1 : U32),n))

def sample(+text: String, +n: U32, lines: U32) -> Bool:
  Bool.and(O.metadata(text,lines),Bool.and(positions(U32.to_nat((n + 1 : U32)),text,0,n),Bool.and(O.get(text,(n + 1 : U32)),Bool.and(O.locate(text,(n + 1 : U32)),locations(U32.to_nat((n + 2 : U32)),text,0,n)))))

def content_cases() -> Bool:
  Bool.and(sample("",0,1),Bool.and(sample("x",1,1),Bool.and(sample("ab",2,1),Bool.and(sample("\n",1,2),Bool.and(sample("a\n\nb",4,3),Bool.and(sample("\r\n",2,2),Bool.and(sample("x\ry",3,1),Bool.and(sample("a😀\nβ",4,2),sample("\u{0}é\n\n",4,3)))))))))

def cursor_cases() -> Bool:
  Bool.and(O.bump("ab",T.Cursor{7,0},T.Cursor{7,1},Some{'a'}),Bool.and(O.bump("ab",T.Cursor{7,1},T.Cursor{7,2},Some{'b'}),Bool.and(O.bump("ab",T.Cursor{7,2},T.Cursor{7,2},None{}),Bool.and(O.bump("",T.Cursor{7,0},T.Cursor{7,0},None{}),Bool.and(O.peek("a😀",T.Cursor{7,1},Done{Some{'😀'}}),Bool.and(O.peek("a😀",T.Cursor{7,2},Done{None{}}),O.restore("a😀",T.Cursor{7,1},Done{T.Cursor{7,1}})))))))

def invalid_cases() -> Bool:
  Bool.and(O.cursor("a",2,Fail{T.Bounds{}}),Bool.and(O.restore("a",T.Cursor{8,0},Fail{T.ForeignFile{}}),Bool.and(O.restore("a",T.Cursor{7,2},Fail{T.Bounds{}}),Bool.and(O.peek("a",T.Cursor{8,4294967295},Fail{T.ForeignFile{}}),Bool.and(O.peek("a",T.Cursor{7,2},Fail{T.Bounds{}}),Bool.and(O.bump_bad("a",T.Cursor{8,0},T.ForeignFile{}),Bool.and(O.bump_bad("a",T.Cursor{7,2},T.Bounds{}),Bool.and(O.span_reject("ab",2,1),Bool.and(O.span_reject("ab",0,3),Bool.and(O.extract("ab",T.Span{8,0,1},Fail{T.ForeignFile{}}),Bool.and(O.extract("ab",T.Span{7,2,1},Fail{T.InvalidRange{}}),Bool.and(O.extract("ab",T.Span{7,0,3},Fail{T.InvalidRange{}}),Bool.and(O.get("ab",4294967295),Bool.and(O.locate("ab",4294967295),O.offset("ab",T.Location{4294967295,4294967295})))))))))))))))

def construction_cases() -> Bool:
  Bool.and(O.rejected(T.Limit{},S.Source.bounded(7,"a",0)),Bool.and(O.rejected(T.Limit{},S.Source.bounded(7,"abc",2)),Bool.and(O.built_content("",S.Source.bounded(7,"",0)),Bool.and(O.built_content("ab",S.Source.bounded(7,"ab",2)),O.preserved_new(SCon{Chr{55295},SCon{Chr{57344},SCon{Chr{1114111},""}}})))))

def all() -> Bool:
  Bool.and(U32.is_eq(S.Source.maximum(),16777215),Bool.and(content_cases(),Bool.and(cursor_cases(),Bool.and(invalid_cases(),construction_cases()))))

def main() -> U32:
  Bool.to_u32(all())
