type Flag is Data:
  Off{}
  On{}
type Ghost is Type:
  Ghost{-value: Flag}
def main() -> Ghost:
  Ghost{On{}}
