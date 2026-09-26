type Flag is Data:
  Off{}
  On{}
type Owned is Type:
  Owned{}
type Middle is Type:
  Middle{x: Owned}
type Outer is Data:
  Outer{x: Middle}
def main() -> Flag:
  On{}
