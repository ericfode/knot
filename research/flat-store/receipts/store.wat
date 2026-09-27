(module
  (type (;0;) (func (param i32 i32 i32 i32) (result i32)))
  (type (;1;) (func (param i32 i32 i32) (result i32)))
  (type (;2;) (func (param i32 i32) (result i32)))
  (type (;3;) (func (param i32) (result i32)))
  (type (;4;) (func (param i32 i32 i32) (result i32)))
  (type (;5;) (func (param i32 i32 i32) (result i32)))
  (func (;0;) (type 0) (param i32 i32 i32 i32) (result i32)
    i32.const 0
    local.get 1
    i32.store offset=16
    i32.const 0
    local.get 2
    i32.store offset=20
    i32.const 0
    local.get 3
    i32.store offset=24
    local.get 0)
  (func (;1;) (type 1) (param i32 i32 i32) (result i32)
    (local i32 i32)
    global.get 0
    if  ;; label = @1
      i32.const 10
      return
    end
    local.get 1
    i32.const 4096
    i32.gt_u
    if  ;; label = @1
      i32.const 1
      return
    end
    i32.const 0
    local.get 0
    i32.store
    i32.const 0
    local.get 1
    i32.store offset=4
    i32.const 0
    local.get 2
    i32.store offset=8
    local.get 1
    i32.eqz
    if  ;; label = @1
      i32.const 0
      i32.const -1
      i32.store offset=12
    else
      i32.const 0
      i32.const 0
      i32.store offset=12
    end
    i32.const 0
    i32.const 0
    i32.store offset=28
    i32.const 0
    local.set 3
    block  ;; label = @1
      loop  ;; label = @2
        local.get 3
        local.get 1
        i32.ge_u
        br_if 1 (;@1;)
        local.get 3
        i32.const 16
        i32.mul
        i32.const 32
        i32.add
        local.set 4
        local.get 4
        i32.const 0
        i32.store
        local.get 4
        i32.const 0
        i32.store offset=4
        local.get 4
        i32.const 0
        i32.store offset=8
        local.get 3
        i32.const 1
        i32.add
        local.get 1
        i32.eq
        if  ;; label = @3
          local.get 4
          i32.const -1
          i32.store offset=12
        else
          local.get 4
          local.get 3
          i32.const 1
          i32.add
          i32.store offset=12
        end
        local.get 3
        i32.const 1
        i32.add
        local.set 3
        br 0 (;@2;)
      end
    end
    i32.const 1
    global.set 0
    i32.const 0
    i32.const -1
    i32.const -1
    i32.const 0
    call 0)
  (func (;2;) (type 2) (param i32 i32) (result i32)
    (local i32 i32 i32 i32 i32 i32 i32)
    global.get 0
    i32.eqz
    if  ;; label = @1
      i32.const 9
      return
    end
    local.get 0
    i32.const 0
    i32.load offset=4
    i32.ge_u
    if  ;; label = @1
      i32.const 3
      i32.const -1
      i32.const -1
      local.get 1
      call 0
      return
    end
    local.get 0
    i32.const 16
    i32.mul
    i32.const 32
    i32.add
    local.set 2
    local.get 2
    i32.load
    local.set 3
    local.get 3
    i32.const 2
    i32.eq
    if  ;; label = @1
      i32.const 8
      i32.const -1
      i32.const -1
      local.get 1
      call 0
      return
    end
    local.get 3
    i32.const 1
    i32.eq
    if  ;; label = @1
      i32.const 7
      i32.const -1
      i32.const -1
      local.get 1
      call 0
      return
    end
    local.get 3
    i32.eqz
    i32.eqz
    if  ;; label = @1
      i32.const 11
      i32.const -1
      i32.const -1
      local.get 1
      call 0
      return
    end
    local.get 2
    i32.load offset=4
    i32.const 0
    i32.load offset=8
    i32.gt_u
    if  ;; label = @1
      i32.const 11
      i32.const -1
      i32.const -1
      local.get 1
      call 0
      return
    end
    i32.const 0
    i32.load offset=12
    local.set 4
    i32.const -1
    local.set 5
    i32.const 0
    local.set 6
    block  ;; label = @1
      loop  ;; label = @2
        local.get 4
        local.get 0
        i32.eq
        br_if 1 (;@1;)
        local.get 4
        i32.const -1
        i32.eq
        if  ;; label = @3
          i32.const 11
          i32.const -1
          i32.const -1
          local.get 1
          call 0
          return
        end
        local.get 4
        i32.const 0
        i32.load offset=4
        i32.ge_u
        if  ;; label = @3
          i32.const 11
          i32.const -1
          i32.const -1
          local.get 1
          call 0
          return
        end
        local.get 6
        i32.const 0
        i32.load offset=4
        i32.ge_u
        if  ;; label = @3
          i32.const 11
          i32.const -1
          i32.const -1
          local.get 1
          call 0
          return
        end
        local.get 4
        i32.const 16
        i32.mul
        i32.const 32
        i32.add
        local.set 8
        local.get 8
        i32.load
        i32.eqz
        i32.eqz
        if  ;; label = @3
          i32.const 11
          i32.const -1
          i32.const -1
          local.get 1
          call 0
          return
        end
        local.get 4
        local.set 5
        local.get 8
        i32.load offset=12
        local.set 4
        local.get 6
        i32.const 1
        i32.add
        local.set 6
        br 0 (;@2;)
      end
    end
    local.get 2
    i32.load offset=12
    local.set 7
    local.get 5
    i32.const -1
    i32.eq
    if  ;; label = @1
      i32.const 0
      local.get 7
      i32.store offset=12
    else
      local.get 5
      i32.const 16
      i32.mul
      i32.const 32
      i32.add
      local.set 8
      local.get 8
      local.get 7
      i32.store offset=12
    end
    local.get 2
    i32.const 1
    i32.store
    local.get 2
    local.get 1
    i32.store offset=8
    local.get 2
    i32.const -1
    i32.store offset=12
    i32.const 0
    local.get 0
    local.get 2
    i32.load offset=4
    i32.const 0
    call 0)
  (func (;3;) (type 3) (param i32) (result i32)
    (local i32)
    global.get 0
    i32.eqz
    if  ;; label = @1
      i32.const 9
      return
    end
    i32.const 0
    i32.load offset=12
    local.set 1
    local.get 1
    i32.const -1
    i32.eq
    if  ;; label = @1
      i32.const 2
      i32.const -1
      i32.const -1
      local.get 0
      call 0
      return
    end
    local.get 1
    local.get 0
    call 2)
  (func (;4;) (type 4) (param i32 i32 i32) (result i32)
    (local i32 i32 i32 i32)
    global.get 0
    i32.eqz
    if  ;; label = @1
      i32.const 9
      return
    end
    local.get 0
    i32.const 0
    i32.load
    i32.ne
    if  ;; label = @1
      i32.const 4
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 1
    i32.const 0
    i32.load offset=4
    i32.ge_u
    if  ;; label = @1
      i32.const 3
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 1
    i32.const 16
    i32.mul
    i32.const 32
    i32.add
    local.set 3
    local.get 3
    i32.load
    local.set 4
    local.get 4
    i32.const 2
    i32.eq
    if  ;; label = @1
      i32.const 8
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 4
    i32.const 1
    i32.gt_u
    if  ;; label = @1
      i32.const 11
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 3
    i32.load offset=4
    local.set 5
    local.get 5
    local.get 2
    i32.ne
    if  ;; label = @1
      i32.const 5
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 4
    i32.eqz
    if  ;; label = @1
      i32.const 6
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 5
    i32.const 0
    i32.load offset=8
    i32.gt_u
    if  ;; label = @1
      i32.const 11
      i32.const -1
      i32.const -1
      i32.const 0
      call 0
      return
    end
    local.get 3
    i32.load offset=8
    local.set 6
    local.get 3
    i32.const 0
    i32.store offset=8
    local.get 5
    i32.const 0
    i32.load offset=8
    i32.lt_u
    if  ;; label = @1
      local.get 3
      i32.const 0
      i32.store
      local.get 3
      local.get 5
      i32.const 1
      i32.add
      i32.store offset=4
      local.get 3
      i32.const 0
      i32.load offset=12
      i32.store offset=12
      i32.const 0
      local.get 1
      i32.store offset=12
    else
      local.get 3
      i32.const 2
      i32.store
      local.get 3
      i32.const -1
      i32.store offset=12
    end
    i32.const 0
    local.get 1
    local.get 2
    local.get 6
    call 0)
  (func (;5;) (type 5) (param i32 i32 i32) (result i32)
    (local i32)
    local.get 0
    local.get 1
    local.get 2
    call 4
    local.set 3
    local.get 3
    i32.eqz
    if  ;; label = @1
      i32.const 0
      i32.const 0
      i32.load offset=28
      i32.const 1
      i32.add
      i32.store offset=28
    end
    local.get 3)
  (memory (;0;) 2 2)
  (global (;0;) (mut i32) (i32.const 0))
  (export "init" (func 1))
  (export "put" (func 2))
  (export "alloc" (func 3))
  (export "take" (func 4))
  (export "release" (func 5))
  (export "memory" (memory 0)))
