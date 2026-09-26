import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S

# Only the published checked builder API constructs buffers here.
def checked(result: Result<B.Error,B.Builder>) -> Result<S.Error,B.Builder>:
  match result:
    case Done{b}: Done{b}
    case Fail{B.Limit{}}: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case Fail{B.InvalidByte{value}}: Fail{S.Internal{"emit","invalid-byte"}}

def bytes(cap: U32, values: List<&2,U32>) -> Result<S.Error,B.Builder>:
  checked(B.fragment(cap,values))

def join(left: B.Builder, right: B.Builder) -> Result<S.Error,B.Builder>:
  checked(B.compose(left,right))

def concat(+cap: U32, parts: List<&1,Result<S.Error,B.Builder>>) -> Result<S.Error,B.Builder>:
  match parts:
    case Nil{}: Done{B.empty(cap)}
    case Con{Fail{e},tail}: Fail{e}
    case Con{Done{+head},tail}:
      S.bind(B.Builder,B.Builder,concat(cap,tail),rest => join(head,rest))

# Positive signed LEB uses a 6-bit final group. U32 LEB uses 7.
# Five groups cover U32; callers request signed encoding only for enum ordinals.
def groups(fuel: Nat, +signed: Bool, +value: U32) -> Result<S.Error,List<&2,U32>>:
  match fuel:
    case 0n: Fail{S.Internal{"emit","leb-width"}}
    case 1n+n:
      S.choose(Result<S.Error,List<&2,U32>>,U32.is_lt(value,Bool.pick(U32,signed,64,128)),u => Done{[value]},u =>
        S.bind(List<&2,U32>,List<&2,U32>,groups(n,signed,U32.shrn(value,7n)),tail => Done{Con{U32.add(U32.and(value,127),128),tail}}))

def unsigned(+cap: U32, value: U32) -> Result<S.Error,B.Builder>:
  S.bind(List<&2,U32>,B.Builder,groups(5n,False{},value),values => bytes(cap,values))

def positive_signed(+cap: U32, +value: U32) -> Result<S.Error,B.Builder>:
  S.choose(Result<S.Error,B.Builder>,U32.is_le(value,2147483647),u =>
    S.bind(List<&2,U32>,B.Builder,groups(5n,True{},value),values => bytes(cap,values)),u => Fail{S.Internal{"emit","signed-range"}})

def chars(text: String) -> List<&2,U32>:
  match text:
    case SNil{}: Nil{}
    case SCon{head,tail}: Con{Char.to_u32(head),chars(tail)}

def sized(+cap: U32, +body: B.Builder) -> Result<S.Error,B.Builder>:
  concat(cap,[unsigned(cap,B.length(body)),Done{body}])

def name(+cap: U32, text: String) -> Result<S.Error,B.Builder>:
  S.bind(B.Builder,B.Builder,bytes(cap,chars(text)),body => sized(cap,body))

def section(+cap: U32, id: U32, body: B.Builder) -> Result<S.Error,B.Builder>:
  concat(cap,[bytes(cap,[id]),sized(cap,body)])
