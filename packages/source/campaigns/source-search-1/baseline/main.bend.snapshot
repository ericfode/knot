import Base
import ./types.bend as T
import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as V

# Buffer and helpers are representation-private by API convention.
type Source is Type:
  Buffer{file: U32, size: U32, chars: V.Vec<Char>, starts: V.Vec<U32>}

def Source.maximum() -> U32:
  16777215

def scalar(+c: Char) -> Bool:
  +u = Char.to_u32(c)
  Bool.and(U32.is_le(u, 1114111), Bool.or(U32.is_lt(u, 55296), U32.is_gt(u, 57343)))

def finish_push(id: U32, n: U32, chars: V.Vec<Char>, lines: V.Vec<U32>, r: Result<V.Error,Unit>) -> Result<T.Error,Source>:
  match r:
    case Fail{e}: Fail{T.Limit{}}
    case Done{x}: Done{Buffer{id,n,chars,lines}}

def finish_line(id: U32, n: U32, chars: V.Vec<Char>, pair: V.Vec<U32> & Result<V.Error,Unit>) -> Result<T.Error,Source>:
  (lines,r) = pair
  finish_push(id,n,chars,lines,r)

def add_line(id: U32, +n: U32, chars: V.Vec<Char>, lines: V.Vec<U32>, newline: Bool) -> Result<T.Error,Source>:
  match newline:
    case False{}: Done{Buffer{id,n,chars,lines}}
    case True{}:
      finish_line(id,n,chars,V.Vec.push(U32,lines,n))

def add_char_result(id: U32, n: U32, chars: V.Vec<Char>, lines: V.Vec<U32>, newline: Bool, r: Result<V.Error,Unit>) -> Result<T.Error,Source>:
  match r:
    case Fail{e}: Fail{T.Limit{}}
    case Done{x}: add_line(id,n,chars,lines,newline)

def finish_char(id: U32, n: U32, lines: V.Vec<U32>, newline: Bool, pair: V.Vec<Char> & Result<V.Error,Unit>) -> Result<T.Error,Source>:
  (chars,r) = pair
  add_char_result(id,n,chars,lines,newline,r)

def add_valid(s: Source, +c: Char, valid: Bool) -> Result<T.Error,Source>:
  match s valid:
    case Buffer{id,n,chars,lines} False{}: Fail{T.InvalidScalar{}}
    case Buffer{id,n,chars,lines} True{}:
      finish_char(id,(n + 1 : U32),lines,Char.is_eq(c,'\n'),V.Vec.push(Char,chars,c))

def add(s: Result<T.Error,Source>, +c: Char) -> Result<T.Error,Source>:
  match s:
    case Fail{e}: Fail{e}
    case Done{src}: add_valid(src,c,scalar(c))

def build(text: String, s: Result<T.Error,Source>) -> Result<T.Error,Source>:
  match text:
    case SNil{}: s
    case SCon{c,tail}: build(tail,add(s,c))

def Source.bounded(file: U32, text: String, limit: U32) -> Result<T.Error,Source>:
  build(text,finish_line(file,0,V.Vec.bounded(Char,U32.min(limit,Source.maximum())),V.Vec.push(U32,V.Vec.new(U32),0)))

def Source.new(file: U32, text: String) -> Result<T.Error,Source>:
  Source.bounded(file,text,Source.maximum())

def Source.file(s: Source) -> Source & U32:
  match s:
    case Buffer{+id,n,chars,lines}: (Buffer{id,n,chars,lines},id)

def Source.length(s: Source) -> Source & U32:
  match s:
    case Buffer{id,+n,chars,lines}: (Buffer{id,n,chars,lines},n)

def count_result(id: U32, n: U32, chars: V.Vec<Char>, pair: V.Vec<U32> & U32) -> Source & U32:
  (lines,count) = pair
  (Buffer{id,n,chars,lines},count)

def Source.line_count(s: Source) -> Source & U32:
  match s:
    case Buffer{id,n,chars,lines}:
      count_result(id,n,chars,V.Vec.length(U32,lines))

def chars_text(xs: List<Char>) -> String:
  match xs:
    case Nil{}: SNil{}
    case Con{h,t}: SCon{h,chars_text(t)}

def text_result(id: U32, n: U32, lines: V.Vec<U32>, pair: V.Vec<Char> & List<Char>) -> Source & String:
  (chars,xs) = pair
  (Buffer{id,n,chars,lines},chars_text(xs))

