import Base
import ./LAWS.bend as L

def L.not_involution(x):
  match x:
    case False{}: {==}
    case True{}: {==}

def L.and_associative(x,y,z):
  match x:
    case False{}: {==}
    case True{}: {==}

def L.or_associative(x,y,z):
  match x:
    case False{}: {==}
    case True{}: {==}

def L.de_morgan(x,y):
  match x:
    case False{}: {==}
    case True{}: {==}

def L.lt_is_unequal():
  {==}

def L.eq_is_equal():
  {==}

def L.gt_is_unequal():
  {==}

def L.unit_unique(x):
  match x:
    case Unit{}: {==}
