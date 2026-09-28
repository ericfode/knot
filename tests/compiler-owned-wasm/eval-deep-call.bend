import Base
import ../../src/driver.bend as D
import ../../src/eval-cli.bend as E

def main() -> IO(Unit):
  D.load("tests/compiler-fields-wasm/fixtures/deep-call.bend",D.Limits{65536n,4096n,4096n},
    book => E.evaluate(book,"main",E.Request{1048576n,Nil{}}))
