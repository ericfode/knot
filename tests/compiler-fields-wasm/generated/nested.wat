(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func (param i32 i32) (result i32)))
  (type (;2;) (func (param i32 i32) (result i32)))
  (type (;3;) (func (result i32)))
  (type (;4;) (func (param i32) (result i32)))
  (func (;0;) (type 0) (param i32) (result i32)
    (local i32 i32 i32 i32 i32)
    local.get 0
    i32.load
    local.set 1
    local.get 0
    i32.load offset=4
    local.set 2
    local.get 2
    i32.load
    local.set 3
    local.get 2
    i32.load offset=4
    local.set 4
    local.get 2
    i32.load offset=8
    local.set 5
    local.get 5)
  (func (;1;) (type 1) (param i32 i32) (result i32)
    (local i32 i32 i32 i32 i32)
    local.get 0
    local.set 2
    local.get 1
    local.set 3
    i32.const 12
    call 4
    local.set 4
    local.get 4
    i32.const 0
    i32.store
    local.get 4
    local.get 2
    i32.store offset=4
    local.get 4
    local.get 3
    i32.store offset=8
    local.get 4
    local.set 5
    i32.const 8
    call 4
    local.set 6
    local.get 6
    i32.const 0
    i32.store
    local.get 6
    local.get 5
    i32.store offset=4
    local.get 6)
  (func (;2;) (type 2) (param i32 i32) (result i32)
    local.get 0
    local.get 1
    call 1
    call 0)
  (func (;3;) (type 3) (result i32)
    i32.const 0
    i32.const 1
    call 2)
  (func (;4;) (type 4) (param i32) (result i32)
    (local i32)
    global.get 0
    local.set 1
    local.get 0
    i32.const 65536
    global.get 0
    i32.sub
    i32.gt_u
    if  ;; label = @1
      unreachable
    end
    global.get 0
    local.get 0
    i32.add
    global.set 0
    local.get 1)
  (memory (;0;) 1 1)
  (global (;0;) (mut i32) (i32.const 0))
  (export "read" (func 0))
  (export "build" (func 1))
  (export "observe" (func 2))
  (export "main" (func 3)))
