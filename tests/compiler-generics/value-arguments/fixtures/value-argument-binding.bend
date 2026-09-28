type Flag is Data:
  Off{}
  On{}

type Tag<f: Flag> is Type:
  Tag{}

def main() -> Flag:
  t: Tag<On{}> = Tag{}
  On{}
