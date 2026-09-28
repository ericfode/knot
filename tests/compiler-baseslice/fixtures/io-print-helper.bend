import Base

type Light is Data:
  Dark{}
  Lit{}

# compile-cli.written, verbatim. No enum entry reaches it.
def written(result: Result<&1, &1, U32 & String, Unit>, count: U32) -> IO(Unit):
  match result:
    case Fail{(code, message)}: IO.die(Unit, 5, String.concat(["HostFailure\twrite\t", U32.show(code), "\t", message]))
    case Done{u}: IO.print(String.append("Built\t", U32.show(count)))

def main() -> Light:
  Bool.pick(Light, String.eq(String.append("Built\t", U32.show(12)), "Built\t12"), Lit{}, Dark{})
