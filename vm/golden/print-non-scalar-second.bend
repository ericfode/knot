import Base

def say(s: String) -> IO(Unit):
  IO.bind(Unit,Unit,IO.print("a"),u => IO.print(s))

def main() -> IO(Unit):
  say(SCon{Chr{55296},SNil{}})
