(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func (param i32) (result i32)))
  (type (;2;) (func (result i32)))
  (type (;3;) (func (result i32)))
  (type (;4;) (func (result i32)))
  (type (;5;) (func (param i32) (result i32)))
  (func (;0;) (type 0) (param i32) (result i32)
    (local i32 i32)
    local.get 0
    local.set 1
    i32.const 8
    call 5
    local.set 2
    local.get 2
    i32.const 1
    i32.store
    local.get 2
    local.get 1
    i32.store offset=4
    local.get 2)
  (func (;1;) (type 1) (param i32) (result i32)
    (local i32 i32 i32 i32)
    local.get 0
    i32.load
    local.set 1
    local.get 1
    i32.const 0
    i32.eq
    if (result i32)  ;; label = @1
      i32.const 0
    else
      local.get 0
      i32.load offset=4
      local.set 2
      local.get 2
      i32.load
      local.set 3
      local.get 3
      i32.const 0
      i32.eq
      if (result i32)  ;; label = @2
        i32.const 1
      else
        local.get 2
        i32.load offset=4
        local.set 4
        i32.const 0
      end
    end)
  (func (;2;) (type 2) (result i32)
    (local i32)
    i32.const 4
    call 5
    local.set 0
    local.get 0
    i32.const 0
    i32.store
    local.get 0
    call 1)
  (func (;3;) (type 3) (result i32)
    (local i32 i32 i32)
    i32.const 4
    call 5
    local.set 0
    local.get 0
    i32.const 0
    i32.store
    local.get 0
    local.set 1
    i32.const 8
    call 5
    local.set 2
    local.get 2
    i32.const 1
    i32.store
    local.get 2
    local.get 1
    i32.store offset=4
    local.get 2
    call 0
    call 1)
  (func (;4;) (type 4) (result i32)
    (local i32)
    i32.const 4
    call 5
    local.set 0
    local.get 0
    i32.const 0
    i32.store
    local.get 0
    call 0
    call 1)
  (func (;5;) (type 5) (param i32) (result i32)
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
  (export "add_one" (func 0))
  (export "is_one" (func 1))
  (export "zero" (func 2))
  (export "two" (func 3))
  (export "main" (func 4)))
