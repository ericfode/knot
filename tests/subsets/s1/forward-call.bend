type Flag is Type:
  Off{}
  On{}

def forward(x: Flag) -> Flag:
  flip(x)

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def main() -> Flag:
  forward(Off{})
