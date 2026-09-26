(module
  (type (;0;) (func (result i32)))
  (type (;1;) (func (result i32)))
  (func (;0;) (type 0) (result i32)
    i32.const 1)
  (func (;1;) (type 1) (result i32)
    call 0)
  (export "f" (func 0))
  (export "main" (func 1)))
