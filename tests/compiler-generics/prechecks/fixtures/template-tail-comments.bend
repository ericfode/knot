type Flag is Data:
  Off{}
  On{}

def f(a: Flag, # ordinary binder

  # the next binder is not leading
  ~b: Flag) -> Flag:
  On{}
