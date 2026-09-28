import Base

# The compiler prints a whole checked tree in one call: one 100,000-character line.
def main() -> IO(Unit):
  IO.print(String.repeat("0123456789",10000n))
