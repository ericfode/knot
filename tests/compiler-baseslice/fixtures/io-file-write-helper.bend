import Base

type Light is Data:
  Dark{}
  Lit{}

def written(result: Result<&1, &1, U32 & String, Unit>, count: U32) -> IO(Unit):
  match result:
    case Fail{(code, message)}: IO.die(Unit, 5, String.concat(["HostFailure\twrite\t", U32.show(code), "\t", message]))
    case Done{u}: IO.die(Unit, 0, String.append("Built\t", U32.show(count)))

# compile-cli.write_pair, output_opened and emitted, with the do block written
# as IO.bind. No enum entry reaches them.
def write_pair(pair: File & Result<&1, &1, U32 & String, Unit>, count: U32) -> IO(Unit):
  (file, result) = pair
  IO.bind(Unit, Unit, File.close(file), u => written(result, count))

def output_opened(result: Result<&1, &1, U32 & String, File>, +bytes: List<&2, U32>) -> IO(Unit):
  match result:
    case Fail{(code, message)}: IO.die(Unit, 5, String.concat(["HostFailure\toutput-open\t", U32.show(code), "\t", message]))
    case Done{file}:
      IO.bind(File & Result<&1, &1, U32 & String, Unit>, Unit, File.write_bytes(file, bytes), pair => write_pair(pair, U32.from_nat(List.length(&2, U32, bytes))))

def emitted(path: String, +bytes: List<&2, U32>) -> IO(Unit):
  IO.bind(Result<&1, &1, U32 & String, File>, Unit, File.open(path, "w"), result => output_opened(result, bytes))

def main() -> Light:
  Bool.pick(Light, U32.is_eq(U32.from_nat(List.length(&2, U32, [0, 97, 115, 109])), 4), Lit{}, Dark{})
