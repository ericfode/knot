import Base
import ./protocol.bend as P
import ./store.bend as S
import ./scheduler.bend as J
import ./model.bend as M

def config() -> P.Config:
  P.Config{4,6,8,1,3,3,8,3,32}

law unsupported_preserves:
  for +cfg: P.Config
  for +store: P.Store
  for +joins: List<&2,P.Join>
  for status: U32
  for reply: U32
  {M.step(P.Command{99,0,0,0,0,0,0,0},P.State{cfg,store,joins,status,reply})
    == P.State{cfg,store,joins,2,0} : P.State}

law reserved_preserves:
  for +cfg: P.Config
  for +store: P.Store
  for +joins: List<&2,P.Join>
  for status: U32
  for reply: U32
  {M.step(P.Command{3,0,1,0,0,0,1,0},P.State{cfg,store,joins,status,reply})
    == P.State{cfg,store,joins,1,0} : P.State}

law span_exact_max:
  for +state: P.State
  {M.span(state,4294967294,1,1,4294967295) == P.result(state,0,4294967295) : P.State}

law span_overflow_preserves:
  for +state: P.State
  {M.span(state,4294967294,2,1,4294967295) == P.result(state,3,0) : P.State}

law span_product_preserves:
  for +state: P.State
  {M.span(state,16,1073741824,4,4294967295) == P.result(state,3,0) : P.State}

law type_cannot_share:
  for +id: U32
  for +tag: U32
  for objects: List<&2,P.Object>
  for limit: U32
  {S.retained(P.Object{id,0,1,tag,Nil{}},objects,limit) == Fail{2} : Result<U32,List<&2,P.Object>>}

law move_once:
  for +tag: U32
  {S.move(S.move(P.State{config(),P.Store{2,0,0,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
    [1,0,0,0,0,0],Nil{}},[P.empty_join()],0,0},0,1),0,2)
    == P.State{config(),P.Store{2,0,0,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
      [0,1,0,0,0,0],Nil{}},[P.empty_join()],1,0} : P.State}

