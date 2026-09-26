import Base
import ./main.bend as S
import ./types.bend as T
import ./model.bend as M

def error_eq(a: T.Error, b: T.Error) -> Bool:
  match a b:
    case T.Bounds{} T.Bounds{}: True{}
    case T.ForeignFile{} T.ForeignFile{}: True{}
    case T.InvalidRange{} T.InvalidRange{}: True{}
    case T.InvalidScalar{} T.InvalidScalar{}: True{}
    case T.Limit{} T.Limit{}: True{}
    case T.IndexInvariant{} T.IndexInvariant{}: True{}
    case _ _: False{}

def chars_eq(a: Result<T.Error,Char>, b: Result<T.Error,Char>) -> Bool:
  match a b:
    case Fail{e} Fail{f}: error_eq(e,f)
    case Done{x} Done{y}: Char.is_eq(x,y)
    case _ _: False{}

def nums_eq(a: Result<T.Error,U32>, b: Result<T.Error,U32>) -> Bool:
  match a b:
    case Fail{e} Fail{f}: error_eq(e,f)
    case Done{x} Done{y}: U32.is_eq(x,y)
    case _ _: False{}

def locs_eq(a: Result<T.Error,T.Location>, b: Result<T.Error,T.Location>) -> Bool:
  match a b:
    case Fail{e} Fail{f}: error_eq(e,f)
    case Done{x} Done{y}: M.location_eq(x,y)
    case _ _: False{}

def texts_eq(a: Result<T.Error,String>, b: Result<T.Error,String>) -> Bool:
  match a b:
    case Fail{e} Fail{f}: error_eq(e,f)
    case Done{x} Done{y}: String.eq(x,y)
    case _ _: False{}

def cursors_eq(a: T.Cursor, b: T.Cursor) -> Bool:
  match a b:
    case T.Cursor{f,i} T.Cursor{g,j}: Bool.and(U32.is_eq(f,g),U32.is_eq(i,j))

def cursors_result(a: Result<T.Error,T.Cursor>, b: Result<T.Error,T.Cursor>) -> Bool:
  match a b:
    case Fail{e} Fail{f}: error_eq(e,f)
    case Done{x} Done{y}: cursors_eq(x,y)
    case _ _: False{}

def maybe_eq(a: Maybe<Char>, b: Maybe<Char>) -> Bool:
  match a b:
    case None{} None{}: True{}
    case Some{x} Some{y}: Char.is_eq(x,y)
    case _ _: False{}

def peek_eq(a: Result<T.Error,Maybe<Char>>, b: Result<T.Error,Maybe<Char>>) -> Bool:
  match a b:
    case Fail{e} Fail{f}: error_eq(e,f)
    case Done{x} Done{y}: maybe_eq(x,y)
    case _ _: False{}

def content_lines(expected: U32, pair: S.Source & U32) -> Bool:
  (s,actual) = pair
  U32.is_eq(expected,actual)

def content_length(+text: String, pair: S.Source & U32) -> Bool:
  (s,actual) = pair
  Bool.and(U32.is_eq(actual,U32.from_nat(String.length(text))),content_lines(M.line_count(text),S.Source.line_count(s)))

def content_file(text: String, pair: S.Source & U32) -> Bool:
  (s,actual) = pair
  Bool.and(U32.is_eq(actual,7),content_length(text,S.Source.length(s)))

def content(+text: String, pair: S.Source & String) -> Bool:
  (s,actual) = pair
  Bool.and(String.eq(text,actual),content_file(text,S.Source.file(s)))

def preserved(s: S.Source, text: String, ok: Bool) -> Bool:
  Bool.and(ok,content(text,S.Source.text(s)))

def read_char(text: String, want: Result<T.Error,Char>, pair: S.Source & Result<T.Error,Char>) -> Bool:
  (s,got) = pair
  preserved(s,text,chars_eq(got,want))

def get_created(+text: String, +i: U32, result: Result<T.Error,S.Source>) -> Bool:
  match result:
    case Fail{e}: False{}
    case Done{s}: read_char(text,M.get(text,U32.to_nat(i)),S.Source.get(s,i))

