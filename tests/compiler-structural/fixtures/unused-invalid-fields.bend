type Flag is Data:
  Off{}
  On{}
type Unused is Data:
  Unused{x: Owned}
type Owned is Type:
  Owned{}
def main() -> Flag:
  On{}
