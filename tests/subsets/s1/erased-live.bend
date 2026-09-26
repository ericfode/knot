type Flag is Type:
  Off{}
  On{}

def observe(-ghost: Flag) -> Flag:
  match ghost:
    case Off{}: On{}
    case On{}: Off{}

def main() -> Flag:
  observe(Off{})
