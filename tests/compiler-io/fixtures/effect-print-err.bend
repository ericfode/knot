import Base

# IO.print_err is a Base effect outside the compiler's host surface.
def main() -> IO(Unit):
  do IO<Unit>:
    IO.print("to stdout")
    IO.print_err("to stderr")