def get(+text: String, +i: U32) -> Bool:
  get_created(text,i,S.Source.new(7,text))

def read_location(+text: String, +i: U32, pair: S.Source & Result<T.Error,T.Location>) -> Bool:
  (s,got) = pair
  preserved(s,text,locs_eq(got,M.locate(text,i)))

def locate_created(text: String, +i: U32, result: Result<T.Error,S.Source>) -> Bool:
  match result:
    case Fail{e}: False{}
    case Done{s}: read_location(text,i,S.Source.locate(s,i))

def locate(+text: String, i: U32) -> Bool:
  locate_created(text,i,S.Source.new(7,text))

def read_offset(+text: String, loc: T.Location, pair: S.Source & Result<T.Error,U32>) -> Bool:
  (s,got) = pair
  preserved(s,text,nums_eq(got,M.offset(text,loc)))

def offset_created(text: String, +loc: T.Location, result: Result<T.Error,S.Source>) -> Bool:
  match result:
    case Fail{e}: False{}
    case Done{s}: read_offset(text,loc,S.Source.offset(s,loc))

def offset(+text: String, loc: T.Location) -> Bool:
  offset_created(text,loc,S.Source.new(7,text))

def roundtrip_offset(text: String, i: U32, pair: S.Source & Result<T.Error,U32>) -> Bool:
  (s,r) = pair
  preserved(s,text,nums_eq(r,Done{i}))