law decrement_keeps_alias:
  for +tag: U32
  {S.clean(1n,P.State{config(),P.Store{2,0,0,[P.Object{1,1,2,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
    [1,0,0,0,0,0],[1]},[P.empty_join()],0,0})
    == P.State{config(),P.Store{2,0,0,[P.Object{1,1,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
      [1,0,0,0,0,0],Nil{}},[P.empty_join()],0,0} : P.State}

law open_transfers:
  for +tag: U32
  {S.open(P.State{config(),P.Store{3,0,0,[P.Object{1,0,1,tag,Nil{}},P.Object{2,0,1,9,[1]},P.Free{},P.Free{}],
    [2,0,0,0,0,0],Nil{}},[P.empty_join()],0,0},0,1,1)
    == P.State{config(),P.Store{3,0,1,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
      [0,1,0,0,0,0],Nil{}},[P.empty_join()],0,0} : P.State}

law shared_open_atomic:
  for +tag: U32
  {S.open(P.State{config(),P.Store{3,0,0,[P.Object{1,1,2,tag,Nil{}},P.Object{2,1,2,9,[1,1]},P.Free{},P.Free{}],
    [2,2,0,0,0,0],Nil{}},[P.empty_join()],0,0},0,2,2)
    == P.State{config(),P.Store{3,0,0,[P.Object{1,1,2,tag,Nil{}},P.Object{2,1,2,9,[1,1]},P.Free{},P.Free{}],
      [2,2,0,0,0,0],Nil{}},[P.empty_join()],3,0} : P.State}

law cleanup_retains_work:
  for +tag: U32
  {S.clean(1n,P.State{config(),P.Store{3,0,0,[P.Object{1,0,1,tag,Nil{}},P.Object{2,0,1,9,[1]},P.Free{},P.Free{}],
    [0,0,0,0,0,0],[2]},[P.empty_join()],0,0})
    == P.State{config(),P.Store{3,0,1,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
      [0,0,0,0,0,0],[1]},[P.empty_join()],3,0} : P.State}

law reader_retains_work:
  for +tag: U32
  {S.clean(1n,P.State{config(),P.Store{2,1,0,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
    [0,0,0,0,0,0],[1]},[P.empty_join()],0,0})
    == P.State{config(),P.Store{2,1,0,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
      [0,0,0,0,0,0],[1]},[P.empty_join()],3,0} : P.State}

law identity_retires:
  {S.construct(P.initial(P.Config{1,1,1,0,0,1,1,1,1}),0,0,7,0,0)
    == P.State{P.Config{1,1,1,0,0,1,1,1,1},P.Store{0,0,0,[P.Object{1,0,1,7,Nil{}}],[1],Nil{}},Nil{},0,0} : P.State}

law stale_preserves_source:
  for +tag: U32
  {J.deliver(P.State{config(),P.Store{2,0,0,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
    [1,0,0,0,0,0],Nil{}},[P.Join{2,1,1,0,0,0,5,0,[0]}],0,0},0,1,0,0)
    == P.State{config(),P.Store{2,0,0,[P.Object{1,0,1,tag,Nil{}},P.Free{},P.Free{},P.Free{}],
      [1,0,0,0,0,0],Nil{}},[P.Join{2,1,1,0,0,0,5,0,[0]}],1,0} : P.State}

law right_before_left:
  {J.deliver(J.deliver(P.State{config(),P.Store{3,0,0,[P.Object{1,0,1,7,Nil{}},P.Object{2,0,1,9,Nil{}},P.Free{},P.Free{}],
    [1,2,0,0,0,0],Nil{}},[P.Join{1,1,2,0,0,0,5,0,[0,0]}],0,0},0,1,1,1),0,1,0,0)
    == P.State{config(),P.Store{3,0,0,[P.Object{1,0,1,7,Nil{}},P.Object{2,0,1,9,Nil{}},P.Free{},P.Free{}],
      [0,0,0,0,0,0],Nil{}},[P.Join{1,2,2,2,1,0,5,0,[1,2]}],0,0} : P.State}

law nary_once:
  {M.run([P.Command{9,0,1,2,2,0,0,0},P.Command{9,0,1,0,0,0,0,0},P.Command{9,0,1,1,1,0,0,0},P.Command{9,0,1,1,3,0,0,0}],
    P.State{config(),P.Store{5,0,0,[P.Object{1,0,1,1,Nil{}},P.Object{2,0,1,2,Nil{}},P.Object{3,0,1,3,Nil{}},P.Object{4,0,1,4,Nil{}}],
      [1,2,3,4,0,0],Nil{}},[P.Join{1,1,3,0,0,0,5,0,[0,0,0]}],0,0})
    == P.State{config(),P.Store{5,0,0,[P.Object{1,0,1,1,Nil{}},P.Object{2,0,1,2,Nil{}},P.Object{3,0,1,3,Nil{}},P.Object{4,0,1,4,Nil{}}],
      [0,0,0,4,0,0],Nil{}},[P.Join{1,2,3,3,1,0,5,0,[1,2,3]}],1,0} : P.State}

law cancel_owns_pending:
  {J.cancel(P.State{config(),P.Store{3,0,0,[P.Object{1,1,1,7,Nil{}},P.Object{2,0,1,9,Nil{}},P.Free{},P.Free{}],
    [0,0,0,0,0,1],Nil{}},[P.Join{1,1,2,1,0,0,5,1,[0,2]}],0,0},0,1)
    == P.State{config(),P.Store{3,0,0,[P.Object{1,1,1,7,Nil{}},P.Object{2,0,1,9,Nil{}},P.Free{},P.Free{}],
      [0,0,0,0,0,0],[1,2]},[P.Join{1,3,2,0,0,0,5,1,[0,0]}],0,0} : P.State}

law empty_join_once:
  {J.resume(J.resume(J.start(P.initial(config()),0,0,7,5,1),0,1,0),0,1,0)
    == P.State{config(),P.Store{1,0,0,[P.Free{},P.Free{},P.Free{},P.Free{}],[0,0,0,0,0,0],Nil{}},
      [P.Join{1,4,0,0,1,7,5,1,Nil{}}],1,0} : P.State}
