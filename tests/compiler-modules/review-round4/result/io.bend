import Base

type Light is Type:
  Dark{}
  Lit{}

def tick() -> IO(Unit):
  IO.pure(Unit, Unit{})

def main() -> Light:
  Lit{}