def roundtrip_loc(s: S.Source, text: String, i: U32, r: Result<T.Error,T.Location>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{loc}: roundtrip_offset(text,i,S.Source.offset(s,loc))

def roundtrip_pair(text: String, i: U32, pair: S.Source & Result<T.Error,T.Location>) -> Bool:
  (s,r) = pair
  roundtrip_loc(s,text,i,r)

def roundtrip_created(text: String, +i: U32, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: roundtrip_pair(text,i,S.Source.locate(s,i))

def roundtrip(+text: String, i: U32) -> Bool:
  roundtrip_created(text,i,S.Source.new(7,text))

def extract_read(text: String, expected: Result<T.Error,String>, pair: S.Source & Result<T.Error,String>) -> Bool:
  (s,r) = pair
  preserved(s,text,texts_eq(r,expected))

def extract_created(text: String, span: T.Span, expected: Result<T.Error,String>, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: extract_read(text,expected,S.Source.extract(s,span))

def extract(+text: String, span: T.Span, expected: Result<T.Error,String>) -> Bool:
  extract_created(text,span,expected,S.Source.new(7,text))

def span_extracted(s: S.Source, text: String, want: String, r: Result<T.Error,T.Span>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{span}: extract_read(text,Done{want},S.Source.extract(s,span))

def span_pair(text: String, want: String, pair: S.Source & Result<T.Error,T.Span>) -> Bool:
  (s,r) = pair
  span_extracted(s,text,want,r)

def span_created(+text: String, +a: U32, +b: U32, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: span_pair(text,M.slice(text,U32.to_nat(a),U32.to_nat((b - a : U32))),S.Source.span(s,a,b))

def span(+text: String, a: U32, b: U32) -> Bool:
  span_created(text,a,b,S.Source.new(7,text))

def cursor_read(text: String, want: Result<T.Error,T.Cursor>, pair: S.Source & Result<T.Error,T.Cursor>) -> Bool:
  (s,r) = pair
  preserved(s,text,cursors_result(r,want))

def cursor_created(text: String, i: U32, want: Result<T.Error,T.Cursor>, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: cursor_read(text,want,S.Source.cursor(s,i))

def cursor(+text: String, i: U32, want: Result<T.Error,T.Cursor>) -> Bool:
  cursor_created(text,i,want,S.Source.new(7,text))

def restore_created(text: String, c: T.Cursor, want: Result<T.Error,T.Cursor>, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: cursor_read(text,want,S.Source.restore(s,c))

def restore(+text: String, c: T.Cursor, want: Result<T.Error,T.Cursor>) -> Bool:
  restore_created(text,c,want,S.Source.new(7,text))

def peek_read(text: String, want: Result<T.Error,Maybe<Char>>, pair: S.Source & Result<T.Error,Maybe<Char>>) -> Bool:
  (s,r) = pair
  preserved(s,text,peek_eq(r,want))

def peek_created(text: String, c: T.Cursor, want: Result<T.Error,Maybe<Char>>, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: peek_read(text,want,S.Source.peek(s,c))

def peek(+text: String, c: T.Cursor, want: Result<T.Error,Maybe<Char>>) -> Bool:
  peek_created(text,c,want,S.Source.new(7,text))

def bumped_check(s: S.Source, text: String, +saved: T.Cursor, want: T.Cursor, ch: Maybe<Char>, r: Result<T.Error,T.Cursor & Maybe<Char>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{Tuple{actual,got}}:
      Bool.and(Bool.and(cursors_eq(actual,want),maybe_eq(got,ch)),cursor_read(text,Done{saved},S.Source.restore(s,saved)))

def bump_pair(text: String, saved: T.Cursor, want: T.Cursor, ch: Maybe<Char>, pair: S.Source & Result<T.Error,T.Cursor & Maybe<Char>>) -> Bool:
  (s,r) = pair
  bumped_check(s,text,saved,want,ch,r)

def bump_created(text: String, +c: T.Cursor, want: T.Cursor, ch: Maybe<Char>, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: Bool.and(cursors_eq(S.Source.checkpoint(c),c),bump_pair(text,S.Source.checkpoint(c),want,ch,S.Source.bump(s,c)))

def bump(+text: String, c: T.Cursor, want: T.Cursor, ch: Maybe<Char>) -> Bool:
  bump_created(text,c,want,ch,S.Source.new(7,text))

def rejected(e: T.Error, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{actual}: error_eq(e,actual)
    case Done{s}: False{}

def built_content(text: String, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: content(text,S.Source.text(s))

def preserved_new(+text: String) -> Bool:
  built_content(text,S.Source.new(7,text))

def metadata_line(text: String, want: U32, pair: S.Source & U32) -> Bool:
  (s,actual) = pair
  preserved(s,text,U32.is_eq(want,actual))

def metadata_len(+text: String, want: U32, pair: S.Source & U32) -> Bool:
  (s,actual) = pair
  Bool.and(U32.is_eq(actual,U32.from_nat(String.length(text))),metadata_line(text,want,S.Source.line_count(s)))

def metadata_file(+text: String, want: U32, pair: S.Source & U32) -> Bool:
  (s,actual) = pair
  Bool.and(U32.is_eq(actual,7),metadata_len(text,want,S.Source.length(s)))

def metadata_created(text: String, lines: U32, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: metadata_file(text,lines,S.Source.file(s))

def metadata(+text: String, lines: U32) -> Bool:
  metadata_created(text,lines,S.Source.new(7,text))

def span_error(r: Result<T.Error,T.Span>) -> Bool:
  match r:
    case Fail{T.InvalidRange{}}: True{}
    case _: False{}

def bad_span(text: String, pair: S.Source & Result<T.Error,T.Span>) -> Bool:
  (s,r) = pair
  preserved(s,text,span_error(r))

def span_reject_created(text: String, a: U32, b: U32, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: bad_span(text,S.Source.span(s,a,b))

def span_reject(+text: String, a: U32, b: U32) -> Bool:
  span_reject_created(text,a,b,S.Source.new(7,text))

def bump_error(e: T.Error, r: Result<T.Error,T.Cursor & Maybe<Char>>) -> Bool:
  match r:
    case Fail{got}: error_eq(e,got)
    case Done{x}: False{}

def bump_bad_read(text: String, e: T.Error, pair: S.Source & Result<T.Error,T.Cursor & Maybe<Char>>) -> Bool:
  (s,r) = pair
  preserved(s,text,bump_error(e,r))

def bump_bad_created(text: String, c: T.Cursor, e: T.Error, r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: bump_bad_read(text,e,S.Source.bump(s,c))

def bump_bad(+text: String, c: T.Cursor, e: T.Error) -> Bool:
  bump_bad_created(text,c,e,S.Source.new(7,text))
