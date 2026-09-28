type Flag is Data:
  Off{}
  On{}

def link(k: Flag -> Flag) -> Flag -> Flag:
  x => k(x)

def link2(k: Flag -> Flag) -> Flag -> Flag:
  link(link(k))

def link4(k: Flag -> Flag) -> Flag -> Flag:
  link2(link2(k))

def link8(k: Flag -> Flag) -> Flag -> Flag:
  link4(link4(k))

def link16(k: Flag -> Flag) -> Flag -> Flag:
  link8(link8(k))

def link32(k: Flag -> Flag) -> Flag -> Flag:
  link16(link16(k))

def link64(k: Flag -> Flag) -> Flag -> Flag:
  link32(link32(k))

def link128(k: Flag -> Flag) -> Flag -> Flag:
  link64(link64(k))

def link256(k: Flag -> Flag) -> Flag -> Flag:
  link128(link128(k))

def link512(k: Flag -> Flag) -> Flag -> Flag:
  link256(link256(k))

def link1024(k: Flag -> Flag) -> Flag -> Flag:
  link512(link512(k))

def link2048(k: Flag -> Flag) -> Flag -> Flag:
  link1024(link1024(k))

def shallow(x: Flag) -> Flag:
  link(y => y)(x)

def deep(x: Flag) -> Flag:
  link2048(y => y)(x)

def main() -> Flag:
  deep(On{})
