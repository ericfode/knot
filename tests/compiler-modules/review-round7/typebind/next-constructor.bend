type Light is Type:
  Dark{}
  Lit{}

type Box is Type:
  Box{Light: Light}
  Other{v: Light}

def main() -> Light:
  Lit{}
