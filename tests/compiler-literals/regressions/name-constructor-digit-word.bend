import Base

# A name is words joined by single dots, and a word starts with a letter or `_`: `A.1` does not.
type Answer is Type:
  No{}
  Yes{}

type Letter is Type:
  A.1{}

def main() -> Answer:
  Yes{}
