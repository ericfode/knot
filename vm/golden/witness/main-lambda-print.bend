import Base

def main() -> IO(Unit):
  R => k => IO.print("direct")(R, k)
