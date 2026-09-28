import Base

def probe(s: String) -> String:
  match s:
    case SNil{}: "empty"
    case SCon{h,t}: "nonempty"

def main() -> IO(Unit):
  IO.bind(Unit,Unit,IO.print("a"),u => IO.print(probe(SCon{Chr{55296},SNil{}})))
