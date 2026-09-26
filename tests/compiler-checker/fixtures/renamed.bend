type Flag is Type:
  Off{}
  On{}
def toggle(input: Flag) -> Flag:
  match input:
    case Off{}: On{}
    case On{}: Off{}
def main() -> Flag:
  toggle(Off{})
