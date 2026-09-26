import Base
import 0x88d5b48c03f82f217d3a2aa0656744f4/release.bend as Release
import 0x88d5b48c03f82f217d3a2aa0656744f4/conformance.bend as Checks
import 0x88d5b48c03f82f217d3a2aa0656744f4/main.bend as S
import 0x88d5b48c03f82f217d3a2aa0656744f4/types.bend as T

def read(r: Result<T.Error,String>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{x}: String.eq(x,"😀")

def extracted(pair: S.Source & Result<T.Error,String>) -> Bool:
  (s,r) = pair
  read(r)

def built(r: Result<T.Error,S.Source>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: extracted(S.Source.extract(s,T.Span{91,1,2}))

def main() -> Bool:
  Bool.and(Checks.all(),Bool.and(String.eq(Release.main(),"😀"),built(S.Source.new(91,"a😀\nβ"))))
