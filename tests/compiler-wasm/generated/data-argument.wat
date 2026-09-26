(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func (param i32) (result i32)))
  (type (;2;) (func (result i32)))
  (func (;0;) (type 0) (param i32) (result i32)
    local.get 0)
  (func (;1;) (type 1) (param i32) (result i32)
    local.get 0
    call 0)
  (func (;2;) (type 2) (result i32)
    i32.const 1
    call 1)
  (export "twice" (func 0))
  (export "f" (func 1))
  (export "main" (func 2)))
