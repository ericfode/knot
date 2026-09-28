(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func (result i32)))
  (type (;2;) (func (result i32)))
  (type (;3;) (func (result i32)))
  (type (;4;) (func (result i32)))
  (type (;5;) (func (result i32)))
  (type (;6;) (func (result i32)))
  (type (;7;) (func (result i32)))
  (type (;8;) (func (result i32)))
  (type (;9;) (func (result i32)))
  (type (;10;) (func (result i32)))
  (type (;11;) (func (result i32)))
  (type (;12;) (func (result i32)))
  (type (;13;) (func (result i32)))
  (type (;14;) (func (result i32)))
  (type (;15;) (func (result i32)))
  (type (;16;) (func (result i32)))
  (type (;17;) (func (param i32) (result i32)))
  (func (;0;) (type 0) (param i32) (result i32)
    (local i32 i32)
    local.get 0
    i32.load
    local.set 1
    local.get 0
    i32.load offset=4
    local.set 2
    local.get 2)
  (func (;1;) (type 1) (result i32)
    (local i32 i32)
    i32.const 1
    local.set 0
    i32.const 8
    call 17
    local.set 1
    local.get 1
    i32.const 0
    i32.store
    local.get 1
    local.get 0
    i32.store offset=4
    local.get 1
    call 0)
  (func (;2;) (type 2) (result i32)
    (local i32)
    call 1
    local.set 0
    call 1)
  (func (;3;) (type 3) (result i32)
    (local i32)
    call 2
    local.set 0
    call 2)
  (func (;4;) (type 4) (result i32)
    (local i32)
    call 3
    local.set 0
    call 3)
  (func (;5;) (type 5) (result i32)
    (local i32)
    call 4
    local.set 0
    call 4)
  (func (;6;) (type 6) (result i32)
    (local i32)
    call 5
    local.set 0
    call 5)
  (func (;7;) (type 7) (result i32)
    (local i32)
    call 6
    local.set 0
    call 6)
  (func (;8;) (type 8) (result i32)
    (local i32)
    call 7
    local.set 0
    call 7)
  (func (;9;) (type 9) (result i32)
    (local i32)
    call 8
    local.set 0
    call 8)
  (func (;10;) (type 10) (result i32)
    (local i32)
    call 9
    local.set 0
    call 9)
  (func (;11;) (type 11) (result i32)
    (local i32)
    call 10
    local.set 0
    call 10)
  (func (;12;) (type 12) (result i32)
    (local i32)
    call 11
    local.set 0
    call 11)
  (func (;13;) (type 13) (result i32)
    (local i32)
    call 12
    local.set 0
    call 12)
  (func (;14;) (type 14) (result i32)
    (local i32)
    call 13
    local.set 0
    call 13)
  (func (;15;) (type 15) (result i32)
    (local i32)
    call 14
    local.set 0
    call 14)
  (func (;16;) (type 16) (result i32)
    call 15)
  (func (;17;) (type 17) (param i32) (result i32)
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
  (export "f0" (func 1))
  (export "f1" (func 2))
  (export "f2" (func 3))
  (export "f3" (func 4))
  (export "f4" (func 5))
  (export "f5" (func 6))
  (export "f6" (func 7))
  (export "f7" (func 8))
  (export "f8" (func 9))
  (export "f9" (func 10))
  (export "f10" (func 11))
  (export "f11" (func 12))
  (export "f12" (func 13))
  (export "f13" (func 14))
  (export "f14" (func 15))
  (export "main" (func 16)))
