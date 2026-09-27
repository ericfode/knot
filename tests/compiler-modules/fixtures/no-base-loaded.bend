type Light is Type:
  Dark{}
  Lit{}

def main() -> Light:
  Bool.pick(Light, True{}, Lit{}, Dark{})
