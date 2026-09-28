import Base

def main() -> IO(Unit):
  IO.print("a\u{D800}b")
