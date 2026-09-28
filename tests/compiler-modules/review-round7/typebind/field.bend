type Light is Data:
  Dark{}
  Lit{}

type Box is Data:
  Box{Light: Light, v: Light}

def main() -> Light:
  Lit{}
