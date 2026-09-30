import Base

def step() -> IO(Unit):
  R => k => IO.print("alpha")(R)(u => IO.print("beta")(R)(k))

def main() -> IO(Unit):
  step()
