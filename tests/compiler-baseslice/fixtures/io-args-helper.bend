import Base

type Light is Data:
  Dark{}
  Lit{}

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Nil{}: IO.die(Unit, 5, "HostFailure\targuments\tusage")
    case Con{head, tail}: IO.die(Unit, 0, head)

# The CLI entry shape: IO.bind(List<String>, Unit, IO.args(), arguments).
# No enum entry reaches it.
def entry() -> IO(Unit):
  IO.bind(List<String>, Unit, IO.args(), arguments)

def main() -> Light:
  Bool.pick(Light, Nat.is_eq(List.length(&1, String, ["compile", "a.bend"]), 2n), Lit{}, Dark{})
