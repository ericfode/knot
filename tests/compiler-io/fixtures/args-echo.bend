import Base

def codes(s: String) -> String:
  match s:
    case SNil{}: ""
    case SCon{c,t}: String.concat([" ",U32.show(Char.to_u32(c)),codes(t)])

# Arguments arrive in order, without the program name.
def each(args: List<String>, +i: U32) -> IO(Unit):
  match args:
    case Nil{}: IO.print(String.append("argc ",U32.show(i)))
    case Con{+arg,rest}:
      do IO<Unit>:
        IO.print(String.concat(["[",arg,"]",codes(arg)]))
        each(rest,U32.add(i,1))

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),args => each(args,0))
