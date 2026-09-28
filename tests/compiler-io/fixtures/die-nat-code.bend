import Base

# The exit code is a U32, not a Nat.
def main() -> IO(Unit):
  IO.die(Unit,3n,"stop")
