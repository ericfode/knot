type Flag is Type:
  Off{}
  On{}

type Box is Type:
  Box{Flag: Flag}
  Other{v: Flag}