def Source.text(s: Source) -> Source & String:
  match s:
    case Buffer{id,n,chars,lines}:
      text_result(id,n,lines,V.Vec.to_list(Char,chars))

def char_result(r: Result<V.Error,Char>) -> Result<T.Error,Char>:
  match r:
    case Fail{e}: Fail{T.Bounds{}}
    case Done{c}: Done{c}

def get_result(id: U32, n: U32, lines: V.Vec<U32>, pair: V.Vec<Char> & Result<V.Error,Char>) -> Source & Result<T.Error,Char>:
  (chars,r) = pair
  (Buffer{id,n,chars,lines},char_result(r))

def Source.get(s: Source, i: U32) -> Source & Result<T.Error,Char>:
  match s:
    case Buffer{id,n,chars,lines}:
      get_result(id,n,lines,V.Vec.get(Char,chars,i))

def cursor_if(s: Source, c: T.Cursor, valid: Bool) -> Source & Result<T.Error,T.Cursor>:
  match valid:
    case False{}: (s,Fail{T.Bounds{}})
    case True{}: (s,Done{c})

def Source.cursor(s: Source, +i: U32) -> Source & Result<T.Error,T.Cursor>:
  match s:
    case Buffer{+id,+n,chars,lines}:
      cursor_if(Buffer{id,n,chars,lines},T.Cursor{id,i},U32.is_le(i,n))

def Source.checkpoint(c: T.Cursor) -> T.Cursor:
  c

def restore_if(s: Source, i: U32, same: Bool) -> Source & Result<T.Error,T.Cursor>:
  match same:
    case False{}: (s,Fail{T.ForeignFile{}})
    case True{}: Source.cursor(s,i)

def Source.restore(s: Source, c: T.Cursor) -> Source & Result<T.Error,T.Cursor>:
  match s c:
    case Buffer{+own,n,chars,lines} T.Cursor{id,i}:
      restore_if(Buffer{own,n,chars,lines},i,U32.is_eq(id,own))

def maybe_char(r: Result<T.Error,Char>) -> Result<T.Error,Maybe<Char>>:
  match r:
    case Fail{e}: Fail{e}
    case Done{c}: Done{Some{c}}

def peek_read(pair: Source & Result<T.Error,Char>) -> Source & Result<T.Error,Maybe<Char>>:
  (s,r) = pair
  (s,maybe_char(r))

def peek_at(s: Source, i: U32, eof: Bool) -> Source & Result<T.Error,Maybe<Char>>:
  match eof:
    case True{}: (s,Done{None{}})
    case False{}:
      peek_read(Source.get(s,i))

def peek_checked(s: Source, r: Result<T.Error,T.Cursor>) -> Source & Result<T.Error,Maybe<Char>>:
  match s r:
    case Buffer{id,n,chars,lines} Fail{e}: (Buffer{id,n,chars,lines},Fail{e})
    case Buffer{id,+n,chars,lines} Done{T.Cursor{other,+i}}:
      peek_at(Buffer{id,n,chars,lines},i,U32.is_eq(i,n))

def peek_restored(pair: Source & Result<T.Error,T.Cursor>) -> Source & Result<T.Error,Maybe<Char>>:
  (s,r) = pair
  peek_checked(s,r)

def Source.peek(s: Source, c: T.Cursor) -> Source & Result<T.Error,Maybe<Char>>:
  peek_restored(Source.restore(s,c))

def bumped(c: T.Cursor, r: Result<T.Error,Maybe<Char>>) -> Result<T.Error,T.Cursor & Maybe<Char>>:
  match c r:
    case T.Cursor{id,i} Fail{e}: Fail{e}
    case T.Cursor{id,i} Done{None{}}: Done{(T.Cursor{id,i},None{})}
    case T.Cursor{id,i} Done{Some{ch}}: Done{(T.Cursor{id,(i + 1 : U32)},Some{ch})}

def bump_result(c: T.Cursor, pair: Source & Result<T.Error,Maybe<Char>>) -> Source & Result<T.Error,T.Cursor & Maybe<Char>>:
  (s,r) = pair
  (s,bumped(c,r))

def Source.bump(s: Source, +c: T.Cursor) -> Source & Result<T.Error,T.Cursor & Maybe<Char>>:
  bump_result(c,Source.peek(s,c))

