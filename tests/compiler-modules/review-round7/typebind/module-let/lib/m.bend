type Flag is Type:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  Flag = x
  y : Flag = On{}
  y
