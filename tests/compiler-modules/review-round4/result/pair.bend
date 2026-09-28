import Base

type Light is Type:
  Dark{}
  Lit{}

def both() -> Light & Light:
  (Lit{}, Dark{})

def main() -> Light:
  Lit{}