def span_if(s: Source, span: T.Span, valid: Bool) -> Source & Result<T.Error,T.Span>:
  match valid:
    case False{}: (s,Fail{T.InvalidRange{}})
    case True{}: (s,Done{span})

def Source.span(s: Source, +start: U32, +end: U32) -> Source & Result<T.Error,T.Span>:
  match s:
    case Buffer{+id,+n,chars,lines}:
      span_if(Buffer{id,n,chars,lines},T.Span{id,start,end},Bool.and(U32.is_le(start,end),U32.is_le(end,n)))

def slice_result(r: Result<V.Error,List<Char>>) -> Result<T.Error,String>:
  match r:
    case Fail{e}: Fail{T.InvalidRange{}}
    case Done{xs}: Done{chars_text(xs)}

def extract_result(id: U32, n: U32, lines: V.Vec<U32>, pair: V.Vec<Char> & Result<V.Error,List<Char>>) -> Source & Result<T.Error,String>:
  (chars,r) = pair
  (Buffer{id,n,chars,lines},slice_result(r))

def extract_if(s: Source, a: U32, b: U32, same: Bool) -> Source & Result<T.Error,String>:
  match s same:
    case Buffer{id,n,chars,lines} False{}: (Buffer{id,n,chars,lines},Fail{T.ForeignFile{}})
    case Buffer{id,n,chars,lines} True{}:
      extract_result(id,n,lines,V.Vec.slice(Char,chars,a,b))

def Source.extract(s: Source, span: T.Span) -> Source & Result<T.Error,String>:
  match s span:
    case Buffer{+own,n,chars,lines} T.Span{id,a,b}:
      extract_if(Buffer{own,n,chars,lines},a,b,U32.is_eq(id,own))

# Upper-bound search: greatest start <= offset. 25 fuel covers <= 2^24 lines.
type Search is Data:
  Searching{lo: U32, hi: U32}
  Found{line: U32}
  BadIndex{}

def split_search(lo: U32, hi: U32, mid: U32, before: Bool) -> Search:
  match before:
    case True{}: Searching{lo,mid}
    case False{}: Searching{mid,hi}

def split_read(lo: U32, hi: U32, mid: U32, pos: U32, r: Result<V.Error,U32>) -> Search:
  match r:
    case Fail{e}: BadIndex{}
    case Done{start}: split_search(lo,hi,mid,U32.is_lt(pos,start))

def search_read(lo: U32, hi: U32, mid: U32, pos: U32, pair: V.Vec<U32> & Result<V.Error,U32>) -> V.Vec<U32> & Search:
  (lines,r) = pair
  (lines,split_read(lo,hi,mid,pos,r))

def search_step(lines: V.Vec<U32>, +lo: U32, +hi: U32, pos: U32, close: Bool) -> V.Vec<U32> & Search:
  match close:
    case True{}: (lines,Found{lo})
    case False{}:
      +mid = (lo + ((hi - lo : U32) / 2 : U32) : U32)
      search_read(lo,hi,mid,pos,V.Vec.get(U32,lines,mid))

def search(fuel: Nat, +pos: U32, pair: V.Vec<U32> & Search) -> V.Vec<U32> & Search:
  match fuel pair:
    case 0n Tuple{lines,Searching{lo,hi}}: (lines,BadIndex{})
    case 0n Tuple{lines,Found{line}}: (lines,Found{line})
    case 0n Tuple{lines,BadIndex{}}: (lines,BadIndex{})
    case 1n+f Tuple{lines,Found{line}}: (lines,Found{line})
    case 1n+f Tuple{lines,BadIndex{}}: (lines,BadIndex{})
    case 1n+f Tuple{lines,Searching{+lo,+hi}}:
      search(f,pos,search_step(lines,lo,hi,pos,U32.is_le((hi - lo : U32),1)))

def location_read(line: U32, pos: U32, r: Result<V.Error,U32>) -> Result<T.Error,T.Location>:
  match r:
    case Fail{e}: Fail{T.IndexInvariant{}}
    case Done{start}: Done{T.Location{line,(pos - start : U32)}}

def locate_read(id: U32, n: U32, chars: V.Vec<Char>, line: U32, pos: U32, pair: V.Vec<U32> & Result<V.Error,U32>) -> Source & Result<T.Error,T.Location>:
  (lines,r) = pair
  (Buffer{id,n,chars,lines},location_read(line,pos,r))

