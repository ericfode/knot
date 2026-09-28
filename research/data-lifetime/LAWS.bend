import Base
import ./model.bend as M

law rejected_transaction_preserves_state:
  for +heap: M.Heap
  for +error: U32
  {M.commit(Fail{error},heap) == (heap,error) : M.Heap & U32}

law successful_transaction_publishes_state:
  for +before: M.Heap
  for +after: M.Heap
  {M.commit(Done{after},before) == (after,0) : M.Heap & U32}

law type_is_not_shareable:
  for +id: U32
  for +tag: U32
  {M.retained(M.Cell{id,0,tag,1,Nil{}},M.initial(1,32,2)) == Fail{2} : Result<U32,M.Heap>}

law count_ceiling_preserves_state:
  for +tag: U32
  {M.share(M.Heap{1,32,1,2,[M.Cell{1,1,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,3,3,0],Nil{}},0,1)
    == Fail{3} : Result<U32,M.Heap>}

law copied_leaf_has_distinct_owner:
  for +tag: U32
  {M.share(M.Heap{0,32,2,2,[M.Cell{1,1,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,2,2,0],Nil{}},0,1)
    == Done{M.Heap{0,32,2,3,[M.Cell{2,1,tag,1,Nil{}},M.Cell{1,1,tag,1,Nil{}}],[M.Holder{1,2},M.Holder{0,1}],Nil{},Nil{},[2,0,2,0,0,0,0,4,4,0],Nil{}}} : Result<U32,M.Heap>}

law counted_leaf_retains_one_record:
  for +tag: U32
  {M.share(M.Heap{1,32,2,2,[M.Cell{1,1,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,3,3,0],Nil{}},0,1)
    == Done{M.Heap{1,32,2,2,[M.Cell{1,1,tag,2,Nil{}}],[M.Holder{1,1},M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,1,0,0,3,3,0],Nil{}}} : Result<U32,M.Heap>}

law empty_capacity_rejects_allocation:
  for +policy: U32
  for +tag: U32
  {M.alloc(M.initial(policy,0,2),0,0,tag,Nil{}) == Fail{3} : Result<U32,M.Heap>}

law copied_allocation_installs_owner:
  for +tag: U32
  {M.alloc(M.initial(0,32,2),0,1,tag,Nil{})
    == Done{M.Heap{0,32,2,2,[M.Cell{1,1,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,2,2,0],Nil{}}} : Result<U32,M.Heap>}

law counted_allocation_starts_at_one:
  for +tag: U32
  {M.alloc(M.initial(1,32,2),0,1,tag,Nil{})
    == Done{M.Heap{1,32,2,2,[M.Cell{1,1,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,3,3,0],Nil{}}} : Result<U32,M.Heap>}

law copied_release_keeps_other_value:
  for +tag: U32
  {M.clean(1n,M.Heap{0,32,2,3,[M.Cell{2,1,tag,1,Nil{}},M.Cell{1,1,tag,1,Nil{}}],[M.Holder{1,2}],[1],Nil{},[2,0,2,0,0,0,0,4,4,1],Nil{}})
    == (M.Heap{0,32,2,3,[M.Cell{2,1,tag,1,Nil{}}],[M.Holder{1,2}],Nil{},Nil{},[2,1,2,0,0,0,1,2,4,1],Nil{}},0) : M.Heap & U32}

law shared_open_acquires_children:
  for +tag: U32
  {M.take(M.Heap{1,32,3,3,[M.Cell{2,1,5,2,[1]},M.Cell{1,1,tag,1,Nil{}}],[M.Holder{0,2},M.Holder{1,2}],Nil{},Nil{},[2,0,0,0,1,0,0,7,7,0],Nil{}},0,[2])
    == Done{M.Heap{1,32,3,3,[M.Cell{2,1,5,1,[1]},M.Cell{1,1,tag,2,Nil{}}],[M.Holder{2,1},M.Holder{1,2}],Nil{},Nil{},[2,0,0,1,2,1,0,7,7,0],Nil{}}} : Result<U32,M.Heap>}

law zero_budget_retains_obligation:
  for +policy: U32
  for +tag: U32
  {M.clean(0n,M.Heap{policy,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,0,0,0,2,2,1],Nil{}})
    == (M.Heap{policy,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,0,0,0,2,2,1],Nil{}},3) : M.Heap & U32}

law reader_blocks_reuse:
  for +policy: U32
  for +tag: U32
  {M.clean(1n,M.Heap{policy,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],Nil{},[1],[M.Holder{7,1}],[1,0,0,0,0,0,0,2,2,1],Nil{}})
    == (M.Heap{policy,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],Nil{},[1],[M.Holder{7,1}],[1,0,0,0,0,0,0,2,2,1],Nil{}},3) : M.Heap & U32}

law type_last_release_drops_once:
  for +tag: U32
  {M.clean(1n,M.Heap{0,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,0,0,0,2,2,1],Nil{}})
    == (M.Heap{0,32,2,2,Nil{},Nil{},Nil{},Nil{},[1,1,0,0,0,0,1,0,2,1],[tag]},0) : M.Heap & U32}

law data_first_release_keeps_alias:
  for +tag: U32
  {M.clean(1n,M.Heap{1,32,2,2,[M.Cell{1,1,tag,2,Nil{}}],[M.Holder{1,1}],[1],Nil{},[1,0,0,0,1,0,0,3,3,1],Nil{}})
    == (M.Heap{1,32,2,2,[M.Cell{1,1,tag,1,Nil{}}],[M.Holder{1,1}],Nil{},Nil{},[1,0,0,0,1,1,1,3,3,1],Nil{}},0) : M.Heap & U32}

law data_last_release_reclaims:
  for +tag: U32
  {M.clean(1n,M.Heap{1,32,2,2,[M.Cell{1,1,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,1,1,1,3,3,1],Nil{}})
    == (M.Heap{1,32,2,2,Nil{},Nil{},Nil{},Nil{},[1,1,0,0,1,2,2,0,3,1],Nil{}},0) : M.Heap & U32}

law consume_transfers_fields:
  {M.take(M.Heap{0,32,2,3,[M.Cell{2,0,13,1,[1]},M.Cell{1,0,7,1,Nil{}}],[M.Holder{0,2}],Nil{},Nil{},[2,0,0,0,0,0,0,5,5,0],Nil{}},0,[1])
    == Done{M.Heap{0,32,2,3,[M.Cell{1,0,7,1,Nil{}}],[M.Holder{1,1}],Nil{},Nil{},[2,1,0,1,0,0,0,2,5,0],Nil{}}} : Result<U32,M.Heap>}

law release_queues_without_disposal:
  for +tag: U32
  {M.release(M.Heap{0,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,2,2,0],Nil{}},0)
    == Done{M.Heap{0,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,0,0,0,2,2,1],Nil{}}} : Result<U32,M.Heap>}

law suspension_moves_one_holder:
  for +tag: U32
  {M.move(M.Heap{0,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],[M.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,2,2,0],Nil{}},0,10)
    == Done{M.Heap{0,32,2,2,[M.Cell{1,0,tag,1,Nil{}}],[M.Holder{10,1}],Nil{},Nil{},[1,0,0,0,0,0,0,2,2,0],Nil{}}} : Result<U32,M.Heap>}

law immutable_graph_rejects_backpatch:
  for +heap: M.Heap
  {M.step(M.Cycle{},heap) == (heap,2) : M.Heap & U32}
