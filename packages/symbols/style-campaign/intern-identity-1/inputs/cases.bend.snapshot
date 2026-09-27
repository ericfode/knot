import Base
import ./protocol.bend as P
import ./observe.bend as O
import ./model.bend as M
import ./main.bend as S

def check(+commands: List<&2,P.Command>, +limit: U32) -> Bool:
  P.trace_eq(O.run(commands,limit),M.run(commands,limit))

def repeat() -> List<&2,P.Command>:
  [P.Intern{"a"},P.Intern{"ab"},P.Intern{"a"},P.Find{"ab"},P.Find{"missing"},P.Resolve{0},P.Resolve{1},P.Length{},P.Limit{}]

def full() -> List<&2,P.Command>:
  [P.Intern{"a"},P.Intern{"b"},P.Intern{"a"},P.Find{"b"},P.Resolve{0},P.Resolve{1},P.Resolve{4294967295},P.Length{},P.Limit{}]

def unicode() -> List<&2,P.Command>:
  [P.Intern{""},P.Intern{SCon{Chr{0},SNil{}}},P.Intern{"é"},P.Intern{"é"},P.Intern{"🪢"},P.Intern{"é"},P.Find{"é"},P.Resolve{0},P.Resolve{1},P.Resolve{2},P.Resolve{3},P.Resolve{4},P.Resolve{5}]

def growth(count: Nat) -> List<&2,P.Command>:
  match count:
    case 0n: [P.Find{"id1"},P.Resolve{0},P.Resolve{31},P.Resolve{32},P.Resolve{64},P.Resolve{65},P.Resolve{4294967295}]
    case 1n+ +p: Con{P.Intern{String.append("id",Nat.show(1n+p))},growth(p)}

def all_cases() -> Bool:
  Bool.and(check(repeat(),4),Bool.and(check(full(),1),Bool.and(check(unicode(),6),Bool.and(check(full(),0),check(growth(65n),65)))))

def alphabet() -> List<&2,P.Command>:
  [P.Intern{""},P.Intern{"a"},P.Intern{"ab"},P.Find{""},P.Find{"a"},P.Find{"ab"},P.Resolve{0},P.Resolve{1},P.Resolve{2},P.Resolve{4294967295},P.Length{},P.Limit{}]

def enumerate(depth: Nat, +prefix: List<&2,P.Command>, +limit: U32) -> Bool:
  match depth:
    case 0n: check(List.reverse(&2,P.Command,prefix),limit)
    case 1n+ +p:
      Bool.and(enumerate(p,Con{P.Intern{""},prefix},limit),Bool.and(enumerate(p,Con{P.Intern{"a"},prefix},limit),Bool.and(enumerate(p,Con{P.Intern{"ab"},prefix},limit),Bool.and(enumerate(p,Con{P.Find{""},prefix},limit),Bool.and(enumerate(p,Con{P.Find{"a"},prefix},limit),Bool.and(enumerate(p,Con{P.Find{"ab"},prefix},limit),Bool.and(enumerate(p,Con{P.Resolve{0},prefix},limit),Bool.and(enumerate(p,Con{P.Resolve{1},prefix},limit),Bool.and(enumerate(p,Con{P.Resolve{2},prefix},limit),Bool.and(enumerate(p,Con{P.Resolve{4294967295},prefix},limit),Bool.and(enumerate(p,Con{P.Length{},prefix},limit),Bool.and(enumerate(p,Con{P.Limit{},prefix},limit),True{}))))))))))))

def exhaustive() -> Bool:
  Bool.and(enumerate(3n,Nil{},0),Bool.and(enumerate(3n,Nil{},1),Bool.and(enumerate(3n,Nil{},2),enumerate(3n,Nil{},3))))
