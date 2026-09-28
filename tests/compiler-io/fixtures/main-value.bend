import Base

# main may answer any IO(A); the host discards the final value.
def main() -> IO(U32):
  IO.bind(Unit,U32,IO.print("value discarded"),u => IO.pure(U32,7))
