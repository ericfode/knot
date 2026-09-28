import Base

type Light is Data:
  Dark{}
  Lit{}

def read_result(result: Result<&1, &1, U32 & String, String>) -> IO(Unit):
  match result:
    case Fail{(code, message)}: IO.die(Unit, 5, String.concat(["HostFailure\tread\t", U32.show(code), "\t", message]))
    case Done{text}: IO.die(Unit, 0, text)

# driver.read_pair, opened and load, with the do block written as IO.bind.
# No enum entry reaches them.
def read_pair(pair: File & Result<&1, &1, U32 & String, String>) -> IO(Unit):
  (file, result) = pair
  IO.bind(Unit, Unit, File.close(file), u => read_result(result))

def opened(result: Result<&1, &1, U32 & String, File>) -> IO(Unit):
  match result:
    case Fail{(code, message)}: IO.die(Unit, 5, String.concat(["HostFailure\topen\t", U32.show(code), "\t", message]))
    case Done{file}: IO.bind(File & Result<&1, &1, U32 & String, String>, Unit, File.read(file, 65537), read_pair)

def load(path: String) -> IO(Unit):
  IO.bind(Result<&1, &1, U32 & String, File>, Unit, File.open(path, "r"), opened)

def main() -> Light:
  Bool.pick(Light, String.eq(String.concat(["HostFailure\topen\t", U32.show(2), "\t", "gone"]), "HostFailure\topen\t2\tgone"), Lit{}, Dark{})
