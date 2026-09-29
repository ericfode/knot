import Base

type Light is Type:
  Dark{}
  Lit{}

def main() -> Light:
  Bool.pick(Light, Bool.not(True{}), Lit{}, Dark{})
