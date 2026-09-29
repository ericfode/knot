import Base

type Light is Type:
  Dark{}
  Lit{}

def tick(x: Light) -> IO(Light):
  import "./lib/tick.js"

def main() -> Light:
  Lit{}
