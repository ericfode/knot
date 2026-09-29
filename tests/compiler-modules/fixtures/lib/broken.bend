type Value is Type:
  Good{}

type Other is Type:
  Wrong{}

def unused() -> Value:
  Wrong{}

def valid() -> Value:
  Good{}
