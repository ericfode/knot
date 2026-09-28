import Base
import ./model.bend as M
import ../../research/data-lifetime/model.bend as R

law allocator_installs_one_owner:
  for +value: U32
  {M.alloc(M.initial(16),0,value) == M.Allocated{M.Pool{65552,65552,Nil{},[M.Cell{65548,0,value}]},65548} : M.Allocation}

law allocator_round_trip_keeps_reusable_cell:
  for +value: U32
  {M.allocated_release(M.alloc(M.initial(16),0,value)) == (M.Pool{65552,65552,[M.Cell{65548,0,value}],Nil{}},0) : M.Pool & U32}

law allocator_reuses_exact_size_class:
  for +before: U32
  for +after: U32
  {M.alloc(M.Pool{65552,65552,[M.Cell{65548,0,before}],Nil{}},0,after)
    == M.Allocated{M.Pool{65552,65552,Nil{},[M.Cell{65548,0,after}]},65548} : M.Allocation}

law wrong_size_class_preserves_rejected_pool:
  for +value: U32
  for incoming: U32
  {M.alloc(M.Pool{65552,65552,[M.Cell{65548,0,value}],Nil{}},1,incoming)
    == M.Rejected{M.Pool{65552,65552,[M.Cell{65548,0,value}],Nil{}},3} : M.Allocation}

law full_allocator_preserves_live_owner:
  for +value: U32
  for incoming: U32
  {M.alloc(M.Pool{65552,65552,Nil{},[M.Cell{65548,0,value}]},0,incoming)
    == M.Rejected{M.Pool{65552,65552,Nil{},[M.Cell{65548,0,value}]},3} : M.Allocation}

law allocator_release_preserves_unrelated_owner:
  for +first: U32
  for +second: U32
  {M.release(M.Pool{65568,65568,Nil{},[M.Cell{65564,0,second},M.Cell{65548,0,first}]},65548)
    == (M.Pool{65568,65568,[M.Cell{65548,0,first}],[M.Cell{65564,0,second}]},0) : M.Pool & U32}

law duplicate_release_preserves_free_chain:
  for +value: U32
  {M.release(M.Pool{65552,65552,[M.Cell{65548,0,value}],Nil{}},65548)
    == (M.Pool{65552,65552,[M.Cell{65548,0,value}],Nil{}},5) : M.Pool & U32}

law counted_allocation_starts_with_one_obligation:
  for +tag: U32
  {R.alloc(R.initial(1,32,2),0,1,tag,Nil{})
    == Done{R.Heap{1,32,2,2,[R.Cell{1,1,tag,1,Nil{}}],[R.Holder{0,1}],Nil{},Nil{},[1,0,0,0,0,0,0,3,3,0],Nil{}}} : Result<U32,R.Heap>}

law first_release_preserves_shared_data:
  for +tag: U32
  {R.clean(1n,R.Heap{1,32,2,2,[R.Cell{1,1,tag,2,Nil{}}],[R.Holder{1,1}],[1],Nil{},[1,0,0,0,1,0,0,3,3,1],Nil{}})
    == (R.Heap{1,32,2,2,[R.Cell{1,1,tag,1,Nil{}}],[R.Holder{1,1}],Nil{},Nil{},[1,0,0,0,1,1,1,3,3,1],Nil{}},0) : R.Heap & U32}

law final_release_reclaims_data:
  for +tag: U32
  {R.clean(1n,R.Heap{1,32,2,2,[R.Cell{1,1,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,1,1,1,3,3,1],Nil{}})
    == (R.Heap{1,32,2,2,Nil{},Nil{},Nil{},Nil{},[1,1,0,0,1,2,2,0,3,1],Nil{}},0) : R.Heap & U32}

law shared_open_counts_both_repeated_edges:
  for +tag: U32
  {R.take(R.Heap{1,64,8,3,[R.Cell{2,1,5,2,[1,1]},R.Cell{1,1,tag,2,Nil{}}],[R.Holder{0,2},R.Holder{1,2}],Nil{},Nil{},[2,0,0,0,2,0,0,8,8,0],Nil{}},0,[2,3])
    == Done{R.Heap{1,64,8,3,[R.Cell{2,1,5,1,[1,1]},R.Cell{1,1,tag,4,Nil{}}],[R.Holder{3,1},R.Holder{2,1},R.Holder{1,2}],Nil{},Nil{},[2,0,0,2,4,1,0,8,8,0],Nil{}}} : Result<U32,R.Heap>}

law shared_open_overflow_preserves_all_obligations:
  for +tag: U32
  {R.step(R.Take{0,[2,3]},R.Heap{1,64,3,3,[R.Cell{2,1,5,2,[1,1]},R.Cell{1,1,tag,2,Nil{}}],[R.Holder{0,2},R.Holder{1,2}],Nil{},Nil{},[2,0,0,0,2,0,0,8,8,0],Nil{}})
    == (R.Heap{1,64,3,3,[R.Cell{2,1,5,2,[1,1]},R.Cell{1,1,tag,2,Nil{}}],[R.Holder{0,2},R.Holder{1,2}],Nil{},Nil{},[2,0,0,0,2,0,0,8,8,0],Nil{}},3) : R.Heap & U32}

law zero_budget_keeps_release_obligation:
  for +tag: U32
  {R.clean(0n,R.Heap{1,32,2,2,[R.Cell{1,0,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,0,0,0,2,2,1],Nil{}})
    == (R.Heap{1,32,2,2,[R.Cell{1,0,tag,1,Nil{}}],Nil{},[1],Nil{},[1,0,0,0,0,0,0,2,2,1],Nil{}},3) : R.Heap & U32}
