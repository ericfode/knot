import Base

# The <- binder is annotated U32, but IO.print answers Unit.
def main() -> IO(Unit):
  do IO<Unit>:
    x : U32 <- IO.print("x")
    IO.print("y")
