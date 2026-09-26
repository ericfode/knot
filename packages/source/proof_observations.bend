import Base
import ./main.bend as S
import ./types.bend as T

def text_pair(pair: S.Source & String) -> Result<T.Error,String>:
  (s,t) = pair
  Done{t}

def text(r: Result<T.Error,S.Source>) -> Result<T.Error,String>:
  match r:
    case Fail{e}: Fail{e}
    case Done{s}: text_pair(S.Source.text(s))

def file_pair(pair: S.Source & U32) -> Result<T.Error,U32>:
  (s,n) = pair
  Done{n}

def file(r: Result<T.Error,S.Source>) -> Result<T.Error,U32>:
  match r:
    case Fail{e}: Fail{e}
    case Done{s}: file_pair(S.Source.file(s))

def length(r: Result<T.Error,S.Source>) -> Result<T.Error,U32>:
  match r:
    case Fail{e}: Fail{e}
    case Done{s}: file_pair(S.Source.length(s))

def lines(r: Result<T.Error,S.Source>) -> Result<T.Error,U32>:
  match r:
    case Fail{e}: Fail{e}
    case Done{s}: file_pair(S.Source.line_count(s))

def scalar_pair(pair: S.Source & U32) -> U32:
  (s,n) = pair
  n

def size(s: S.Source) -> U32:
  scalar_pair(S.Source.length(s))

def identity(s: S.Source) -> U32:
  scalar_pair(S.Source.file(s))
