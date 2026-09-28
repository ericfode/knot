import Base

type Light is Type:
  Dark{}
  Lit{}

type Box is Type:
  Box{p: Light & Light}

def main() -> Light:
  Lit{}
