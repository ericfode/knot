type Flag is Data:
  Off{}
  On{}

type Tag<f: Flag> is Type:
  Tag{}

def take(x: Tag<On{}>) -> Flag:
  On{}

def main() -> Flag:
  take(Tag{})
