import Base

type Light is Type:
  Dark{}
  Lit{}

type Box is Type:
  Box{v: Light}

def open(b: Box) -> Light:
  match b:
    case Box{True}: True

def main() -> Light:
  Dark{}
