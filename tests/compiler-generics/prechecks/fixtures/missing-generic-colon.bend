type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type # c
  Box{value: A}