def location_finish(id: U32, n: U32, chars: V.Vec<Char>, lines: V.Vec<U32>, pos: U32, state: Search) -> Source & Result<T.Error,T.Location>:
  match state:
    case BadIndex{}: (Buffer{id,n,chars,lines},Fail{T.IndexInvariant{}})
    case Searching{lo,hi}: (Buffer{id,n,chars,lines},Fail{T.IndexInvariant{}})
    case Found{+line}:
      locate_read(id,n,chars,line,pos,V.Vec.get(U32,lines,line))

def locate_searched(id: U32, n: U32, chars: V.Vec<Char>, pos: U32, pair: V.Vec<U32> & Search) -> Source & Result<T.Error,T.Location>:
  (lines,state) = pair
  location_finish(id,n,chars,lines,pos,state)

def locate_counted(id: U32, n: U32, chars: V.Vec<Char>, +pos: U32, pair: V.Vec<U32> & U32) -> Source & Result<T.Error,T.Location>:
  (lines,count) = pair
  locate_searched(id,n,chars,pos,search(25n,pos,(lines,Searching{0,count})))

def locate_if(s: Source, +pos: U32, valid: Bool) -> Source & Result<T.Error,T.Location>:
  match s valid:
    case Buffer{id,n,chars,lines} False{}: (Buffer{id,n,chars,lines},Fail{T.Bounds{}})
    case Buffer{id,n,chars,lines} True{}:
      locate_counted(id,n,chars,pos,V.Vec.length(U32,lines))

def Source.locate(s: Source, +pos: U32) -> Source & Result<T.Error,T.Location>:
  match s:
    case Buffer{id,+n,chars,lines}:
      locate_if(Buffer{id,n,chars,lines},pos,U32.is_le(pos,n))

def offset_valid(start: U32, col: U32, valid: Bool) -> Result<T.Error,U32>:
  match valid:
    case False{}: Fail{T.Bounds{}}
    case True{}: Done{(start + col : U32)}

def offset_bound(+start: U32, +col: U32, next: Result<V.Error,U32>) -> Result<T.Error,U32>:
  match next:
    case Fail{e}: Fail{T.IndexInvariant{}}
    case Done{end}: offset_valid(start,col,U32.is_lt(col,(end - start : U32)))

def offset_next(start: U32, col: U32, pair: V.Vec<U32> & Result<V.Error,U32>) -> V.Vec<U32> & Result<T.Error,U32>:
  (lines,b) = pair
  (lines,offset_bound(start,col,b))

def offset_line(lines: V.Vec<U32>, +line: U32, +col: U32, n: U32, start: Result<V.Error,U32>, last: Bool) -> V.Vec<U32> & Result<T.Error,U32>:
  match start last:
    case Fail{e} False{}: (lines,Fail{T.Bounds{}})
    case Fail{e} True{}: (lines,Fail{T.Bounds{}})
    case Done{+a} True{}: (lines,offset_valid(a,col,U32.is_le(col,(n - a : U32))))
    case Done{a} False{}:
      offset_next(a,col,V.Vec.get(U32,lines,(line + 1 : U32)))

def offset_finish(id: U32, n: U32, chars: V.Vec<Char>, pair: V.Vec<U32> & Result<T.Error,U32>) -> Source & Result<T.Error,U32>:
  (lines,r) = pair
  (Buffer{id,n,chars,lines},r)

def offset_read(id: U32, +n: U32, chars: V.Vec<Char>, line: U32, col: U32, last: Bool, pair: V.Vec<U32> & Result<V.Error,U32>) -> Source & Result<T.Error,U32>:
  (lines,a) = pair
  offset_finish(id,n,chars,offset_line(lines,line,col,n,a,last))

def offset_counted(id: U32, n: U32, chars: V.Vec<Char>, +line: U32, col: U32, pair: V.Vec<U32> & U32) -> Source & Result<T.Error,U32>:
  (lines,count) = pair
  offset_read(id,n,chars,line,col,U32.is_eq(line,(count - 1 : U32)),V.Vec.get(U32,lines,line))

def Source.offset(s: Source, loc: T.Location) -> Source & Result<T.Error,U32>:
  match s loc:
    case Buffer{id,n,chars,lines} T.Location{line,col}:
      offset_counted(id,n,chars,line,col,V.Vec.length(U32,lines))
