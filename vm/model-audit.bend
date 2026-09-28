import Base
import ./model-cli.bend as C

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),C.audit_arguments)
