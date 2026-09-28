import Base

def shown(result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.print(String.concat(["Fail ",U32.show(code)," ",message]))
    case Done{value}: IO.print(String.append("Done ",value))

# IO.get_env is a Base effect outside the compiler's host surface.
def main() -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,String>,Unit,IO.get_env("KNOT_IO_FIXTURE_UNSET"),shown)
