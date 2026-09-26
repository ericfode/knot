import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/release.bend as CheckedRelease
import 0xc409b77d3230ca33374caf6b0993f0cb/main.bend as Text
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as Bytes

def assert(ok: Bool, label: String) -> IO(Unit):
  match ok:
    case True{}:
      IO.print(label)
    case False{}:
      IO.die(Unit,1,"remote mismatch: " ++ label)

def equal(a: List<&2,U32>, b: List<&2,U32>) -> Bool:
  match a b:
    case Nil{} Nil{}:
      True{}
    case Con{x,xs} Con{y,ys}:
      Bool.and(U32.is_eq(x,y),equal(xs,ys))
    case Nil{} Con{y,ys}:
      False{}
    case Con{x,xs} Nil{}:
      False{}

def output(result: Result<Bytes.Error,Bytes.Builder>) -> IO(Unit):
  match result:
    case Fail{err}:
      IO.die(Unit,1,"remote byte construction failed")
    case Done{+b}:
      assert(Bool.and(equal(Bytes.finish(b),[0,97,115,109,1,0,0,0]),U32.is_eq(Bytes.length(b),8)),"REMOTE bytes:pass")

def join(a: Result<Bytes.Error,Bytes.Builder>, b: Result<Bytes.Error,Bytes.Builder>) -> IO(Unit):
  match a b:
    case Done{x} Done{y}:
      output(Bytes.compose(x,y))
    case Done{x} Fail{err}:
      IO.die(Unit,1,"remote second chunk failed")
    case Fail{err} Done{y}:
      IO.die(Unit,1,"remote first chunk failed")
    case Fail{err} Fail{other}:
      IO.die(Unit,1,"remote chunks failed")

def main() -> IO(Unit):
  do IO<Unit>:
    assert(String.eq(Text.finish(Text.character(Text.compose(Text.fragment("wasm"),Text.fragment("🙂")),Chr{10})),"wasm🙂\n"),"REMOTE text:pass")
    join(Bytes.fragment(8,[0,97,115,109]),Bytes.fragment(4,[1,0,0,0]))
