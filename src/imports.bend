import Base
import ./syntax.bend as S

type Import is Data:
  Import{path: String, alias: String}

type Header is Data:
  Header{imports: List<&2,Import>, body: String}

type Target is Data:
  Target{path: String, namespace: String}

# Reversed pieces bound the host stack independently of source length.
def split_chars(text: String, +separator: Char, +piece: String, +done: List<&2,String>) -> List<&2,String>:
  match text:
    case SNil{}: List.reverse(&2,String,Con{String.reverse(piece),done})
    case SCon{+c,+tail}:
      S.choose(List<&2,String>,Char.is_eq(c,separator),u =>
        split_chars(tail,separator,"",Con{String.reverse(piece),done}),u =>
        split_chars(tail,separator,SCon{c,piece},done))

def split(text: String, separator: Char) -> List<&2,String>:
  split_chars(text,separator,"",Nil{})

def first(xs: List<&2,String>) -> String:
  match xs:
    case Nil{}: ""
    case Con{x,rest}: x

def member(+key: String, xs: List<&2,String>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{x,rest}: Bool.or(String.eq(key,x),member(key,rest))

def word_tail(text: String, +dash: Bool) -> Bool:
  match text:
    case SNil{}: True{}
    case SCon{+c,rest}:
      Bool.and(Bool.or(S.alpha(Char.to_u32(c)),Bool.or(S.digit(Char.to_u32(c)),
        Bool.and(dash,Char.is_eq(c,'-')))),word_tail(rest,dash))

def plain(text: String, +dash: Bool) -> Bool:
  match text:
    case SNil{}: False{}
    case SCon{c,rest}: Bool.and(S.alpha(Char.to_u32(c)),word_tail(rest,dash))

def lower_hex(text: String) -> Bool:
  match text:
    case SNil{}: True{}
    case SCon{c,rest}:
      +n = Char.to_u32(c)
      Bool.and(Bool.or(S.digit(n),Bool.and(U32.is_ge(n,97),U32.is_le(n,102))),lower_hex(rest))

def hash_head(+text: String) -> Bool:
  Bool.and(String.starts_with(text,"0x"),Bool.and(Bool.not(String.eq(text,"0x")),lower_hex(String.drop(text,2n))))

def hashed(path: String) -> Bool:
  hash_head(first(split(path,'/')))

def names(parts: List<&2,String>) -> Bool:
  match parts:
    case Nil{}: True{}
    case Con{part,rest}: Bool.and(plain(part,True{}),names(rest))

def relative(parts: List<&2,String>) -> Bool:
  match parts:
    case Nil{}: False{}
    case Con{+part,+rest}:
      S.choose(Bool,String.eq(part,".."),u => relative(rest),u => names(Con{part,rest}))

def without_suffix(path: String) -> String:
  String.reverse(String.drop(String.reverse(path),5n))

def valid_parts(parts: List<&2,String>) -> Bool:
  match parts:
    case Nil{}: False{}
    case Con{+part,+rest}:
      S.choose(Bool,hash_head(part),u => Bool.and(Bool.not(List.is_empty(&2,String,rest)),names(rest)),u =>
      S.choose(Bool,String.eq(part,"."),u => relative(rest),u => relative(Con{part,rest})))

def valid(+path: String) -> Bool:
  Bool.and(String.ends_with(path,".bend"),valid_parts(split(without_suffix(path),'/')))

# A reversed segment stack makes both dot rules local.
def parent(stack: List<&2,String>, +absolute: Bool) -> List<&2,String>:
  match stack:
    case Nil{}: S.choose(List<&2,String>,absolute,u => Nil{},u => [".."])
    case Con{+head,+tail}:
      S.choose(List<&2,String>,String.eq(head,".."),u => Con{"..",Con{head,tail}},u => tail)

def segments(parts: List<&2,String>, +absolute: Bool, +stack: List<&2,String>) -> List<&2,String>:
  match parts:
    case Nil{}: List.reverse(&2,String,stack)
    case Con{+head,tail}:
      +next = S.choose(List<&2,String>,Bool.or(String.eq(head,""),String.eq(head,".")),u => stack,u =>
        S.choose(List<&2,String>,String.eq(head,".."),u => parent(stack,absolute),u => Con{head,stack}))
      segments(tail,absolute,next)

def normalize(+path: String) -> String:
  +absolute = String.starts_with(path,"/")
  String.append(Bool.pick(String,absolute,"/",""),String.join(segments(split(path,'/'),absolute,Nil{}),"/"))

def directory_parts(parts: List<&2,String>) -> String:
  match parts:
    case Nil{}: ""
    case Con{last,rest}: String.join(List.reverse(&2,String,rest),"/")

def directory(path: String) -> String:
  directory_parts(List.reverse(&2,String,split(path,'/')))

def beside(path: String, relative: String) -> String:
  normalize(String.concat([directory(path),"/",relative]))

def join(+dir: String, +path: String) -> String:
  S.choose(String,String.eq(dir,""),u => normalize(path),u => normalize(String.concat([dir,"/",path])))

def parents(parts: List<&2,String>) -> List<&2,String>:
  match parts:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{"..",parents(tail)}

def relative_parts(+left: List<&2,String>, +right: List<&2,String>) -> List<&2,String>:
  match left right:
    case Con{lh,lt} Con{rh,rt}:
      S.choose(List<&2,String>,String.eq(lh,rh),u => relative_parts(lt,rt),u => List.append(&2,String,parents(left),right))
    case _ _: List.append(&2,String,parents(left),right)

def relative_path(from: String, target: String) -> String:
  String.join(relative_parts(segments(split(from,'/'),False{},Nil{}),segments(split(target,'/'),False{},Nil{})),"/")

def bundle_prefix(+bundle: String) -> String:
  S.choose(String,String.ends_with(bundle,"/"),u => bundle,u => String.append(bundle,"/"))

def resolve(+importer: String, +namespace: String, +bundle: String, +path: String) -> Result<S.Error,Target>:
  +target = S.choose(String,hashed(path),u => join(bundle,path),u => join(directory(importer),path))
  +inside = String.starts_with(target,bundle_prefix(bundle))
  +space = S.choose(String,inside,u => without_suffix(String.drop(target,String.length(bundle_prefix(bundle)))),u =>
    without_suffix(join(directory(namespace),relative_path(directory(importer),target))))
  S.choose(Result<S.Error,Target>,Bool.and(hashed(namespace),Bool.not(hashed(space))),u =>
    Fail{S.Invalid{"load","package-escape",S.At{0,0,0,0}}},u =>
  S.choose(Result<S.Error,Target>,Bool.and(inside,Bool.not(hashed(space))),u =>
    Fail{S.Invalid{"load","import-path",S.At{0,0,0,0}}},u => Done{Target{target,space}}))

def pushed(+word: String, +rest: List<&2,String>) -> List<&2,String>:
  S.choose(List<&2,String>,String.is_empty(word),u => rest,u => Con{String.reverse(word),rest})

# A '#' that begins a word begins the comment; one inside a word belongs to it,
# as in the seed's `import\s+(\S+)`. Words accumulate reversed.
def words(text: String, +word: String, +rest: List<&2,String>) -> List<&2,String>:
  match text:
    case SNil{}: List.reverse(&2,String,pushed(word,rest))
    case SCon{+c,+tail}:
      S.choose(List<&2,String>,Bool.or(Char.is_eq(c,' '),Char.is_eq(c,'\t')),u =>
        words(tail,"",pushed(word,rest)),u =>
      S.choose(List<&2,String>,Bool.and(String.is_empty(word),Char.is_eq(c,'#')),u =>
        List.reverse(&2,String,rest),u =>
        words(tail,SCon{c,word},rest)))

# The seed splits header lines on JavaScript whitespace, which also covers form
# feed, vertical tab, U+00A0 and U+FEFF. Only printable ASCII, space and tab are
# classified here; any other header character is Unsupported.
def printable(text: String) -> Bool:
  match text:
    case SNil{}: True{}
    case SCon{c,tail}:
      +n = Char.to_u32(c)
      S.choose(Bool,Bool.or(U32.is_eq(n,9),Bool.and(U32.is_ge(n,32),U32.is_le(n,126))),u => printable(tail),u => False{})

def aliased(+path: String, +as: String, +alias: String, +at: S.At) -> Result<S.Error,Import>:
  S.choose(Result<S.Error,Import>,Bool.and(String.eq(as,"as"),plain(alias,False{})),u =>
  S.choose(Result<S.Error,Import>,String.contains(first(split(path,'/')),"@"),u =>
    Fail{S.Unsupported{"load","named-package",at}},u =>
  S.choose(Result<S.Error,Import>,String.starts_with(path,"/"),u =>
    Fail{S.Unsupported{"load","absolute-import",at}},u =>
  S.choose(Result<S.Error,Import>,valid(path),u => Done{Import{path,alias}},u =>
    Fail{S.Invalid{"load","import-path",at}}))),u => Fail{S.Invalid{"load","import-alias",at}})

# An alias ends with its identifier: a '#' glued to it starts the comment.
def import_words(parts: List<&2,String>, +at: S.At) -> Result<S.Error,Import>:
  match parts:
    case Con{word,Con{+path,Nil{}}}:
      S.choose(Result<S.Error,Import>,String.eq(path,"Base"),u => Done{Import{"Base",""}},u =>
        Fail{S.Invalid{"load","import-alias",at}})
    case Con{word,Con{+path,Con{+as,Con{+alias,+rest}}}}:
      S.choose(Result<S.Error,Import>,Bool.or(List.is_empty(&2,String,rest),String.contains(alias,"#")),u =>
        aliased(path,as,first(split(alias,'#')),at),u => Fail{S.Invalid{"load","import-syntax",at}})
    case _: Fail{S.Invalid{"load","import-syntax",at}}

def alias(item: Import) -> String:
  match item:
    case Import{path,name}: name

def push_import(result: Result<S.Error,Import>, +seen: List<&2,String>, next: Import -> Result<S.Error,Header>) -> Result<S.Error,Header>:
  match result:
    case Fail{error}: Fail{error}
    case Done{+item}:
      S.choose(Result<S.Error,Header>,Bool.and(Bool.not(String.eq(alias(item),"")),member(alias(item),seen)),u =>
        Fail{S.Invalid{"load","duplicate-alias",S.At{0,0,0,0}}},u => next(item))

def join_lines(lines: List<&2,String>, +text: String) -> String:
  match lines:
    case Nil{}: text
    case Con{line,tail}: join_lines(tail,String.concat([line,"\n",text]))

def body_lines(reversed: List<&2,String>) -> String:
  match reversed:
    case Nil{}: ""
    case Con{line,tail}: join_lines(tail,line)

def foreign(parts: List<&2,String>) -> Bool:
  match parts:
    case Con{word,Con{path,rest}}: String.starts_with(path,"\"")
    case _: False{}

def header_lines(lines: List<&2,String>, +open: Bool, +row: U32,
  +imports: List<&2,Import>, +seen: List<&2,String>, +body: List<&2,String>) -> Result<S.Error,Header>:
  match lines:
    case Nil{}: Done{Header{List.reverse(&2,Import,imports),body_lines(body)}}
    case Con{+line,+tail}:
      +parts = words(line,"",Nil{})
      +is_import = String.eq(first(parts),"import")
      S.choose(Result<S.Error,Header>,Bool.and(open,Bool.not(printable(line))),u =>
        Fail{S.Unsupported{"load","header-character",S.At{0,0,row,0}}},u =>
      S.choose(Result<S.Error,Header>,Bool.and(open,is_import),u =>
        push_import(import_words(parts,S.At{0,0,row,0}),seen,+item =>
          header_lines(tail,True{},U32.add(row,1),Con{item,imports},Con{alias(item),seen},Con{"",body})),u =>
      S.choose(Result<S.Error,Header>,Bool.and(Bool.not(open),is_import),u =>
        S.choose(Result<S.Error,Header>,foreign(parts),u =>
          Fail{S.Unsupported{"check","foreign-definition",S.At{0,0,row,0}}},u =>
          Fail{S.Invalid{"load","import-after-declaration",S.At{0,0,row,0}}}),u =>
        header_lines(tail,Bool.and(open,List.is_empty(&2,String,parts)),U32.add(row,1),imports,seen,Con{line,body}))))

def header(text: String) -> Result<S.Error,Header>:
  header_lines(split(text,'\n'),True{},1,Nil{},Nil{},Nil{})
