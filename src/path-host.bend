import Base
import ./syntax.bend as S

# Host observation only: exact component spelling and absence of symlinks.
# Missing paths still reach the ordinary open/missing-module classifier.
def inspect(path: String) -> IO(Result<&1,&2,U32 & String,Bool>):
  import "./host/path-identity.c"
  import "./host/path-identity.js"

def classified(result: Result<&1,&2,U32 & String,Bool>) -> Result<S.Error,Unit>:
  match result:
    case Fail{(code,message)}:
      Fail{S.Host{"path-identity",String.append(U32.show(code),String.append("\t",message))}}
    case Done{canonical}:
      S.choose(Result<S.Error,Unit>,canonical,u => Done{Unit{}},u =>
        Fail{S.Unsupported{"load","path-identity",S.At{0,0,0,0}}})

def check(path: String, next: Result<S.Error,Unit> -> IO(Unit)) -> IO(Unit):
  IO.bind(Result<&1,&2,U32 & String,Bool>,Unit,inspect(path),result => next(classified(result)))
