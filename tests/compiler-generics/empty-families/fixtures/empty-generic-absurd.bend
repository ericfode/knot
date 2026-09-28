type Flag is Data:
  Off{}
  On{}

type Never<-A: Type> is Type:

def absurd(-A: Type, n: Never<A>) -> A:
  match n:

def main() -> Flag:
  On{}
