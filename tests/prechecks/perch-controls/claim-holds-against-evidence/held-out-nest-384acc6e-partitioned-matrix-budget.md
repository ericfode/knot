<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=nest; head=384acc6e83c5; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: research/compiler-fields/SPEC.md@384acc6e sha256=6282a40d4f838576f3d1e6f1ea231d9890031bb00796d2ee2b2b98792057a56b; src/check.bend@384acc6e sha256=195be2cc9318974a84487ef598984dda7f3f05869d12277f78d136b1151f8355 -->
# Claim
research/compiler-fields/SPEC.md:73-75 (section: Observations and bounds) - verbatim text:

> Expanded matches additionally receive
> 4096 matrix steps, partitioned among constructor branches; an exhausted
> partition reports Exhausted check budget.

# Evidence
Evidence: the declarations that use the stated number, at head.

`src/check.bend:237-312` (declaration using the budget 4096)
```
  237  def run(fuel: Nat, mode: Mode, +catalog: C.Catalog, +current: U32, +scope: E.Scope) -> Result<S.Error,C.Checked>:
  238    match fuel mode catalog scope:
  239      case 0n _ _ _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
  240      case 1n+ +n Expression{S.Variable{+token},+wanted} _ _:
  241        S.bind(C.Binding,C.Checked,E.lookup(scope,token),binding =>
  242          S.bind(C.Checked,C.Checked,variable(binding,token,scope,term => run(n,Rebuild{term},catalog,current,scope)),value => expected(token,wanted,value)))
  243      case 1n+ +n Expression{S.Constructor{+token,+args},+wanted} C.Catalog{+types,sigs} _:
  244        S.bind(G.ConstructorRef,C.Checked,G.find_constructor(types,token,0),+reference =>
  245          S.bind(List<&2,C.Parameter>,C.Checked,G.field_signature(reference,types),+params =>
  246            constructor(reference,args,token,wanted,params,u => run(n,Arguments{args,params,token},catalog,current,scope))))
  247      case 1n+ +n Expression{S.Call{+token,+args},+wanted} C.Catalog{types,sigs} _:
  248        S.bind(G.FunctionRef,C.Checked,G.find_function(sigs,token,0),reference =>
  249          S.bind(G.FunctionRef,C.Checked,callable(reference,token,current,scope),call =>
  250            call_body(call,token,wanted,current,scope,params => run(n,Arguments{args,params,token},catalog,current,scope))))
  251      case 1n+ +n Expression{S.Binding{+token,+q,ann,+value,+body},+wanted} C.Catalog{+types,sigs} E.Scope{bindings,+next,from,live,smaller}:
  252        S.choose(Result<S.Error,C.Checked>,U32.is_eq(next,4096),u => C.exhausted(C.Checked,token),u =>
  253          S.bind(Maybe<&2,U32>,C.Checked,annotation(types,ann),target =>
  254            S.bind(C.Checked,C.Checked,run(n,Expression{value,target},catalog,current,E.live_scope(scope,q)),+initial =>
  255              binding_body(initial,token,q,types,scope,extended =>
  256                S.bind(C.Checked,C.Checked,run(n,Expression{body,wanted},catalog,current,extended),checked => let_result(initial,checked,token,next,q))))))
  257      case 1n+ +n Expression{S.Match{token,S.Remainder{name,level,tags},Nil{}},wanted} C.Catalog{types,sigs} _:
  258        empty_remainder(tags,token,level,types,scope,wanted)
  259      case 1n+ +n Expression{S.Decision{+token,+column,S.Constructor{+ctor,+args},+yes,+no},+wanted} C.Catalog{+types,sigs} _:
  260        +pat : S.Node = S.Constructor{ctor,args}
  261        S.bind(C.Binding,C.Checked,M.column_binding(column,scope),+binding =>
  262          decision_body(binding,token,column,ctor,types,scope,wanted,+level => +tag => +tags =>
  263            S.bind(G.ConstructorRef,C.Checked,G.find_constructor(types,ctor,0),reference =>
  264            S.bind(P.Fields,C.Checked,P.branch(scope,level,reference,pat,types),opened =>
  265              arm_scope(opened,bound => +fields =>
  266                S.bind(C.Checked,C.Checked,run(n,Expression{yes,wanted},catalog,current,bound),positive =>
  267                  S.bind(C.Checked,C.Checked,run(n,Expression{no,wanted},catalog,current,E.residual(scope,binding,List.is_empty(&2,S.Token,tags))),negative =>
  268                    decision_arms(positive,negative,tag,fields,tags,level,types,scope))))))))
  269      case 1n+ +n Expression{S.Match{+token,+value,+arms},+wanted} C.Catalog{+types,sigs} _:
  270        S.choose(Result<S.Error,C.Checked>,M.flat(value,arms),u =>
  271          S.bind(C.Binding,C.Checked,E.scrutinee(value,scope),binding =>
  272            match_body(binding,token,arms,types,scope,wanted,level =>
  273              run(n,Arms{arms,token,level,wanted},catalog,current,scope))),u =>
  274          S.bind(S.Node,C.Checked,M.start(n,token,value,arms,types),node =>
  275            run(n,Expression{node,wanted},catalog,current,scope)))
  276      case 1n+ +n Expression{S.Matrix{token,columns,rows,+work},+wanted} C.Catalog{types,sigs} _:
  277        S.bind(M.Expansion,C.Checked,M.expand(n,S.Matrix{token,columns,rows,work},types,scope,work),tree =>
  278          run(n,Expression{M.expanded(tree),wanted},catalog,current,scope))
  279      case 1n+ +n Expression{S.Alias{token,level,mark,+body},+wanted} C.Catalog{types,sigs} _:
  280        S.bind(E.Scope,C.Checked,M.alias(scope,token,level,mark,types),bound =>
  281          run(n,Expression{body,wanted},catalog,current,bound))
  282      case 1n+ +n Expression{node,wanted} _ _: C.internal(C.Checked,"expression-node")
  283      case 1n+ +n Arguments{Nil{},Nil{},token} _ _:
  284        Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
  285      case 1n+ +n Arguments{Con{head,+tail},Con{C.Parameter{name,q,type_id},+rest},+token} _ _:
  286        S.bind(C.Checked,C.Checked,run(n,Expression{head,Some{type_id}},catalog,current,E.live_scope(scope,q)),checked =>
  287          S.bind(C.Checked,C.Checked,run(n,Arguments{tail,rest,token},catalog,current,scope),remaining => prepend_argument(checked,remaining,token)))
  288      case 1n+ +n Arguments{nodes,params,token} _ _: C.invalid(C.Checked,"call-arity",token)
  289      case 1n+ +n Arms{Nil{},token,level,wanted} _ _:
  290        Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
  291      case 1n+ +n Arms{Con{S.Arm{arm,+pat,+body},+tail},+token,+level,+wanted} C.Catalog{+types,sigs} _:
  292        S.bind(G.ConstructorRef,C.Checked,pattern(pat,types),+reference =>
  293          arm_body(reference,+tag =>
  294            S.bind(P.Fields,C.Checked,P.branch(scope,level,reference,pat,types),opened =>
  295              arm_scope(opened,bound => +fields =>
  296                S.bind(C.Checked,C.Checked,run(n,Expression{body,wanted},catalog,current,bound),checked =>
  297                  S.bind(C.Checked,C.Checked,run(n,Arms{tail,token,level,wanted},catalog,current,scope),remaining => prepend_arm(tag,fields,checked,remaining)))))))
  298      case 1n+ +n Arms{nodes,token,level,wanted} _ _: C.internal(C.Checked,"arm-node")
  299      case 1n+ +n Rebuild{C.Value{token,+type_id,tag}} _ _:
  300        Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
  301      case 1n+ +n Rebuild{C.Reference{+token,level,type_id}} _ E.Scope{bindings,next,open,live,smaller}:
  302        S.bind(C.Binding,C.Checked,E.find_level(bindings,level),binding =>
  303          variable(binding,token,scope,term => run(n,Rebuild{term},catalog,current,scope)))
  304      case 1n+ +n Rebuild{C.Construct{+token,+type_id,+tag,+params,args}} _ _:
  305        S.bind(C.Checked,C.Checked,run(n,RebuildArguments{args,params,token},catalog,current,scope),value => rebuilt(value,token,type_id,tag,params))
  306      case 1n+ +n Rebuild{other} _ _: C.internal(C.Checked,"refinement-node")
  307      case 1n+ +n RebuildArguments{Nil{},Nil{},token} _ _:
  308        Done{C.Checked{C.Sequence{Nil{}},0,Nil{}}}
  309      case 1n+ +n RebuildArguments{Con{head,+tail},Con{C.Parameter{name,q,type_id},+rest},+token} _ _:
  310        S.bind(C.Checked,C.Checked,run(n,Rebuild{head},catalog,current,E.live_scope(scope,q)),checked =>
  311          S.bind(C.Checked,C.Checked,run(n,RebuildArguments{tail,rest,token},catalog,current,scope),remaining => prepend_argument(checked,remaining,token)))
  312      case 1n+ +n RebuildArguments{terms,params,token} _ _: C.internal(C.Checked,"refinement-arity")
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
