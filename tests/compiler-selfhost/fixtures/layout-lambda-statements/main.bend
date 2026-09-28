# Lambda bodies continued on new lines inside open argument lists: the
# pipeline of src/driver.bend:33-37 closed by a dedented `name)`, and a lambda
# body of let statements then a term, each on its own line (closures'
# LambdaStatements, src/check.bend binding bodies).
type Answer is Data:
  No{}
  Yes{}

type Step is Data:
  Stuck{}
  Next{value: Answer}

def flip(a: Answer) -> Answer:
  match a:
    case No{}: Yes{}
    case Yes{}: No{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def guard(a: Answer) -> Step:
  match a:
    case No{}: Stuck{}
    case Yes{}: Next{Yes{}}

def bind(s: Step, next: Answer -> Step) -> Step:
  match s:
    case Stuck{}: Stuck{}
    case Next{v}: next(v)

def finish(s: Step, last: Answer -> Answer) -> Answer:
  match s:
    case Stuck{}: No{}
    case Next{v}: last(v)

def pipeline(a: Answer, b: Answer, last: Answer -> Answer) -> Answer:
  finish(
    bind(guard(a),x =>
      bind(guard(b),y =>
        Next{both(x,y)})),
    last)

def staged(a: Answer, +b: Answer) -> Answer:
  finish(bind(guard(a),x =>
    +m = flip(x)
    +k = both(flip(m),b)
    Next{both(k,flip(m))}),u => u)

def meet(a: Answer, b: Answer) -> Answer:
  pipeline(a,b,v => v)

def main() -> Answer:
  staged(Yes{},Yes{})
