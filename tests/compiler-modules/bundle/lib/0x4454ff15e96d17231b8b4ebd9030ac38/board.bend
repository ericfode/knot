import ./mark.bend as M

def first() -> M.Mark:
  M.swap(M.Nought{})

def twice(m: M.Mark) -> M.Mark:
  M.swap(M.swap(m))
