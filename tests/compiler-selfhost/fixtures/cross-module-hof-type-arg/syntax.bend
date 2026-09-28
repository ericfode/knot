# Local module for cross-module-hof: src/syntax.bend's generic continuation helpers.
import Base

type Error is Data:
  Unknown{}
  Late{}

def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def bind(-A: Data, -B: Data, result: Result<Error,A>, next: A -> Result<Error,B>) -> Result<Error,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)
