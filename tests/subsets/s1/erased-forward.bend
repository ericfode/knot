type Flag is Type:
  Off{}
  On{}

def take(-ghost: Flag, value: Flag) -> Flag:
  value

def forward(-ghost: Flag) -> Flag:
  take(ghost,On{})

def main() -> Flag:
  forward(Off{})
