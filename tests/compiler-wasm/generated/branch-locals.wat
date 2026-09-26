(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func (param i32 i32) (result i32)))
  (type (;2;) (func (result i32)))
  (func (;0;) (type 0) (param i32) (result i32)
    local.get 0)
  (func (;1;) (type 1) (param i32 i32) (result i32)
    (local i32 i32)
    local.get 0
    i32.const 0
    i32.eq
    if (result i32)  ;; label = @1
      local.get 1
      call 0
      local.set 2
      local.get 2
    else
      i32.const 0
      local.set 2
      i32.const 1
      local.set 3
      local.get 3
    end)
  (func (;2;) (type 2) (result i32)
    i32.const 0
    i32.const 0
    call 1)
  (export "identity" (func 0))
  (export "f" (func 1))
  (export "main" (func 2)))
