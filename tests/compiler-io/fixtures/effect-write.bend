import Base

# IO.write is a Base effect outside the compiler's host surface.
def main() -> IO(Unit):
  do IO<Unit>:
    IO.write("no newline;")
    IO.print("then a line")
