import Base

# An IO value is affine: binding the same action twice consumes it twice.
def twice(action: IO(Unit)) -> IO(Unit):
  IO.bind(Unit,Unit,action,u => action)

def main() -> IO(Unit):
  twice(IO.print("x"))
