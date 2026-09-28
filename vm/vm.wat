;; knot-vm-1: runs knot-image-1 images. Written from vm/SPEC.md (cited as §n),
;; independently of vm/model.bend; the two meet in vm-lockstep.
;;
;; Conventions.
;; - Image word offsets are absolute (§2). Word i lives at byte 4096 + 4i, read
;;   with `offset=4096` on `i << 2`. Frames and cells hold word offsets, never
;;   byte addresses of image records.
;; - Nothing recurses: no function calls itself directly or indirectly, and
;;   there is no call_indirect. Every traversal keeps an explicit worklist.
;; - Every refusal or stop reports through the host (`die`, `exhausted`) and
;;   never returns; `unreachable` follows each such call.
;; - Lines starting `;;TEST ` are the test build's debug exports; the
;;   production build ignores them as comments (vm/build.py strips the prefix).
;; - vm-core has no reclamation (SPEC §5's RC heap arrives in vm-rc): cells
;;   come from a bump arena, `$dup`/`$drop` mark the spec's substeps and do
;;   nothing yet, and image constants are immortal.
(module
  (import "knot_io" "args" (func $io_args (param i32)))
  (import "knot_io" "print" (func $io_print (param i32 i32)))
  (import "knot_io" "die" (func $io_die (param i32 i32 i32)))
  (import "knot_io" "open" (func $io_open (param i32 i32 i32 i32 i32)))
  (import "knot_io" "read_bytes" (func $io_read_bytes (param i32 i32 i32)))
  (import "knot_io" "close" (func $io_close (param i32)))
  (import "knot_io" "exhausted" (func $io_exhausted (param i32)))

  (memory (export "memory") 1 65536)

  ;; ---------------------------------------------------------------- control region
  ;; [0,4096): 16 host result record; 32 single-operand buffer; 36 "r"; 40 "--";
  ;; 44 "main"; 60 constant kinds; 64 decimal scratch; 96 describe punctuation;
  ;; 128 message prefixes (32-byte slots); 384 representation shapes; 480 pinned
  ;; Base digest; 512 message buffer; 1024 reason codes (24-byte slots,
  ;; NUL-terminated); 3712 prim table; 3880 foreign table; 3920 test dump.
  (data (i32.const 36) "r")
  (data (i32.const 40) "--")
  (data (i32.const 44) "main")
  ;; representation position of each constant kind: U32, Nat, Char, String
  (data (i32.const 60) "\01\00\02\03")
  (data (i32.const 128) "HostFailure\09image\09")
  (data (i32.const 160) "HostFailure\09invoke\09")
  (data (i32.const 192) "HostFailure\09arguments\09")
  (data (i32.const 224) "Unsupported\09invoke\09")
  (data (i32.const 256) "Unsupported\09vm\09")
  (data (i32.const 288) "InternalFailure\09vm\09")
  (data (i32.const 320) "HostFailure\09io\09")
  (data (i32.const 352) "Evaluated\09")
  ;; §2 pinned representation shapes, in registry order (Nat U32 Char String
  ;; Bool Cmp Unit List Result Sigma IO.OP File): constructor count (0xfe:
  ;; opaque), then per constructor its field count and field representations
  ;; (0xff: an erased type parameter).
  (data (i32.const 384) "\02\00\01\00")
  (data (i32.const 392) "\fe")
  (data (i32.const 400) "\01\01\01")
  (data (i32.const 408) "\02\00\02\02\03")
  (data (i32.const 416) "\02\00\00")
  (data (i32.const 424) "\03\00\00\00")
  (data (i32.const 432) "\01\00")
  (data (i32.const 440) "\02\00\02\ff\07")
  (data (i32.const 448) "\02\01\ff\01\ff")
  (data (i32.const 456) "\01\02\ff\ff")
  (data (i32.const 464) "\02\01\ff\02\01\03")
  (data (i32.const 472) "\fe")
  ;; registry.json base.sha256, packed little-endian (§2 header words 24-31)
  (data (i32.const 480) "\22\ee\a8\39\11\e2\39\5f\63\59\4f\ea\7c\10\ac\0c\1e\5b\54\82\51\68\1f\c9\7c\d7\66\7e\0e\b7\03\1b")

  ;; reason codes: slot k at 1024 + 24k
  (data (i32.const 1024) "image-size")
  (data (i32.const 1048) "length")
  (data (i32.const 1072) "magic")
  (data (i32.const 1096) "total")
  (data (i32.const 1120) "header")
  (data (i32.const 1144) "registry-digest")
  (data (i32.const 1168) "section-offset")
  (data (i32.const 1192) "record-count")
  (data (i32.const 1216) "record-length")
  (data (i32.const 1240) "trailing-words")
  (data (i32.const 1264) "name-length")
  (data (i32.const 1288) "name-padding")
  (data (i32.const 1312) "name-utf8")
  (data (i32.const 1336) "duplicate-name")
  (data (i32.const 1360) "name-index")
  (data (i32.const 1384) "type-record")
  (data (i32.const 1408) "constructor-grouping")
  (data (i32.const 1432) "opaque-type")
  (data (i32.const 1456) "arrow-name")
  (data (i32.const 1480) "type-index")
  (data (i32.const 1504) "constructor-count")
  (data (i32.const 1528) "constructor-record")
  (data (i32.const 1552) "constructor-tag")
  (data (i32.const 1576) "constructor-order")
  (data (i32.const 1600) "constant-record")
  (data (i32.const 1624) "scalar-constant-width")
  (data (i32.const 1648) "string-code")
  (data (i32.const 1672) "node-record")
  (data (i32.const 1696) "node-length")
  (data (i32.const 1720) "function-record")
  (data (i32.const 1744) "function-root")
  (data (i32.const 1768) "child-offset")
  (data (i32.const 1792) "child-after-parent")
  (data (i32.const 1816) "shared-node")
  (data (i32.const 1840) "standalone-arm")
  (data (i32.const 1864) "constant-index")
  (data (i32.const 1888) "case-key")
  (data (i32.const 1912) "case-arm-kind")
  (data (i32.const 1936) "unreachable-node")
  (data (i32.const 1960) "main-index")
  (data (i32.const 1984) "representation-opaque")
  (data (i32.const 2008) "representation-shape")
  (data (i32.const 2032) "duplicate-function")
  (data (i32.const 2056) "arrow-cycle")
  (data (i32.const 2080) "program-main")
  (data (i32.const 2104) "program-representation")
  (data (i32.const 2128) "program-io")
  (data (i32.const 2152) "limits")
  (data (i32.const 2176) "literal-kind")
  (data (i32.const 2200) "value-nullary")
  (data (i32.const 2224) "slot-depth")
  (data (i32.const 2248) "reference-type")
  (data (i32.const 2272) "construct-tag")
  (data (i32.const 2296) "construct-arity")
  (data (i32.const 2320) "construct-field-type")
  (data (i32.const 2344) "function-index")
  (data (i32.const 2368) "call-arity")
  (data (i32.const 2392) "call-types")
  (data (i32.const 2416) "unknown-prim")
  (data (i32.const 2440) "unknown-foreign")
  (data (i32.const 2464) "prim-arity")
  (data (i32.const 2488) "foreign-arity")
  (data (i32.const 2512) "prim-operand")
  (data (i32.const 2536) "foreign-operand")
  (data (i32.const 2560) "prim-result")
  (data (i32.const 2584) "foreign-result")
  (data (i32.const 2608) "let-slot")
  (data (i32.const 2632) "let-body-type")
  (data (i32.const 2656) "case-slot")
  (data (i32.const 2680) "case-scrutinee-type")
  (data (i32.const 2704) "tag-case-type")
  (data (i32.const 2728) "tag-table")
  (data (i32.const 2752) "default-coverage")
  (data (i32.const 2776) "branch-key")
  (data (i32.const 2800) "branch-binders")
  (data (i32.const 2824) "branch-body-type")
  (data (i32.const 2848) "key-case-type")
  (data (i32.const 2872) "key-order")
  (data (i32.const 2896) "key-branch-binders")
  (data (i32.const 2920) "key-branch-body-type")
  (data (i32.const 2944) "default-body-type")
  (data (i32.const 2968) "closure-arrow")
  (data (i32.const 2992) "capture-order")
  (data (i32.const 3016) "capture-use")
  (data (i32.const 3040) "closure-slots")
  (data (i32.const 3064) "closure-result-type")
  (data (i32.const 3088) "invoke-arity")
  (data (i32.const 3112) "invoke-types")
  (data (i32.const 3136) "function-slots")
  (data (i32.const 3160) "body-type")
  (data (i32.const 3184) "noncanonical")
  (data (i32.const 3208) "ill-typed")
  (data (i32.const 3232) "unreadable")
  (data (i32.const 3256) "usage")
  (data (i32.const 3280) "expected-u32")
  (data (i32.const 3304) "unknown-export")
  (data (i32.const 3328) "argument-arity")
  (data (i32.const 3352) "argument-range")
  (data (i32.const 3376) "structured-argument")
  (data (i32.const 3400) "result-type")
  (data (i32.const 3424) "foreign")
  (data (i32.const 3448) "fuel")
  (data (i32.const 3472) "heap")
  (data (i32.const 3496) "frames")
  (data (i32.const 3520) "NatRange")
  (data (i32.const 3544) "RCOverflow")
  (data (i32.const 3568) "display")
  (data (i32.const 3592) "non-scalar")
  (data (i32.const 3616) "internal")

  ;; §9 prim registry (ids 0..40): arity, input representations, output
  ;; representation; arity 0xff marks a reserved id. Representation ids follow
  ;; the §2 order: 0 Nat 1 U32 2 Char 3 String 4 Bool 5 Cmp 6 Unit 7 List
  ;; 8 Result 9 Sigma 10 IO.OP 11 File.
  (data (i32.const 3712)
    "\02\01\01\01" "\02\01\01\01" "\02\01\01\01" "\02\01\01\01" "\02\01\01\01"   ;; add sub mul div mod
    "\01\01\00\01" "\02\01\01\01" "\02\01\01\05"                               ;; not and cmp
    "\02\01\01\04" "\02\01\01\04" "\02\01\01\04" "\02\01\01\04" "\02\01\01\04" "\02\01\01\04" ;; eq ne lt le gt ge
    "\02\01\00\01" "\02\01\00\01"                                              ;; shln shrn
    "\01\01\00\00" "\01\00\00\01" "\01\01\00\02" "\01\02\00\01"                ;; to_nat from_nat from_u32 to_u32
    "\02\02\02\04" "\01\02\00\04"                                              ;; Char.is_eq is_space
    "\02\00\00\00" "\02\00\00\00" "\02\00\00\00" "\02\00\00\05"                ;; Nat add sub mul cmp
    "\02\00\00\04" "\02\00\00\04" "\02\00\00\04" "\02\00\00\04" "\02\00\00\04" "\02\00\00\04" ;; Nat eq ne lt le gt ge
    "\01\01\00\03" "\01\00\00\03"                                              ;; U32.show Nat.show
    "\02\03\03\04" "\02\03\03\03" "\01\03\00\03" "\01\03\00\00" "\01\03\00\04" ;; eq append reverse length is_empty
    "\ff\01\01\01" "\ff\01\01\01")                                             ;; reserved U32.or U32.xor
  ;; §10 foreign rows 0..7: arity, inputs, output of IO(X)
  (data (i32.const 3880)
    "\00\00\00\07" "\01\03\00\06" "\02\03\03\08" "\02\0b\01\09"
    "\02\0b\07\09" "\01\0b\00\06" "\02\0b\01\09" "\01\03\00\08")

  ;; ---------------------------------------------------------------- reason codes
  (global $R_image_size i32 (i32.const 1024))
  (global $R_length i32 (i32.const 1048))
  (global $R_magic i32 (i32.const 1072))
  (global $R_total i32 (i32.const 1096))
  (global $R_header i32 (i32.const 1120))
  (global $R_registry_digest i32 (i32.const 1144))
  (global $R_section_offset i32 (i32.const 1168))
  (global $R_record_count i32 (i32.const 1192))
  (global $R_record_length i32 (i32.const 1216))
  (global $R_trailing_words i32 (i32.const 1240))
  (global $R_name_length i32 (i32.const 1264))
  (global $R_name_padding i32 (i32.const 1288))
  (global $R_name_utf8 i32 (i32.const 1312))
  (global $R_duplicate_name i32 (i32.const 1336))
  (global $R_name_index i32 (i32.const 1360))
  (global $R_type_record i32 (i32.const 1384))
  (global $R_constructor_grouping i32 (i32.const 1408))
  (global $R_opaque_type i32 (i32.const 1432))
  (global $R_arrow_name i32 (i32.const 1456))
  (global $R_type_index i32 (i32.const 1480))
  (global $R_constructor_count i32 (i32.const 1504))
  (global $R_constructor_record i32 (i32.const 1528))
  (global $R_constructor_tag i32 (i32.const 1552))
  (global $R_constructor_order i32 (i32.const 1576))
  (global $R_constant_record i32 (i32.const 1600))
  (global $R_scalar_constant_width i32 (i32.const 1624))
  (global $R_string_code i32 (i32.const 1648))
  (global $R_node_record i32 (i32.const 1672))
  (global $R_node_length i32 (i32.const 1696))
  (global $R_function_record i32 (i32.const 1720))
  (global $R_function_root i32 (i32.const 1744))
  (global $R_child_offset i32 (i32.const 1768))
  (global $R_child_after_parent i32 (i32.const 1792))
  (global $R_shared_node i32 (i32.const 1816))
  (global $R_standalone_arm i32 (i32.const 1840))
  (global $R_constant_index i32 (i32.const 1864))
  (global $R_case_key i32 (i32.const 1888))
  (global $R_case_arm_kind i32 (i32.const 1912))
  (global $R_unreachable_node i32 (i32.const 1936))
  (global $R_main_index i32 (i32.const 1960))
  (global $R_representation_opaque i32 (i32.const 1984))
  (global $R_representation_shape i32 (i32.const 2008))
  (global $R_duplicate_function i32 (i32.const 2032))
  (global $R_arrow_cycle i32 (i32.const 2056))
  (global $R_program_main i32 (i32.const 2080))
  (global $R_program_representation i32 (i32.const 2104))
  (global $R_program_io i32 (i32.const 2128))
  (global $R_limits i32 (i32.const 2152))
  (global $R_literal_kind i32 (i32.const 2176))
  (global $R_value_nullary i32 (i32.const 2200))
  (global $R_slot_depth i32 (i32.const 2224))
  (global $R_reference_type i32 (i32.const 2248))
  (global $R_construct_tag i32 (i32.const 2272))
  (global $R_construct_arity i32 (i32.const 2296))
  (global $R_construct_field_type i32 (i32.const 2320))
  (global $R_function_index i32 (i32.const 2344))
  (global $R_call_arity i32 (i32.const 2368))
  (global $R_call_types i32 (i32.const 2392))
  (global $R_unknown_prim i32 (i32.const 2416))
  (global $R_unknown_foreign i32 (i32.const 2440))
  (global $R_prim_arity i32 (i32.const 2464))
  (global $R_foreign_arity i32 (i32.const 2488))
  (global $R_prim_operand i32 (i32.const 2512))
  (global $R_foreign_operand i32 (i32.const 2536))
  (global $R_prim_result i32 (i32.const 2560))
  (global $R_foreign_result i32 (i32.const 2584))
  (global $R_let_slot i32 (i32.const 2608))
  (global $R_let_body_type i32 (i32.const 2632))
  (global $R_case_slot i32 (i32.const 2656))
  (global $R_case_scrutinee_type i32 (i32.const 2680))
  (global $R_tag_case_type i32 (i32.const 2704))
  (global $R_tag_table i32 (i32.const 2728))
  (global $R_default_coverage i32 (i32.const 2752))
  (global $R_branch_key i32 (i32.const 2776))
  (global $R_branch_binders i32 (i32.const 2800))
  (global $R_branch_body_type i32 (i32.const 2824))
  (global $R_key_case_type i32 (i32.const 2848))
  (global $R_key_order i32 (i32.const 2872))
  (global $R_key_branch_binders i32 (i32.const 2896))
  (global $R_key_branch_body_type i32 (i32.const 2920))
  (global $R_default_body_type i32 (i32.const 2944))
  (global $R_closure_arrow i32 (i32.const 2968))
  (global $R_capture_order i32 (i32.const 2992))
  (global $R_capture_use i32 (i32.const 3016))
  (global $R_closure_slots i32 (i32.const 3040))
  (global $R_closure_result_type i32 (i32.const 3064))
  (global $R_invoke_arity i32 (i32.const 3088))
  (global $R_invoke_types i32 (i32.const 3112))
  (global $R_function_slots i32 (i32.const 3136))
  (global $R_body_type i32 (i32.const 3160))
  (global $R_noncanonical i32 (i32.const 3184))
  (global $R_ill_typed i32 (i32.const 3208))
  (global $R_unreadable i32 (i32.const 3232))
  (global $R_usage i32 (i32.const 3256))
  (global $R_expected_u32 i32 (i32.const 3280))
  (global $R_unknown_export i32 (i32.const 3304))
  (global $R_argument_arity i32 (i32.const 3328))
  (global $R_argument_range i32 (i32.const 3352))
  (global $R_structured_argument i32 (i32.const 3376))
  (global $R_result_type i32 (i32.const 3400))
  (global $R_foreign i32 (i32.const 3424))
  (global $R_fuel i32 (i32.const 3448))
  (global $R_heap i32 (i32.const 3472))
  (global $R_frames i32 (i32.const 3496))
  (global $R_nat_range i32 (i32.const 3520))
  (global $R_rc_overflow i32 (i32.const 3544))
  (global $R_display i32 (i32.const 3568))
  (global $R_non_scalar i32 (i32.const 3592))
  (global $R_internal i32 (i32.const 3616))

  ;; ---------------------------------------------------------------- registers
  ;; image geometry: total words, section offsets and record counts (§2)
  (global $W (mut i32) (i32.const 0))
  (global $sT (mut i32) (i32.const 0))
  (global $sC (mut i32) (i32.const 0))
  (global $sF (mut i32) (i32.const 0))
  (global $sK (mut i32) (i32.const 0))
  (global $sN (mut i32) (i32.const 0))
  (global $sM (mut i32) (i32.const 0))
  (global $nT (mut i32) (i32.const 0))
  (global $nC (mut i32) (i32.const 0))
  (global $nF (mut i32) (i32.const 0))
  (global $nK (mut i32) (i32.const 0))
  (global $nN (mut i32) (i32.const 0))
  (global $nM (mut i32) (i32.const 0))
  ;; pinned representation type indices, header words 12-23 (0xffffffff: absent)
  (global $rNat (mut i32) (i32.const -1))
  (global $rU32 (mut i32) (i32.const -1))
  (global $rChar (mut i32) (i32.const -1))
  (global $rString (mut i32) (i32.const -1))
  (global $rIoop (mut i32) (i32.const -1))

  ;; machine state (§6): control is `$mode` with its register; Enter keeps its
  ;; target (a function record offset when `$tfn`, else a word) and `$nops`
  ;; operand words at byte address `$ops`.
  (global $mode (mut i32) (i32.const 3))     ;; 0 Eval 1 Return 2 Enter 3 Halt
  (global $node (mut i32) (i32.const 0))
  (global $val (mut i32) (i32.const 0))
  (global $tgt (mut i32) (i32.const 0))
  (global $tfn (mut i32) (i32.const 0))
  (global $ops (mut i32) (i32.const 0))
  (global $nops (mut i32) (i32.const 0))
  (global $act (mut i32) (i32.const 0))
  (global $top (mut i32) (i32.const 0))
  (global $fuel (mut i32) (i32.const 0))
  (global $calls (mut i32) (i32.const 0))
  (global $quantum (mut i32) (i32.const 0))
  (global $terminal (mut i32) (i32.const 0))
  ;; memory map (§5): frame region [F0, FL), heap [H0, HL) with bump
  (global $F0 (mut i32) (i32.const 0))
  (global $FL (mut i32) (i32.const 0))
  (global $H0 (mut i32) (i32.const 0))
  (global $bump (mut i32) (i32.const 0))
  (global $HL (mut i64) (i64.const 0x100000000))
  (global $frameBytes (mut i32) (i32.const 0x1000000))
  ;; knot_alloc's cursor for host transfers
  (global $hbump (mut i32) (i32.const 0))
  ;; outcome: 1 Completed, 2 Halted, 3 HostFailure, 4 Unsupported, 5 Exhausted,
  ;; 6 InternalFailure; kind is the host exit or exhaustion kind; cause a reason
  (global $oc (mut i32) (i32.const 0))
  (global $okind (mut i32) (i32.const 0))
  (global $ocause (mut i32) (i32.const 0))
  ;; test builds stop after every transition when set
  (global $single (mut i32) (i32.const 0))
  (global $yields (mut i32) (i32.const 0))
  ;; boot: arguments, scratch cursor, parsed entry
  (global $argc (mut i32) (i32.const 0))
  (global $argv (mut i32) (i32.const 0))
  (global $scratch (mut i32) (i32.const 0))

  ;; ---------------------------------------------------------------- memory and reporting
  ;; Grow linear memory to cover [0, end). The callers bound `end` by 4 GiB; a
  ;; host that refuses growth below the maximum traps, which the host reports
  ;; as HostFailure (§5).
  (func $grow (param $end i64)
    (local $have i64)
    (local.set $have (i64.shl (i64.extend_i32_u (memory.size)) (i64.const 16)))
    (if (i64.gt_u (local.get $end) (local.get $have))
      (then
        (if (i32.lt_s
              (memory.grow (i32.wrap_i64 (i64.shr_u
                (i64.add (i64.sub (local.get $end) (local.get $have)) (i64.const 65535))
                (i64.const 16))))
              (i32.const 0))
          (then unreachable)))))

  ;; The host's allocator entry: disjoint ranges at `$hbump`, which boot aims
  ;; at the argument area and then at the image's next chunk.
  (func (export "knot_alloc") (param $n i32) (result i32)
    (local $p i32) (local $end i64)
    (local.set $p (global.get $hbump))
    (local.set $end (i64.add (i64.extend_i32_u (local.get $p)) (i64.extend_i32_u (local.get $n))))
    (if (i64.gt_u (local.get $end) (i64.const 0x100000000))
      (then (call $io_exhausted (i32.const 2)) unreachable))
    (call $grow (local.get $end))
    (global.set $hbump (i32.wrap_i64 (local.get $end)))
    (local.get $p))

  ;; NUL-terminated length of a control-region string
  (func $strlen (param $p i32) (result i32)
    (local $n i32)
    (block $done
      (loop $next
        (br_if $done (i32.eqz (i32.load8_u (i32.add (local.get $p) (local.get $n)))))
        (local.set $n (i32.add (local.get $n) (i32.const 1)))
        (br $next)))
    (local.get $n))

  ;; Report `prefix code` through die(status). Never returns.
  (func $stop (param $class i32) (param $status i32) (param $prefix i32) (param $code i32)
    (local $a i32) (local $b i32)
    (global.set $oc (local.get $class))
    (global.set $okind (local.get $status))
    (global.set $ocause (local.get $code))
    (global.set $mode (i32.const 3))
    (local.set $a (call $strlen (local.get $prefix)))
    (local.set $b (call $strlen (local.get $code)))
    (memory.copy (i32.const 512) (local.get $prefix) (local.get $a))
    (memory.copy (i32.add (i32.const 512) (local.get $a)) (local.get $code) (local.get $b))
    (call $io_die (local.get $status) (i32.const 512) (i32.add (local.get $a) (local.get $b)))
    unreachable)

  ;; A malformed image or an ill-typed word (§4, §6): HostFailure image.
  (func $refuse (param $code i32)
    (call $stop (i32.const 3) (i32.const 5) (i32.const 128) (local.get $code)))

  ;; A broken VM invariant: InternalFailure, never exhaustion (§5).
  (func $internal
    (call $stop (i32.const 6) (i32.const 6) (i32.const 288) (global.get $R_internal)))

  ;; §11: the precise cause stays in the outcome; the host sees only the kind.
  (func $exhaust (param $kind i32) (param $cause i32)
    (global.set $oc (i32.const 5))
    (global.set $okind (local.get $kind))
    (global.set $ocause (local.get $cause))
    (global.set $mode (i32.const 3))
    (call $io_exhausted (local.get $kind))
    unreachable)

  ;; image word i
  (func $w (param $i i32) (result i32)
    (i32.load offset=4096 (i32.shl (local.get $i) (i32.const 2))))

  ;; type record field: 0 kind, 1 name, 2 a (first constructor or domain),
  ;; 3 b (constructor count or result). Type records are exactly 5 words.
  (func $ty (param $t i32) (param $f i32) (result i32)
    (call $w (i32.add (i32.add (global.get $sT) (i32.const 2))
                      (i32.add (i32.mul (local.get $t) (i32.const 5)) (local.get $f)))))

  ;; kind of a type or 0xff for `none`
  (func $kind (param $t i32) (result i32)
    (if (result i32) (i32.eq (local.get $t) (i32.const -1))
      (then (i32.const 0xff))
      (else (call $ty (local.get $t) (i32.const 0)))))

  ;; representation index for registry position r (0..11)
  (func $rep (param $r i32) (result i32)
    (call $w (i32.add (i32.const 12) (local.get $r))))

  ;; round up to a multiple of 8
  (func $align8 (param $p i32) (result i32)
    (i32.and (i32.add (local.get $p) (i32.const 7)) (i32.const -8)))

  ;; take `bytes` of boot scratch, zeroed
  (func $take (param $bytes i32) (result i32)
    (local $p i32) (local $end i64)
    (local.set $p (call $align8 (global.get $scratch)))
    (local.set $end (i64.add (i64.extend_i32_u (local.get $p)) (i64.extend_i32_u (local.get $bytes))))
    (if (i64.gt_u (local.get $end) (i64.const 0xfffff000))
      (then (call $exhaust (i32.const 2) (global.get $R_heap))))
    (call $grow (local.get $end))
    (memory.fill (local.get $p) (i32.const 0) (local.get $bytes))
    (global.set $scratch (i32.wrap_i64 (local.get $end)))
    (local.get $p))

  ;; ---------------------------------------------------------------- boot tables
  ;; Record offsets by index, in the frame region (free until the machine
  ;; starts): names, constructors by (first constructor + tag), functions and
  ;; constants. Linking turns constructor-name, function and constant entries
  ;; into what the machine reads.
  (global $tM (mut i32) (i32.const 0))
  (global $tC (mut i32) (i32.const 0))
  (global $tF (mut i32) (i32.const 0))
  (global $tK (mut i32) (i32.const 0))
  ;; boot scratch: node marks (1 record start, 2 child, 4 root), representation
  ;; of each type, scope types and uses, the task stack, the fits stack and its
  ;; pair memo
  (global $mk (mut i32) (i32.const 0))
  (global $ro (mut i32) (i32.const 0))
  (global $sc (mut i32) (i32.const 0))
  (global $us (mut i32) (i32.const 0))
  (global $tk (mut i32) (i32.const 0))
  (global $tkEnd (mut i32) (i32.const 0))
  (global $tp (mut i32) (i32.const 0))
  (global $fs (mut i32) (i32.const 0))
  (global $psT (mut i32) (i32.const 0))
  (global $psCap (mut i32) (i32.const 0))
  (global $psN (mut i32) (i32.const 0))
  ;; tree walk counters (§4 step 3) and the canonical flag (§4 step 5)
  (global $owned (mut i32) (i32.const 0))
  (global $roots (mut i32) (i32.const 0))
  (global $expect (mut i32) (i32.const 0))
  (global $nextConst (mut i32) (i32.const 0))
  (global $nextSite (mut i32) (i32.const 0))
  (global $noncanon (mut i32) (i32.const 0))
  ;; validator unit: scope base and deepest depth reached
  (global $vbase (mut i32) (i32.const 0))
  (global $vdeep (mut i32) (i32.const 0))

  (func $tab (param $t i32) (param $i i32) (result i32)
    (i32.load (i32.add (local.get $t) (i32.shl (local.get $i) (i32.const 2)))))
  (func $tabset (param $t i32) (param $i i32) (param $v i32)
    (i32.store (i32.add (local.get $t) (i32.shl (local.get $i) (i32.const 2))) (local.get $v)))

  ;; the constructor record of (t, tag) before linking
  (func $ctorv (param $t i32) (param $tag i32) (result i32)
    (call $tab (global.get $tC) (i32.add (call $ty (local.get $t) (i32.const 2)) (local.get $tag))))

  ;; a type reference: `none` or an index below the type count
  (func $typeref (param $t i32)
    (if (i32.and (i32.ne (local.get $t) (i32.const -1)) (i32.ge_u (local.get $t) (global.get $nT)))
      (then (call $refuse (global.get $R_type_index)))))

  ;; strict UTF-8 over [p, p+n): scalars only, shortest forms
  (func $utf8 (param $p i32) (param $n i32) (result i32)
    (local $i i32) (local $b i32) (local $need i32) (local $lo i32) (local $hi i32)
    (block $bad
      (loop $next
        (if (i32.ge_u (local.get $i) (local.get $n)) (then (return (i32.const 1))))
        (local.set $b (i32.load8_u (i32.add (local.get $p) (local.get $i))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $next (i32.lt_u (local.get $b) (i32.const 0x80)))
        (br_if $bad (i32.lt_u (local.get $b) (i32.const 0xc2)))
        (br_if $bad (i32.gt_u (local.get $b) (i32.const 0xf4)))
        (local.set $lo (i32.const 0x80))
        (local.set $hi (i32.const 0xbf))
        (if (i32.lt_u (local.get $b) (i32.const 0xe0))
          (then (local.set $need (i32.const 1)))
          (else (if (i32.lt_u (local.get $b) (i32.const 0xf0))
            (then
              (local.set $need (i32.const 2))
              (if (i32.eq (local.get $b) (i32.const 0xe0)) (then (local.set $lo (i32.const 0xa0))))
              (if (i32.eq (local.get $b) (i32.const 0xed)) (then (local.set $hi (i32.const 0x9f)))))
            (else
              (local.set $need (i32.const 3))
              (if (i32.eq (local.get $b) (i32.const 0xf0)) (then (local.set $lo (i32.const 0x90))))
              (if (i32.eq (local.get $b) (i32.const 0xf4)) (then (local.set $hi (i32.const 0x8f))))))))
        (br_if $bad (i32.gt_u (local.get $need) (i32.sub (local.get $n) (local.get $i))))
        (local.set $b (i32.load8_u (i32.add (local.get $p) (local.get $i))))
        (br_if $bad (i32.or (i32.lt_u (local.get $b) (local.get $lo)) (i32.gt_u (local.get $b) (local.get $hi))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (local.set $need (i32.sub (local.get $need) (i32.const 1)))
        (block $tail
          (loop $cont
            (br_if $tail (i32.eqz (local.get $need)))
            (local.set $b (i32.load8_u (i32.add (local.get $p) (local.get $i))))
            (br_if $bad (i32.ne (i32.and (local.get $b) (i32.const 0xc0)) (i32.const 0x80)))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (local.set $need (i32.sub (local.get $need) (i32.const 1)))
            (br $cont)))
        (br $next)))
    (i32.const 0))

  ;; Two records with equal words (length word included) among `count`
  ;; records whose offsets are in table `t`: names and constants are interned,
  ;; so equal records are a duplicate. Open addressing on an FNV-1a hash.
  (func $duplicate (param $t i32) (param $count i32) (result i32)
    (local $cap i32) (local $h i32) (local $i i32) (local $at i32) (local $n i32)
    (local $j i32) (local $e i32) (local $o i32) (local $k i32) (local $same i32)
    (local.set $cap (i32.const 4))
    (loop $size
      (if (i32.lt_u (local.get $cap) (i32.shl (local.get $count) (i32.const 1)))
        (then (local.set $cap (i32.shl (local.get $cap) (i32.const 1))) (br $size))))
    (local.set $h (call $take (i32.shl (local.get $cap) (i32.const 2))))
    (block $done
      (loop $each
        (br_if $done (i32.ge_u (local.get $i) (local.get $count)))
        (local.set $at (call $tab (local.get $t) (local.get $i)))
        (local.set $n (call $w (local.get $at)))
        (local.set $e (i32.const 0x811c9dc5))
        (local.set $j (i32.const 0))
        (block $hashed
          (loop $mix
            (br_if $hashed (i32.ge_u (local.get $j) (local.get $n)))
            (local.set $e (i32.mul (i32.xor (local.get $e) (call $w (i32.add (local.get $at) (local.get $j))))
                                   (i32.const 0x01000193)))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $mix)))
        (local.set $e (i32.and (local.get $e) (i32.sub (local.get $cap) (i32.const 1))))
        (block $placed
          (loop $probe
            (local.set $k (call $tab (local.get $h) (local.get $e)))
            (if (i32.eqz (local.get $k))
              (then (call $tabset (local.get $h) (local.get $e) (i32.add (local.get $i) (i32.const 1)))
                    (br $placed)))
            (local.set $o (call $tab (local.get $t) (i32.sub (local.get $k) (i32.const 1))))
            (if (i32.eq (call $w (local.get $o)) (local.get $n))
              (then
                (local.set $same (i32.const 1))
                (local.set $j (i32.const 0))
                (block $cmp
                  (loop $word
                    (br_if $cmp (i32.ge_u (local.get $j) (local.get $n)))
                    (if (i32.ne (call $w (i32.add (local.get $o) (local.get $j)))
                                (call $w (i32.add (local.get $at) (local.get $j))))
                      (then (local.set $same (i32.const 0)) (br $cmp)))
                    (local.set $j (i32.add (local.get $j) (i32.const 1)))
                    (br $word)))
                (if (local.get $same) (then (return (i32.const 1))))))
            (local.set $e (i32.and (i32.add (local.get $e) (i32.const 1)) (i32.sub (local.get $cap) (i32.const 1))))
            (br $probe)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (i32.const 0))

  ;; ---------------------------------------------------------------- loading (§4 step 1)
  ;; argv lands at 0x2010000, above every frame region; the image arrives in
  ;; 1 MiB read_bytes chunks directly at byte 4096.
  (func $read_image
    (local $h i32) (local $total i32) (local $n i32) (local $argend i32)
    (global.set $hbump (i32.const 0x2010000))
    (call $io_args (i32.const 16))
    (global.set $argc (i32.load (i32.const 20)))
    (global.set $argv (i32.load (i32.const 24)))
    (local.set $argend (global.get $hbump))
    (if (i32.eqz (global.get $argc))
      (then (call $stop (i32.const 3) (i32.const 5) (i32.const 192) (global.get $R_usage))))
    (call $io_open (i32.load (global.get $argv)) (i32.load offset=4 (global.get $argv))
                   (i32.const 36) (i32.const 1) (i32.const 16))
    (if (i32.load (i32.const 16)) (then (call $refuse (global.get $R_unreadable))))
    (local.set $h (i32.load (i32.const 20)))
    (block $eof
      (loop $chunk
        (global.set $hbump (i32.add (i32.const 4096) (local.get $total)))
        (call $io_read_bytes (local.get $h) (i32.const 0x100000) (i32.const 16))
        (if (i32.load (i32.const 16)) (then (call $refuse (global.get $R_unreadable))))
        (local.set $n (i32.load (i32.const 28)))
        (br_if $eof (i32.eqz (local.get $n)))
        (if (i32.ne (i32.load (i32.const 24)) (i32.add (i32.const 4096) (local.get $total)))
          (then (call $internal)))
        (local.set $total (i32.add (local.get $total) (local.get $n)))
        ;; §4 step 1: size first, even for an otherwise malformed image
        (if (i32.gt_u (local.get $total) (i32.const 0x1000000))
          (then (call $io_close (local.get $h))
                (call $exhaust (i32.const 2) (global.get $R_image_size))))
        (br $chunk)))
    (call $io_close (local.get $h))
    (if (i32.or (i32.and (local.get $total) (i32.const 3)) (i32.lt_u (local.get $total) (i32.const 128)))
      (then (call $refuse (global.get $R_length))))
    (global.set $W (i32.shr_u (local.get $total) (i32.const 2)))
    ;; §5 memory map
    (global.set $F0 (i32.and (i32.add (i32.add (i32.const 4096) (local.get $total)) (i32.const 0xffff))
                             (i32.const 0xffff0000)))
    (global.set $FL (i32.add (global.get $F0) (global.get $frameBytes)))
    (global.set $H0 (i32.add (global.get $F0) (i32.const 0x1000000)))
    (global.set $bump (global.get $H0))
    (global.set $HL (select (i64.const 0x100000000)
                            (i64.add (i64.extend_i32_u (global.get $H0)) (global.get $heapBytes))
                            (i64.gt_u (i64.add (i64.extend_i32_u (global.get $H0)) (global.get $heapBytes))
                                      (i64.const 0x100000000))))
    (global.set $scratch (select (global.get $H0) (local.get $argend)
                                 (i32.gt_u (global.get $H0) (local.get $argend))))
    (call $grow (i64.extend_i32_u (global.get $H0))))
  (global $heapBytes (mut i64) (i64.const 0x100000000))

  ;; ---------------------------------------------------------------- decoding (§4 steps 1-3)
  ;; The order of checks follows serializer.decode, so a refusal names the
  ;; same first defect as the reference codec.
  (func $decode
    (local $s i32) (local $cursor i32) (local $count i32) (local $at i32) (local $i i32)
    (local $len i32) (local $size i32) (local $nw i32) (local $p i32) (local $j i32)
    (local $kind i32) (local $expect i64) (local $t i32) (local $tag i32) (local $slot i32)
    (local $op i32) (local $lx i32) (local $root i32)
    (if (i32.or (i32.ne (call $w (i32.const 0)) (i32.const 0x474d494b)) (i32.ne (call $w (i32.const 1)) (i32.const 1)))
      (then (call $refuse (global.get $R_magic))))
    (if (i32.ne (call $w (i32.const 2)) (global.get $W)) (then (call $refuse (global.get $R_total))))
    (if (i32.or (i32.ge_u (call $w (i32.const 3)) (i32.const 2)) (call $w (i32.const 11)))
      (then (call $refuse (global.get $R_header))))
    (local.set $i (i32.const 0))
    (loop $digest
      (if (i32.ne (call $w (i32.add (i32.const 24) (local.get $i)))
                  (i32.load (i32.add (i32.const 480) (i32.shl (local.get $i) (i32.const 2)))))
        (then (call $refuse (global.get $R_registry_digest))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br_if $digest (i32.lt_u (local.get $i) (i32.const 8))))

    ;; six adjacent sections of length-prefixed records
    (local.set $cursor (i32.const 32))
    (local.set $s (i32.const 0))
    (loop $section
      (if (i32.ne (call $w (i32.add (i32.const 5) (local.get $s))) (local.get $cursor))
        (then (call $refuse (global.get $R_section_offset))))
      (if (i32.ge_u (local.get $cursor) (global.get $W)) (then (call $refuse (global.get $R_record_length))))
      (local.set $count (call $w (local.get $cursor)))
      (if (i32.gt_u (local.get $count) (i32.const 0x100000)) (then (call $refuse (global.get $R_record_count))))
      (local.set $at (i32.add (local.get $cursor) (i32.const 1)))
      (local.set $i (i32.const 0))
      (block $end
        (loop $record
          (br_if $end (i32.ge_u (local.get $i) (local.get $count)))
          (if (i32.ge_u (local.get $at) (global.get $W)) (then (call $refuse (global.get $R_record_length))))
          (local.set $len (call $w (local.get $at)))
          (if (i32.or (i32.lt_u (local.get $len) (i32.const 2))
                      (i32.gt_u (local.get $len) (i32.sub (global.get $W) (local.get $at))))
            (then (call $refuse (global.get $R_record_length))))
          (local.set $at (i32.add (local.get $at) (local.get $len)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $record)))
      (block $which
        (block $m (block $n (block $k (block $f (block $c (block $t
          (br_table $t $c $f $k $n $m (local.get $s)))
          (global.set $sT (local.get $cursor)) (global.set $nT (local.get $count)) (br $which))
          (global.set $sC (local.get $cursor)) (global.set $nC (local.get $count)) (br $which))
          (global.set $sF (local.get $cursor)) (global.set $nF (local.get $count)) (br $which))
          (global.set $sK (local.get $cursor)) (global.set $nK (local.get $count)) (br $which))
          (global.set $sN (local.get $cursor)) (global.set $nN (local.get $count)) (br $which))
        (global.set $sM (local.get $cursor)) (global.set $nM (local.get $count)))
      (local.set $cursor (local.get $at))
      (local.set $s (i32.add (local.get $s) (i32.const 1)))
      (br_if $section (i32.lt_u (local.get $s) (i32.const 6))))
    (if (i32.ne (local.get $cursor) (global.get $W)) (then (call $refuse (global.get $R_trailing_words))))

    ;; boot tables and scratch, sized by the counts
    (global.set $tM (i32.add (global.get $F0) (i32.const 0x10000)))
    (global.set $tC (i32.add (global.get $tM) (i32.shl (global.get $nM) (i32.const 2))))
    (global.set $tF (i32.add (global.get $tC) (i32.shl (global.get $nC) (i32.const 2))))
    (global.set $tK (i32.add (global.get $tF) (i32.shl (global.get $nF) (i32.const 2))))
    (call $grow (i64.extend_i32_u (i32.add (global.get $tK) (i32.shl (global.get $nK) (i32.const 2)))))
    (memory.fill (global.get $tM) (i32.const 0)
      (i32.sub (i32.add (global.get $tK) (i32.shl (global.get $nK) (i32.const 2))) (global.get $tM)))
    (global.set $mk (call $take (global.get $W)))

    ;; names: length, padding, strict UTF-8, then uniqueness
    (local.set $at (i32.add (global.get $sM) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $name
        (br_if $end (i32.ge_u (local.get $i) (global.get $nM)))
        (call $tabset (global.get $tM) (local.get $i) (local.get $at))
        (local.set $size (call $w (i32.add (local.get $at) (i32.const 1))))
        (local.set $nw (i32.sub (call $w (local.get $at)) (i32.const 2)))
        (if (i32.or (i32.eqz (local.get $size))
                    (i32.ne (local.get $nw) (i32.add (i32.shr_u (local.get $size) (i32.const 2))
                                                     (i32.ne (i32.and (local.get $size) (i32.const 3)) (i32.const 0)))))
          (then (call $refuse (global.get $R_name_length))))
        (local.set $p (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $at) (i32.const 2)) (i32.const 2))))
        (local.set $j (i32.const 0))
        (loop $byte
          (if (i32.lt_u (local.get $j) (local.get $size))
            (then (if (i32.eqz (i32.load8_u (i32.add (local.get $p) (local.get $j))))
                    (then (call $refuse (global.get $R_name_padding)))))
            (else (if (i32.load8_u (i32.add (local.get $p) (local.get $j)))
                    (then (call $refuse (global.get $R_name_padding))))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br_if $byte (i32.lt_u (local.get $j) (i32.shl (local.get $nw) (i32.const 2)))))
        (if (i32.eqz (call $utf8 (local.get $p) (local.get $size))) (then (call $refuse (global.get $R_name_utf8))))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $name)))
    (if (call $duplicate (global.get $tM) (global.get $nM)) (then (call $refuse (global.get $R_duplicate_name))))

    ;; types: fixed 5-word records; data types claim consecutive constructors
    (local.set $at (i32.add (global.get $sT) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $type
        (br_if $end (i32.ge_u (local.get $i) (global.get $nT)))
        (local.set $kind (call $w (i32.add (local.get $at) (i32.const 1))))
        (if (i32.or (i32.ne (call $w (local.get $at)) (i32.const 5)) (i32.ge_u (local.get $kind) (i32.const 4)))
          (then (call $refuse (global.get $R_type_record))))
        (if (i32.eqz (local.get $kind))
          (then
            (if (i64.ne (i64.extend_i32_u (call $w (i32.add (local.get $at) (i32.const 3)))) (local.get $expect))
              (then (call $refuse (global.get $R_constructor_grouping))))
            (local.set $expect (i64.add (local.get $expect) (i64.extend_i32_u (call $w (i32.add (local.get $at) (i32.const 4))))))
            (if (i32.ge_u (call $w (i32.add (local.get $at) (i32.const 2))) (global.get $nM))
              (then (call $refuse (global.get $R_name_index))))))
        (if (i32.eq (local.get $kind) (i32.const 3))
          (then
            (if (i32.or (call $w (i32.add (local.get $at) (i32.const 3))) (call $w (i32.add (local.get $at) (i32.const 4))))
              (then (call $refuse (global.get $R_opaque_type))))
            (if (i32.ge_u (call $w (i32.add (local.get $at) (i32.const 2))) (global.get $nM))
              (then (call $refuse (global.get $R_name_index))))))
        (if (i32.and (i32.ge_u (local.get $kind) (i32.const 1)) (i32.le_u (local.get $kind) (i32.const 2)))
          (then
            (if (i32.ne (call $w (i32.add (local.get $at) (i32.const 2))) (i32.const -1))
              (then (call $refuse (global.get $R_arrow_name))))
            (call $typeref (call $w (i32.add (local.get $at) (i32.const 3))))
            (call $typeref (call $w (i32.add (local.get $at) (i32.const 4))))))
        (local.set $at (i32.add (local.get $at) (i32.const 5)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $type)))
    (if (i64.ne (local.get $expect) (i64.extend_i32_u (global.get $nC)))
      (then (call $refuse (global.get $R_constructor_count))))

    ;; constructors: each (type, tag) filled once; tC is indexed by first + tag
    (local.set $at (i32.add (global.get $sC) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $ctor
        (br_if $end (i32.ge_u (local.get $i) (global.get $nC)))
        (local.set $len (i32.sub (call $w (local.get $at)) (i32.const 1)))
        (local.set $t (call $w (i32.add (local.get $at) (i32.const 1))))
        (if (i32.or (i32.lt_u (local.get $len) (i32.const 4))
              (i32.or (i32.ne (call $w (i32.add (local.get $at) (i32.const 4))) (i32.sub (local.get $len) (i32.const 4)))
                      (i32.ge_u (local.get $t) (global.get $nT))))
          (then (call $refuse (global.get $R_constructor_record))))
        (local.set $tag (call $w (i32.add (local.get $at) (i32.const 2))))
        (if (call $ty (local.get $t) (i32.const 0)) (then (call $refuse (global.get $R_constructor_tag))))
        (if (i32.ge_u (local.get $tag) (call $ty (local.get $t) (i32.const 3)))
          (then (call $refuse (global.get $R_constructor_tag))))
        (local.set $slot (i32.add (call $ty (local.get $t) (i32.const 2)) (local.get $tag)))
        (if (call $tab (global.get $tC) (local.get $slot)) (then (call $refuse (global.get $R_constructor_tag))))
        (call $tabset (global.get $tC) (local.get $slot) (local.get $at))
        (if (i32.ge_u (call $w (i32.add (local.get $at) (i32.const 3))) (global.get $nM))
          (then (call $refuse (global.get $R_name_index))))
        (local.set $j (i32.const 0))
        (block $fields
          (loop $field
            (br_if $fields (i32.ge_u (local.get $j) (call $w (i32.add (local.get $at) (i32.const 4)))))
            (call $typeref (call $w (i32.add (i32.add (local.get $at) (i32.const 5)) (local.get $j))))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $field)))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $ctor)))

    ;; constants: scalars hold one word; String codes stay within the plan's text
    (local.set $at (i32.add (global.get $sK) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $constant
        (br_if $end (i32.ge_u (local.get $i) (global.get $nK)))
        (call $tabset (global.get $tK) (local.get $i) (local.get $at))
        (local.set $len (i32.sub (call $w (local.get $at)) (i32.const 1)))
        (local.set $kind (call $w (i32.add (local.get $at) (i32.const 1))))
        (local.set $nw (call $w (i32.add (local.get $at) (i32.const 2))))
        (if (i32.or (i32.lt_u (local.get $len) (i32.const 2))
              (i32.or (i32.ge_u (local.get $kind) (i32.const 4))
                      (i32.ne (local.get $nw) (i32.sub (local.get $len) (i32.const 2)))))
          (then (call $refuse (global.get $R_constant_record))))
        (if (i32.and (i32.ne (local.get $kind) (i32.const 3)) (i32.ne (local.get $nw) (i32.const 1)))
          (then (call $refuse (global.get $R_scalar_constant_width))))
        (if (i32.eq (local.get $kind) (i32.const 3))
          (then
            (local.set $j (i32.const 0))
            (block $codes
              (loop $code
                (br_if $codes (i32.ge_u (local.get $j) (local.get $nw)))
                (if (i32.gt_u (call $w (i32.add (i32.add (local.get $at) (i32.const 3)) (local.get $j))) (i32.const 0x10ffff))
                  (then (call $refuse (global.get $R_string_code))))
                (local.set $j (i32.add (local.get $j) (i32.const 1)))
                (br $code)))))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $constant)))

    ;; node shapes (§3): record lengths fixed by opcode and counts
    (local.set $at (i32.add (global.get $sN) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $shape
        (br_if $end (i32.ge_u (local.get $i) (global.get $nN)))
        (i32.store8 (i32.add (global.get $mk) (local.get $at)) (i32.const 1))
        (local.set $len (i32.sub (call $w (local.get $at)) (i32.const 1)))
        (local.set $op (call $w (i32.add (local.get $at) (i32.const 1))))
        (if (i32.or (i32.lt_u (local.get $len) (i32.const 2)) (i32.ge_u (local.get $op) (i32.const 13)))
          (then (call $refuse (global.get $R_node_record))))
        (local.set $lx (i32.sub (local.get $len) (i32.const 2)))
        (block $ok
          (block $bad
            (block $closure (block $case (block $counted (block $four (block $three (block $one
              (br_table $one $counted $one $one $counted $one $counted $three $case $four $closure $counted $counted
                        (local.get $op)))
              (br_if $ok (i32.eq (local.get $lx) (i32.const 1))) (br $bad))
              (br_if $ok (i32.eq (local.get $lx) (i32.const 3))) (br $bad))
              (br_if $ok (i32.eq (local.get $lx) (i32.const 4))) (br $bad))
              (br_if $bad (i32.lt_u (local.get $lx) (i32.const 2)))
              (br_if $ok (i32.eq (i32.sub (local.get $lx) (i32.const 2)) (call $w (i32.add (local.get $at) (i32.const 4)))))
              (br $bad))
              (br_if $bad (i32.lt_u (local.get $lx) (i32.const 4)))
              (br_if $bad (i32.ge_u (call $w (i32.add (local.get $at) (i32.const 5))) (i32.const 2)))
              (br_if $ok (i64.eq (i64.extend_i32_u (local.get $lx))
                                 (i64.add (i64.const 5)
                                   (i64.mul (i64.extend_i32_u (call $w (i32.add (local.get $at) (i32.const 6))))
                                            (i64.extend_i32_u (i32.add (call $w (i32.add (local.get $at) (i32.const 5))) (i32.const 1)))))))
              (br $bad))
            (br_if $bad (i32.lt_u (local.get $lx) (i32.const 5)))
            (br_if $ok (i32.eq (i32.sub (local.get $lx) (i32.const 5)) (call $w (i32.add (local.get $at) (i32.const 6))))))
          (call $refuse (global.get $R_node_length)))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $shape)))

    ;; functions and their trees (§4 step 3), then reachability, main and the
    ;; representation table
    (global.set $tk (call $take (i32.shl (i32.add (i32.shl (global.get $W) (i32.const 1)) (i32.const 64)) (i32.const 4))))
    (global.set $tkEnd (global.get $scratch))
    (global.set $expect (i32.add (global.get $sN) (i32.const 1)))
    (local.set $at (i32.add (global.get $sF) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $function
        (br_if $end (i32.ge_u (local.get $i) (global.get $nF)))
        (call $tabset (global.get $tF) (local.get $i) (local.get $at))
        (local.set $len (i32.sub (call $w (local.get $at)) (i32.const 1)))
        (if (i32.or (i32.lt_u (local.get $len) (i32.const 5))
                    (i32.ne (call $w (i32.add (local.get $at) (i32.const 3))) (i32.sub (local.get $len) (i32.const 5))))
          (then (call $refuse (global.get $R_function_record))))
        (local.set $root (call $w (i32.add (local.get $at) (i32.const 5))))
        (if (i32.ge_u (local.get $root) (global.get $W)) (then (call $refuse (global.get $R_function_root))))
        (if (i32.ne (i32.load8_u (i32.add (global.get $mk) (local.get $root))) (i32.const 1))
          (then (call $refuse (global.get $R_function_root))))
        (i32.store8 (i32.add (global.get $mk) (local.get $root)) (i32.const 5))
        (global.set $roots (i32.add (global.get $roots) (i32.const 1)))
        (if (i32.ge_u (call $w (i32.add (local.get $at) (i32.const 1))) (global.get $nM))
          (then (call $refuse (global.get $R_name_index))))
        (local.set $j (i32.const 0))
        (block $params
          (loop $param
            (br_if $params (i32.ge_u (local.get $j) (call $w (i32.add (local.get $at) (i32.const 3)))))
            (call $typeref (call $w (i32.add (i32.add (local.get $at) (i32.const 6)) (local.get $j))))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $param)))
        (call $typeref (call $w (i32.add (local.get $at) (i32.const 2))))
        (call $walk (local.get $root))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $function)))
    (if (i32.ne (i32.add (global.get $owned) (global.get $roots)) (global.get $nN))
      (then (call $refuse (global.get $R_unreachable_node))))
    (local.set $j (call $w (i32.const 4)))
    (if (i32.ne (local.get $j) (i32.const -1))
      (then
        (if (i32.ge_u (local.get $j) (global.get $nF)) (then (call $refuse (global.get $R_main_index))))
        (if (i32.eqz (call $is_main (call $tab (global.get $tF) (local.get $j))))
          (then (call $refuse (global.get $R_main_index))))))
    (local.set $i (i32.const 0))
    (loop $rep
      (call $typeref (call $rep (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br_if $rep (i32.lt_u (local.get $i) (i32.const 12))))
    (global.set $rNat (call $rep (i32.const 0)))
    (global.set $rU32 (call $rep (i32.const 1)))
    (global.set $rChar (call $rep (i32.const 2)))
    (global.set $rString (call $rep (i32.const 3)))
    (global.set $rIoop (call $rep (i32.const 10))))

  ;; the name of function record `f` spells "main"
  (func $is_main (param $f i32) (result i32)
    (local $n i32)
    (local.set $n (call $tab (global.get $tM) (call $w (i32.add (local.get $f) (i32.const 1)))))
    (i32.and (i32.eq (call $w (i32.add (local.get $n) (i32.const 1))) (i32.const 4))
             (i32.eq (call $w (i32.add (local.get $n) (i32.const 2))) (i32.load (i32.const 44)))))

  ;; ---------------------------------------------------------------- the tree walk (§4 step 3)
  ;; Tasks are 4 words: kind, a, b, c. The walk visits each tree as
  ;; serializer.decode's tree() does and records canonical order on the way:
  ;; post-order positions, first uses of constants and closure sites (§2).
  (func $push (param $k i32) (param $a i32) (param $b i32) (param $c i32)
    (local $p i32)
    (local.set $p (global.get $tp))
    (if (i32.ge_u (local.get $p) (global.get $tkEnd)) (then (call $internal)))
    (i32.store (local.get $p) (local.get $k))
    (i32.store offset=4 (local.get $p) (local.get $a))
    (i32.store offset=8 (local.get $p) (local.get $b))
    (i32.store offset=12 (local.get $p) (local.get $c))
    (global.set $tp (i32.add (local.get $p) (i32.const 16))))

  (func $walk (param $root i32)
    (local $k i32) (local $a i32) (local $b i32) (local $c i32) (local $op i32) (local $t i32)
    (local $n i32) (local $j i32) (local $mode i32) (local $x i32) (local $last i32)
    (global.set $tp (global.get $tk))
    (call $push (i32.const 1) (local.get $root) (i32.const 0) (i32.const 0))
    (block $done
      (loop $next
        (br_if $done (i32.eq (global.get $tp) (global.get $tk)))
        (global.set $tp (i32.sub (global.get $tp) (i32.const 16)))
        (local.set $k (i32.load (global.get $tp)))
        (local.set $a (i32.load offset=4 (global.get $tp)))
        (local.set $b (i32.load offset=8 (global.get $tp)))
        (local.set $c (i32.load offset=12 (global.get $tp)))
        (block $task
          (block $post (block $caseend (block $key (block $child (block $visit (block $zero
            (br_table $zero $visit $child $key $caseend $post (local.get $k)))
            (call $internal))
            ;; VISIT(at=a, arm=b)
            (call $typeref (call $w (i32.add (local.get $a) (i32.const 2))))
            (local.set $op (call $w (i32.add (local.get $a) (i32.const 1))))
            (if (i32.and (i32.or (i32.eq (local.get $op) (i32.const 9)) (i32.eq (local.get $op) (i32.const 2)))
                         (i32.eqz (local.get $b)))
              (then (call $refuse (global.get $R_standalone_arm))))
            (call $push (i32.const 5) (local.get $a) (i32.const 0) (i32.const 0))
            (local.set $last (call $w (i32.add (local.get $a) (i32.sub (call $w (local.get $a)) (i32.const 1)))))
            (block $kids
              (block $invoke (block $case (block $let (block $counted (block $lastkid (block $lit (block $leaf
                (br_table $lit $counted $lastkid $leaf $counted $leaf $counted $let $case $lastkid $lastkid $invoke $counted
                          (local.get $op)))
                (br $kids))
                ;; Literal: a known constant
                (if (i32.ge_u (call $w (i32.add (local.get $a) (i32.const 3))) (global.get $nK))
                  (then (call $refuse (global.get $R_constant_index))))
                (br $kids))
                ;; Default, Branch and Closure: one child, the record's last word
                (call $push (i32.const 2) (local.get $a) (local.get $last) (i32.const 0))
                (br $kids))
                ;; Intrinsic, Construct, Application, Foreign: operands in order
                (local.set $n (call $w (i32.add (local.get $a) (i32.const 4))))
                (local.set $j (local.get $n))
                (block $pushed
                  (loop $each
                    (br_if $pushed (i32.eqz (local.get $j)))
                    (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                    (call $push (i32.const 2) (local.get $a)
                      (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j))) (i32.const 0))
                    (br $each)))
                (br $kids))
                ;; Let: value, then body
                (call $push (i32.const 2) (local.get $a) (call $w (i32.add (local.get $a) (i32.const 5))) (i32.const 0))
                (call $push (i32.const 2) (local.get $a) (call $w (i32.add (local.get $a) (i32.const 4))) (i32.const 0))
                (br $kids))
                ;; Case: rows, the default, then the arm kinds
                (local.set $mode (call $w (i32.add (local.get $a) (i32.const 5))))
                (local.set $n (call $w (i32.add (local.get $a) (i32.const 6))))
                (call $push (i32.const 4) (local.get $a) (i32.const 0) (i32.const 0))
                (if (i32.ne (local.get $last) (i32.const -1))
                  (then (call $push (i32.const 2) (local.get $a) (local.get $last) (i32.const 1))))
                (local.set $j (local.get $n))
                (block $pushed
                  (loop $each
                    (br_if $pushed (i32.eqz (local.get $j)))
                    (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                    (if (local.get $mode)
                      (then
                        (local.set $x (call $w (i32.add (i32.add (local.get $a) (i32.const 8)) (i32.shl (local.get $j) (i32.const 1)))))
                        (call $push (i32.const 3) (local.get $x)
                          (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (i32.shl (local.get $j) (i32.const 1)))) (i32.const 0))
                        (call $push (i32.const 2) (local.get $a) (local.get $x) (i32.const 1)))
                      (else
                        (local.set $x (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (local.get $j))))
                        (if (i32.ne (local.get $x) (i32.const -1))
                          (then (call $push (i32.const 2) (local.get $a) (local.get $x) (i32.const 1))))))
                    (br $each)))
                (br $kids))
              ;; Invoke: function, then its argument
              (local.set $n (call $w (i32.add (local.get $a) (i32.const 4))))
              (local.set $j (local.get $n))
              (block $pushed
                (loop $each
                  (br_if $pushed (i32.eqz (local.get $j)))
                  (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                  (call $push (i32.const 2) (local.get $a)
                    (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j))) (i32.const 0))
                  (br $each)))
              (call $push (i32.const 2) (local.get $a) (call $w (i32.add (local.get $a) (i32.const 3))) (i32.const 0)))
            (br $task))
            ;; CHILD(parent=a, offset=b, arm=c)
            (if (i32.ge_u (local.get $b) (global.get $W)) (then (call $refuse (global.get $R_child_offset))))
            (local.set $x (i32.load8_u (i32.add (global.get $mk) (local.get $b))))
            (if (i32.eqz (i32.and (local.get $x) (i32.const 1))) (then (call $refuse (global.get $R_child_offset))))
            (if (i32.ge_u (local.get $b) (local.get $a)) (then (call $refuse (global.get $R_child_after_parent))))
            (if (i32.and (local.get $x) (i32.const 2)) (then (call $refuse (global.get $R_shared_node))))
            (i32.store8 (i32.add (global.get $mk) (local.get $b)) (i32.or (local.get $x) (i32.const 2)))
            (global.set $owned (i32.add (global.get $owned) (i32.const 1)))
            (call $push (i32.const 1) (local.get $b) (local.get $c) (i32.const 0))
            (br $task))
            ;; KEY(arm=a, key=b): a key row's arm is a Branch with that key
            (if (i32.or (i32.ne (call $w (i32.add (local.get $a) (i32.const 1))) (i32.const 9))
                        (i32.ne (call $w (i32.add (local.get $a) (i32.const 3))) (local.get $b)))
              (then (call $refuse (global.get $R_case_key))))
            (br $task))
            ;; CASEEND(case=a): arm kinds, the scrutinee type, and (canonical)
            ;; arms carrying their Case's result type
            (local.set $mode (call $w (i32.add (local.get $a) (i32.const 5))))
            (local.set $n (call $w (i32.add (local.get $a) (i32.const 6))))
            (local.set $t (call $w (i32.add (local.get $a) (i32.const 2))))
            (local.set $j (i32.const 0))
            (block $rows
              (loop $row
                (br_if $rows (i32.ge_u (local.get $j) (local.get $n)))
                (local.set $x (if (result i32) (local.get $mode)
                  (then (call $w (i32.add (i32.add (local.get $a) (i32.const 8)) (i32.shl (local.get $j) (i32.const 1)))))
                  (else (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (local.get $j))))))
                (if (i32.ne (local.get $x) (i32.const -1))
                  (then
                    (if (i32.ne (call $w (i32.add (local.get $x) (i32.const 1))) (i32.const 9))
                      (then (call $refuse (global.get $R_case_arm_kind))))
                    (if (i32.ne (call $w (i32.add (local.get $x) (i32.const 2))) (local.get $t))
                      (then (global.set $noncanon (i32.const 1))))))
                (local.set $j (i32.add (local.get $j) (i32.const 1)))
                (br $row)))
            (local.set $x (call $w (i32.add (local.get $a) (i32.sub (call $w (local.get $a)) (i32.const 1)))))
            (if (i32.ne (local.get $x) (i32.const -1))
              (then
                (if (i32.ne (call $w (i32.add (local.get $x) (i32.const 1))) (i32.const 2))
                  (then (call $refuse (global.get $R_case_arm_kind))))
                (if (i32.ne (call $w (i32.add (local.get $x) (i32.const 2))) (local.get $t))
                  (then (global.set $noncanon (i32.const 1))))))
            (call $typeref (call $w (i32.add (local.get $a) (i32.const 4))))
            (br $task))
          ;; POST(at=a): canonical post-order, constant first uses, closure sites
          (if (i32.ne (local.get $a) (global.get $expect)) (then (global.set $noncanon (i32.const 1))))
          (global.set $expect (i32.add (local.get $a) (call $w (local.get $a))))
          (local.set $op (call $w (i32.add (local.get $a) (i32.const 1))))
          (if (i32.eqz (local.get $op))
            (then
              (local.set $x (call $w (i32.add (local.get $a) (i32.const 3))))
              (if (i32.eq (local.get $x) (global.get $nextConst))
                (then (global.set $nextConst (i32.add (local.get $x) (i32.const 1))))
                (else (if (i32.gt_u (local.get $x) (global.get $nextConst))
                  (then (global.set $noncanon (i32.const 1))))))))
          (if (i32.eq (local.get $op) (i32.const 10))
            (then
              (if (i32.ne (call $w (i32.add (local.get $a) (i32.const 3))) (global.get $nextSite))
                (then (global.set $noncanon (i32.const 1))))
              (global.set $nextSite (i32.add (global.get $nextSite) (i32.const 1))))))
        (br $next))))

  ;; ---------------------------------------------------------------- validation (§4 step 4)
  ;; A value of type `a` fits where `d` is declared: `none` fits anything,
  ;; arrows of one kind fit position by position (§3). Iterative over a stack
  ;; in the frame region's upper half; pairs already entered are memoized,
  ;; since any failing pair ends validation.
  (func $fits (param $d i32) (param $a i32) (result i32)
    (local $sp i32) (local $x i32) (local $y i32) (local $kx i32)
    (local.set $sp (global.get $fs))
    (i32.store (local.get $sp) (local.get $d))
    (i32.store offset=4 (local.get $sp) (local.get $a))
    (local.set $sp (i32.add (local.get $sp) (i32.const 8)))
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $sp) (global.get $fs)))
        (local.set $sp (i32.sub (local.get $sp) (i32.const 8)))
        (local.set $x (i32.load (local.get $sp)))
        (local.set $y (i32.load offset=4 (local.get $sp)))
        (br_if $next (i32.or (i32.or (i32.eq (local.get $x) (i32.const -1)) (i32.eq (local.get $y) (i32.const -1)))
                             (i32.eq (local.get $x) (local.get $y))))
        (local.set $kx (call $kind (local.get $x)))
        (if (i32.or (i32.or (i32.eqz (local.get $kx)) (i32.ge_u (local.get $kx) (i32.const 3)))
                    (i32.ne (local.get $kx) (call $kind (local.get $y))))
          (then (return (i32.const 0))))
        (br_if $next (call $entered (local.get $x) (local.get $y)))
        (i32.store (local.get $sp) (call $ty (local.get $x) (i32.const 2)))
        (i32.store offset=4 (local.get $sp) (call $ty (local.get $y) (i32.const 2)))
        (i32.store offset=8 (local.get $sp) (call $ty (local.get $x) (i32.const 3)))
        (i32.store offset=12 (local.get $sp) (call $ty (local.get $y) (i32.const 3)))
        (local.set $sp (i32.add (local.get $sp) (i32.const 16)))
        (br $next)))
    (i32.const 1))

  ;; Insert the arrow pair (x, y) into the memo; 1 when it was already there.
  ;; The table doubles when half full.
  (func $entered (param $x i32) (param $y i32) (result i32)
    (local $e i32) (local $old i32) (local $cap i32) (local $i i32)
    (if (i32.ge_u (i32.shl (global.get $psN) (i32.const 1)) (global.get $psCap))
      (then
        (local.set $old (global.get $psT))
        (local.set $cap (global.get $psCap))
        (global.set $psCap (i32.shl (local.get $cap) (i32.const 1)))
        (global.set $psT (call $take (i32.shl (global.get $psCap) (i32.const 3))))
        (global.set $psN (i32.const 0))
        (block $moved
          (loop $move
            (br_if $moved (i32.ge_u (local.get $i) (local.get $cap)))
            (local.set $e (i32.add (local.get $old) (i32.shl (local.get $i) (i32.const 3))))
            (if (i32.load (local.get $e))
              (then (drop (call $pairslot (i32.sub (i32.load (local.get $e)) (i32.const 1)) (i32.load offset=4 (local.get $e))))))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $move)))))
    (call $pairslot (local.get $x) (local.get $y)))

  ;; open addressing without growth; entries hold x + 1 so zero is empty
  (func $pairslot (param $x i32) (param $y i32) (result i32)
    (local $h i32) (local $e i32)
    (local.set $h (i32.and (i32.mul (i32.xor (i32.mul (local.get $x) (i32.const 0x9e3779b1)) (local.get $y))
                                    (i32.const 0x85ebca6b))
                           (i32.sub (global.get $psCap) (i32.const 1))))
    (loop $probe
      (local.set $e (i32.add (global.get $psT) (i32.shl (local.get $h) (i32.const 3))))
      (if (i32.eqz (i32.load (local.get $e)))
        (then
          (i32.store (local.get $e) (i32.add (local.get $x) (i32.const 1)))
          (i32.store offset=4 (local.get $e) (local.get $y))
          (global.set $psN (i32.add (global.get $psN) (i32.const 1)))
          (return (i32.const 0))))
      (if (i32.and (i32.eq (i32.load (local.get $e)) (i32.add (local.get $x) (i32.const 1)))
                   (i32.eq (i32.load offset=4 (local.get $e)) (local.get $y)))
        (then (return (i32.const 1))))
      (local.set $h (i32.and (i32.add (local.get $h) (i32.const 1)) (i32.sub (global.get $psCap) (i32.const 1))))
      (br $probe))
    (i32.const 0))

  ;; t is IO(x) = @-R -> (x -> IO.OP<R>) -> IO.OP<R>, x concrete (§8)
  (func $io (param $t i32) (param $x i32) (result i32)
    (local $live i32) (local $k i32)
    (if (i32.or (i32.or (i32.eq (local.get $x) (i32.const -1)) (i32.eq (global.get $rIoop) (i32.const -1)))
                (i32.ne (call $kind (local.get $t)) (i32.const 2)))
      (then (return (i32.const 0))))
    (if (i32.ne (call $ty (local.get $t) (i32.const 2)) (i32.const -1)) (then (return (i32.const 0))))
    (local.set $live (call $ty (local.get $t) (i32.const 3)))
    (if (i32.or (i32.ne (call $kind (local.get $live)) (i32.const 1))
                (i32.ne (call $ty (local.get $live) (i32.const 3)) (global.get $rIoop)))
      (then (return (i32.const 0))))
    (local.set $k (call $ty (local.get $live) (i32.const 2)))
    (i32.and (i32.eq (call $kind (local.get $k)) (i32.const 1))
      (i32.and (i32.eq (call $ty (local.get $k) (i32.const 2)) (local.get $x))
               (i32.eq (call $ty (local.get $k) (i32.const 3)) (global.get $rIoop)))))

  ;; the registry position whose representation is type t, or 0xff
  (func $repof (param $t i32) (result i32)
    (if (result i32) (i32.eq (local.get $t) (i32.const -1))
      (then (i32.const 0xff))
      (else (i32.load8_u (i32.add (global.get $ro) (local.get $t))))))

  (func $validate
    (local $r i32) (local $t i32) (local $shape i32) (local $n i32) (local $c i32) (local $rec i32)
    (local $nf i32) (local $j i32) (local $e i32) (local $f i32) (local $at i32) (local $i i32)
    (local $seen i32) (local $col i32) (local $sp i32) (local $u i32) (local $v i32) (local $main i32)
    ;; scratch for this phase
    (global.set $ro (call $take (i32.add (global.get $nT) (i32.const 8))))
    (memory.fill (global.get $ro) (i32.const 0xff) (global.get $nT))
    (local.set $r (i32.const 12))
    (loop $each
      (local.set $r (i32.sub (local.get $r) (i32.const 1)))
      (local.set $t (call $rep (local.get $r)))
      (if (i32.ne (local.get $t) (i32.const -1))
        (then (i32.store8 (i32.add (global.get $ro) (local.get $t)) (local.get $r))))
      (br_if $each (local.get $r)))
    (global.set $sc (call $take (i32.shl (i32.add (global.get $W) (i32.const 4200)) (i32.const 2))))
    (global.set $us (call $take (i32.add (global.get $W) (i32.const 4200))))
    (global.set $fs (i32.add (global.get $F0) (i32.const 0x800000)))
    (global.set $psCap (i32.const 1024))
    (global.set $psT (call $take (i32.const 8192)))

    ;; §2 representations: opaque U32 and File, pinned constructor shapes
    (local.set $r (i32.const 0))
    (loop $each
      (local.set $t (call $rep (local.get $r)))
      (if (i32.ne (local.get $t) (i32.const -1))
        (then
          (local.set $shape (i32.add (i32.const 384) (i32.shl (local.get $r) (i32.const 3))))
          (local.set $n (i32.load8_u (local.get $shape)))
          (if (i32.eq (local.get $n) (i32.const 0xfe))
            (then (if (i32.ne (call $kind (local.get $t)) (i32.const 3))
                    (then (call $refuse (global.get $R_representation_opaque)))))
            (else
              (if (i32.or (call $kind (local.get $t)) (i32.ne (call $ty (local.get $t) (i32.const 3)) (local.get $n)))
                (then (call $refuse (global.get $R_representation_shape))))
              (local.set $shape (i32.add (local.get $shape) (i32.const 1)))
              (local.set $c (i32.const 0))
              (block $ctors
                (loop $ctor
                  (br_if $ctors (i32.ge_u (local.get $c) (local.get $n)))
                  (local.set $rec (call $ctorv (local.get $t) (local.get $c)))
                  (local.set $nf (i32.load8_u (local.get $shape)))
                  (local.set $shape (i32.add (local.get $shape) (i32.const 1)))
                  (if (i32.ne (call $w (i32.add (local.get $rec) (i32.const 4))) (local.get $nf))
                    (then (call $refuse (global.get $R_representation_shape))))
                  (local.set $j (i32.const 0))
                  (block $fields
                    (loop $field
                      (br_if $fields (i32.ge_u (local.get $j) (local.get $nf)))
                      (local.set $e (i32.load8_u (local.get $shape)))
                      (local.set $shape (i32.add (local.get $shape) (i32.const 1)))
                      (local.set $f (call $w (i32.add (i32.add (local.get $rec) (i32.const 5)) (local.get $j))))
                      (if (i32.eq (local.get $e) (i32.const 0xff))
                        (then (if (i32.ne (local.get $f) (i32.const -1))
                                (then (call $refuse (global.get $R_representation_shape)))))
                        (else (if (i32.or (i32.eq (call $rep (local.get $e)) (i32.const -1))
                                          (i32.ne (local.get $f) (call $rep (local.get $e))))
                                (then (call $refuse (global.get $R_representation_shape))))))
                      (local.set $j (i32.add (local.get $j) (i32.const 1)))
                      (br $field)))
                  (local.set $c (i32.add (local.get $c) (i32.const 1)))
                  (br $ctor)))))))
      (local.set $r (i32.add (local.get $r) (i32.const 1)))
      (br_if $each (i32.lt_u (local.get $r) (i32.const 12))))

    ;; function names are unique
    (local.set $seen (call $take (i32.add (global.get $nM) (i32.const 8))))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nF)))
        (local.set $n (call $w (i32.add (call $tab (global.get $tF) (local.get $i)) (i32.const 1))))
        (if (i32.load8_u (i32.add (local.get $seen) (local.get $n)))
          (then (call $refuse (global.get $R_duplicate_function))))
        (i32.store8 (i32.add (local.get $seen) (local.get $n)) (i32.const 1))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))

    ;; arrow types are acyclic through their domains and results: a
    ;; depth-first search with colours (1 on the path, 2 done)
    (local.set $col (call $take (i32.add (global.get $nT) (i32.const 8))))
    (local.set $sp (call $take (i32.shl (i32.add (global.get $nT) (i32.const 2)) (i32.const 3))))
    (local.set $at (local.get $sp))
    (local.set $t (i32.const 0))
    (block $end
      (loop $root
        (br_if $end (i32.ge_u (local.get $t) (global.get $nT)))
        (if (i32.and (i32.eqz (i32.load8_u (i32.add (local.get $col) (local.get $t))))
                     (i32.and (i32.ge_u (call $kind (local.get $t)) (i32.const 1))
                              (i32.le_u (call $kind (local.get $t)) (i32.const 2))))
          (then
            (i32.store8 (i32.add (local.get $col) (local.get $t)) (i32.const 1))
            (i32.store (local.get $sp) (local.get $t))
            (i32.store offset=4 (local.get $sp) (i32.const 0))
            (local.set $sp (i32.add (local.get $sp) (i32.const 8)))
            (block $finished
              (loop $step
                (br_if $finished (i32.eq (local.get $sp) (local.get $at)))
                (local.set $u (i32.load (i32.sub (local.get $sp) (i32.const 8))))
                (local.set $e (i32.load (i32.sub (local.get $sp) (i32.const 4))))
                (if (i32.ge_u (local.get $e) (i32.const 2))
                  (then
                    (i32.store8 (i32.add (local.get $col) (local.get $u)) (i32.const 2))
                    (local.set $sp (i32.sub (local.get $sp) (i32.const 8)))
                    (br $step)))
                (i32.store (i32.sub (local.get $sp) (i32.const 4)) (i32.add (local.get $e) (i32.const 1)))
                (local.set $v (call $ty (local.get $u) (i32.add (i32.const 2) (local.get $e))))
                (if (i32.and (i32.ge_u (call $kind (local.get $v)) (i32.const 1)) (i32.le_u (call $kind (local.get $v)) (i32.const 2)))
                  (then
                    (local.set $c (i32.load8_u (i32.add (local.get $col) (local.get $v))))
                    (if (i32.eq (local.get $c) (i32.const 1)) (then (call $refuse (global.get $R_arrow_cycle))))
                    (if (i32.eqz (local.get $c))
                      (then
                        (i32.store8 (i32.add (local.get $col) (local.get $v)) (i32.const 1))
                        (i32.store (local.get $sp) (local.get $v))
                        (i32.store offset=4 (local.get $sp) (i32.const 0))
                        (local.set $sp (i32.add (local.get $sp) (i32.const 8)))))))
                (br $step)))))
        (local.set $t (i32.add (local.get $t) (i32.const 1)))
        (br $root)))

    ;; §8 Program: main takes no live argument and returns IO(Unit)
    (if (i32.eq (call $w (i32.const 3)) (i32.const 1))
      (then
        (local.set $main (i32.const -1))
        (local.set $i (i32.const 0))
        (block $found
          (loop $each
            (br_if $found (i32.ge_u (local.get $i) (global.get $nF)))
            (if (call $is_main (call $tab (global.get $tF) (local.get $i)))
              (then (local.set $main (call $tab (global.get $tF) (local.get $i))) (br $found)))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $each)))
        (if (i32.or (i32.eq (local.get $main) (i32.const -1))
                    (call $w (i32.add (local.get $main) (i32.const 3))))
          (then (call $refuse (global.get $R_program_main))))
        (if (i32.or (i32.eq (call $rep (i32.const 6)) (i32.const -1))
              (i32.or (i32.eq (call $rep (i32.const 3)) (i32.const -1)) (i32.eq (call $rep (i32.const 10)) (i32.const -1))))
          (then (call $refuse (global.get $R_program_representation))))
        (if (i32.eqz (call $io (call $w (i32.add (local.get $main) (i32.const 2))) (call $rep (i32.const 6))))
          (then (call $refuse (global.get $R_program_io))))))

    ;; §3 scope, arity and type rules, function by function
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nF)))
        (call $check (call $tab (global.get $tF) (local.get $i)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each))))

  ;; scope type and use marks at absolute scope index
  (func $scope (param $s i32) (result i32)
    (i32.load (i32.add (global.get $sc) (i32.shl (local.get $s) (i32.const 2)))))
  (func $setscope (param $s i32) (param $t i32)
    (i32.store (i32.add (global.get $sc) (i32.shl (local.get $s) (i32.const 2))) (local.get $t)))
  (func $use (param $s i32)
    (i32.store8 (i32.add (global.get $us) (local.get $s)) (i32.const 1)))
  (func $nodetype (param $n i32) (result i32)
    (call $w (i32.add (local.get $n) (i32.const 2))))

  ;; One function: tasks as serializer.validate's check() recursion orders
  ;; them, stopping at the first defect. Kinds: 1 NODE(n, depth) 2 POST(n)
  ;; 3 SETSCOPE(index, type) 4 ROW(case, i, depth) 5 ROWPOST(case, arm)
  ;; 6 DEFAULT(case, depth) 7 DEFPOST(case, default) 8 CLOSE(closure, base,
  ;; deepest) 9 END(function).
  (func $check (param $fn i32)
    (local $k i32) (local $a i32) (local $b i32) (local $c i32) (local $j i32)
    (local $n i32) (local $d i32) (local $t i32) (local $op i32) (local $x i32) (local $y i32)
    (local $s i32) (local $mode i32) (local $cnt i32) (local $last i32) (local $rec i32) (local $nf i32)
    (local $row i32) (local $kd i32) (local $live i32) (local $nb i32)
    (if (i32.or (i32.gt_u (call $w (i32.add (local.get $fn) (i32.const 3))) (i32.const 4096))
                (i32.gt_u (call $w (i32.add (local.get $fn) (i32.const 4))) (i32.const 65536)))
      (then (call $refuse (global.get $R_limits))))
    (global.set $vbase (i32.const 0))
    (global.set $vdeep (i32.const 0))
    (local.set $n (call $w (i32.add (local.get $fn) (i32.const 3))))
    (local.set $j (i32.const 0))
    (block $params
      (loop $param
        (br_if $params (i32.ge_u (local.get $j) (local.get $n)))
        (call $setscope (local.get $j) (call $w (i32.add (i32.add (local.get $fn) (i32.const 6)) (local.get $j))))
        (local.set $j (i32.add (local.get $j) (i32.const 1)))
        (br $param)))
    (global.set $tp (global.get $tk))
    (call $push (i32.const 9) (local.get $fn) (i32.const 0) (i32.const 0))
    (call $push (i32.const 1) (call $w (i32.add (local.get $fn) (i32.const 5))) (local.get $n) (i32.const 0))
    (block $done
      (loop $next
        (br_if $done (i32.eq (global.get $tp) (global.get $tk)))
        (global.set $tp (i32.sub (global.get $tp) (i32.const 16)))
        (local.set $k (i32.load (global.get $tp)))
        (local.set $a (i32.load offset=4 (global.get $tp)))
        (local.set $b (i32.load offset=8 (global.get $tp)))
        (local.set $c (i32.load offset=12 (global.get $tp)))
        (block $task
          (block $end (block $close (block $defpost (block $default (block $rowpost (block $row (block $setscope
          (block $post (block $node (block $zero
            (br_table $zero $node $post $setscope $row $rowpost $default $defpost $close $end (local.get $k)))
            (call $internal))
            ;; NODE(n=a, depth=b)
            (local.set $d (local.get $b))
            (if (i32.gt_u (local.get $d) (global.get $vdeep)) (then (global.set $vdeep (local.get $d))))
            (local.set $t (call $nodetype (local.get $a)))
            (local.set $op (call $w (i32.add (local.get $a) (i32.const 1))))
            (local.set $last (call $w (i32.add (local.get $a) (i32.sub (call $w (local.get $a)) (i32.const 1)))))
            (block $kinds
              (block $invoke (block $closure (block $case (block $let (block $gather (block $ref (block $value (block $lit (block $arm
                (br_table $lit $gather $arm $value $gather $ref $gather $let $case $arm $closure $invoke $gather (local.get $op)))
                (call $internal))
                ;; Literal: its constant's kind is the representation of its type
                (local.set $x (call $w (i32.add (call $tab (global.get $tK) (call $w (i32.add (local.get $a) (i32.const 3))))
                                               (i32.const 1))))
                (if (i32.ne (call $repof (local.get $t)) (i32.load8_u (i32.add (i32.const 60) (local.get $x))))
                  (then (call $refuse (global.get $R_literal_kind))))
                (br $kinds))
                ;; Value: a nullary constructor of an algebraic type
                (local.set $x (call $w (i32.add (local.get $a) (i32.const 3))))
                (if (call $kind (local.get $t)) (then (call $refuse (global.get $R_value_nullary))))
                (if (i32.ge_u (local.get $x) (call $ty (local.get $t) (i32.const 3)))
                  (then (call $refuse (global.get $R_value_nullary))))
                (if (call $w (i32.add (call $ctorv (local.get $t) (local.get $x)) (i32.const 4)))
                  (then (call $refuse (global.get $R_value_nullary))))
                (br $kinds))
                ;; Reference: a slot below the depth, of exactly its type
                (local.set $s (call $w (i32.add (local.get $a) (i32.const 3))))
                (if (i32.ge_u (local.get $s) (local.get $d)) (then (call $refuse (global.get $R_slot_depth))))
                (call $use (i32.add (global.get $vbase) (local.get $s)))
                (if (i32.ne (call $scope (i32.add (global.get $vbase) (local.get $s))) (local.get $t))
                  (then (call $refuse (global.get $R_reference_type))))
                (br $kinds))
                ;; Construct, Application, Intrinsic, Foreign: operands, then the node
                (call $push (i32.const 2) (local.get $a) (local.get $d) (i32.const 0))
                (local.set $j (call $w (i32.add (local.get $a) (i32.const 4))))
                (block $pushed
                  (loop $each
                    (br_if $pushed (i32.eqz (local.get $j)))
                    (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                    (call $push (i32.const 1) (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j)))
                                (local.get $d) (i32.const 0))
                    (br $each)))
                (br $kinds))
                ;; Let: binds slot = depth; body one deeper, typed by the value
                (if (i32.ne (call $w (i32.add (local.get $a) (i32.const 3))) (local.get $d))
                  (then (call $refuse (global.get $R_let_slot))))
                (local.set $x (call $w (i32.add (local.get $a) (i32.const 4))))
                (call $push (i32.const 2) (local.get $a) (local.get $d) (i32.const 0))
                (call $push (i32.const 1) (call $w (i32.add (local.get $a) (i32.const 5))) (i32.add (local.get $d) (i32.const 1)) (i32.const 0))
                (call $push (i32.const 3) (i32.add (global.get $vbase) (local.get $d)) (call $nodetype (local.get $x)) (i32.const 0))
                (call $push (i32.const 1) (local.get $x) (local.get $d) (i32.const 0))
                (br $kinds))
                ;; Case: the scrutinee slot, its concrete type, then the table
                (local.set $s (call $w (i32.add (local.get $a) (i32.const 3))))
                (if (i32.ge_u (local.get $s) (local.get $d)) (then (call $refuse (global.get $R_case_slot))))
                (call $use (i32.add (global.get $vbase) (local.get $s)))
                (local.set $y (call $w (i32.add (local.get $a) (i32.const 4))))
                (if (i32.or (i32.eq (local.get $y) (i32.const -1))
                            (i32.ne (call $scope (i32.add (global.get $vbase) (local.get $s))) (local.get $y)))
                  (then (call $refuse (global.get $R_case_scrutinee_type))))
                (local.set $mode (call $w (i32.add (local.get $a) (i32.const 5))))
                (local.set $cnt (call $w (i32.add (local.get $a) (i32.const 6))))
                (if (i32.eqz (local.get $mode))
                  (then
                    (if (call $kind (local.get $y)) (then (call $refuse (global.get $R_tag_case_type))))
                    (if (i32.ne (local.get $cnt) (call $ty (local.get $y) (i32.const 3)))
                      (then (call $refuse (global.get $R_tag_table))))
                    (local.set $x (i32.const 1))
                    (local.set $j (i32.const 0))
                    (block $rows
                      (loop $each
                        (br_if $rows (i32.ge_u (local.get $j) (local.get $cnt)))
                        (if (i32.eq (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (local.get $j))) (i32.const -1))
                          (then (local.set $x (i32.const 0))))
                        (local.set $j (i32.add (local.get $j) (i32.const 1)))
                        (br $each)))
                    (if (i32.ne (i32.eq (local.get $last) (i32.const -1)) (local.get $x))
                      (then (call $refuse (global.get $R_default_coverage)))))
                  (else
                    (if (i32.or (i32.eq (local.get $y) (i32.const -1))
                                (i32.and (i32.ne (local.get $y) (global.get $rU32)) (i32.ne (local.get $y) (global.get $rChar))))
                      (then (call $refuse (global.get $R_key_case_type))))
                    (if (i32.eq (local.get $last) (i32.const -1)) (then (call $refuse (global.get $R_key_order))))
                    (local.set $j (i32.const 1))
                    (block $rows
                      (loop $each
                        (br_if $rows (i32.ge_u (local.get $j) (local.get $cnt)))
                        (if (i32.ge_u (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (i32.shl (local.get $j) (i32.const 1))))
                                      (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (i32.shl (local.get $j) (i32.const 1)))))
                          (then (call $refuse (global.get $R_key_order))))
                        (local.set $j (i32.add (local.get $j) (i32.const 1)))
                        (br $each)))))
                (if (i32.ne (local.get $last) (i32.const -1))
                  (then (call $push (i32.const 6) (local.get $a) (local.get $d) (i32.const 0))))
                (local.set $j (local.get $cnt))
                (block $pushed
                  (loop $each
                    (br_if $pushed (i32.eqz (local.get $j)))
                    (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                    (call $push (i32.const 4) (local.get $a) (local.get $j) (local.get $d))
                    (br $each)))
                (br $kinds))
                ;; Closure: its arrow, strictly increasing captures below the
                ;; depth, and a body checked as a unit of its own
                (local.set $kd (call $kind (local.get $t)))
                (local.set $live (call $w (i32.add (local.get $a) (i32.const 4))))
                (if (i32.or (i32.or (i32.eqz (local.get $kd)) (i32.ge_u (local.get $kd) (i32.const 3)))
                            (i32.ne (local.get $live) (i32.eq (local.get $kd) (i32.const 1))))
                  (then (call $refuse (global.get $R_closure_arrow))))
                (local.set $cnt (call $w (i32.add (local.get $a) (i32.const 6))))
                (local.set $j (i32.const 0))
                (block $caps
                  (loop $each
                    (br_if $caps (i32.ge_u (local.get $j) (local.get $cnt)))
                    (local.set $x (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (local.get $j))))
                    (if (i32.ge_u (local.get $x) (local.get $d)) (then (call $refuse (global.get $R_capture_order))))
                    (if (local.get $j)
                      (then (if (i32.ge_u (call $w (i32.add (i32.add (local.get $a) (i32.const 6)) (local.get $j))) (local.get $x))
                              (then (call $refuse (global.get $R_capture_order))))))
                    (local.set $j (i32.add (local.get $j) (i32.const 1)))
                    (br $each)))
                (local.set $nb (i32.add (global.get $vbase) (local.get $d)))
                (local.set $j (i32.const 0))
                (block $caps
                  (loop $each
                    (br_if $caps (i32.ge_u (local.get $j) (local.get $cnt)))
                    (local.set $x (i32.add (global.get $vbase) (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (local.get $j)))))
                    (call $use (local.get $x))
                    (call $setscope (i32.add (local.get $nb) (local.get $j)) (call $scope (local.get $x)))
                    (i32.store8 (i32.add (global.get $us) (i32.add (local.get $nb) (local.get $j))) (i32.const 0))
                    (local.set $j (i32.add (local.get $j) (i32.const 1)))
                    (br $each)))
                (if (local.get $live)
                  (then (call $setscope (i32.add (local.get $nb) (local.get $cnt)) (call $ty (local.get $t) (i32.const 2)))))
                (call $push (i32.const 8) (local.get $a) (global.get $vbase) (global.get $vdeep))
                (global.set $vbase (local.get $nb))
                (global.set $vdeep (i32.const 0))
                (call $push (i32.const 1) (local.get $last) (i32.add (local.get $cnt) (local.get $live)) (i32.const 0))
                (br $kinds))
              ;; Invoke: function, argument, then the node
              (call $push (i32.const 2) (local.get $a) (local.get $d) (i32.const 0))
              (local.set $j (call $w (i32.add (local.get $a) (i32.const 4))))
              (block $pushed
                (loop $each
                  (br_if $pushed (i32.eqz (local.get $j)))
                  (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                  (call $push (i32.const 1) (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j)))
                              (local.get $d) (i32.const 0))
                  (br $each)))
              (call $push (i32.const 1) (call $w (i32.add (local.get $a) (i32.const 3))) (local.get $d) (i32.const 0)))
            (br $task))
            ;; POST(n=a): the node's own rules after its operands
            (call $post (local.get $a))
            (br $task))
            ;; SETSCOPE(index=a, type=b)
            (call $setscope (local.get $a) (local.get $b))
            (br $task))
            ;; ROW(case=a, i=b, depth=c)
            (local.set $y (call $w (i32.add (local.get $a) (i32.const 4))))
            (if (call $w (i32.add (local.get $a) (i32.const 5)))
              (then
                (local.set $row (call $w (i32.add (i32.add (local.get $a) (i32.const 8)) (i32.shl (local.get $b) (i32.const 1)))))
                (if (i32.or (i32.ne (call $w (i32.add (local.get $row) (i32.const 4))) (local.get $c))
                            (call $w (i32.add (local.get $row) (i32.const 5))))
                  (then (call $refuse (global.get $R_key_branch_binders))))
                (call $push (i32.const 5) (local.get $a) (local.get $row) (i32.const 0))
                (call $push (i32.const 1) (call $w (i32.add (local.get $row) (i32.const 6))) (local.get $c) (i32.const 0)))
              (else
                (local.set $row (call $w (i32.add (i32.add (local.get $a) (i32.const 7)) (local.get $b))))
                (if (i32.ne (local.get $row) (i32.const -1))
                  (then
                    (if (i32.ne (call $w (i32.add (local.get $row) (i32.const 3))) (local.get $b))
                      (then (call $refuse (global.get $R_branch_key))))
                    (local.set $rec (call $ctorv (local.get $y) (local.get $b)))
                    (local.set $nf (call $w (i32.add (local.get $rec) (i32.const 4))))
                    (if (i32.or (i32.ne (call $w (i32.add (local.get $row) (i32.const 4))) (local.get $c))
                                (i32.ne (call $w (i32.add (local.get $row) (i32.const 5))) (local.get $nf)))
                      (then (call $refuse (global.get $R_branch_binders))))
                    (local.set $j (i32.const 0))
                    (block $fields
                      (loop $field
                        (br_if $fields (i32.ge_u (local.get $j) (local.get $nf)))
                        (call $setscope (i32.add (i32.add (global.get $vbase) (local.get $c)) (local.get $j))
                                        (call $w (i32.add (i32.add (local.get $rec) (i32.const 5)) (local.get $j))))
                        (local.set $j (i32.add (local.get $j) (i32.const 1)))
                        (br $field)))
                    (call $push (i32.const 5) (local.get $a) (local.get $row) (i32.const 0))
                    (call $push (i32.const 1) (call $w (i32.add (local.get $row) (i32.const 6)))
                                (i32.add (local.get $c) (local.get $nf)) (i32.const 0))))))
            (br $task))
            ;; ROWPOST(case=a, arm=b)
            (if (i32.ne (call $nodetype (call $w (i32.add (local.get $b) (i32.const 6)))) (call $nodetype (local.get $a)))
              (then (call $refuse (select (global.get $R_key_branch_body_type) (global.get $R_branch_body_type)
                                          (call $w (i32.add (local.get $a) (i32.const 5)))))))
            (br $task))
            ;; DEFAULT(case=a, depth=b)
            (local.set $x (call $w (i32.add (local.get $a) (i32.sub (call $w (local.get $a)) (i32.const 1)))))
            (call $push (i32.const 7) (local.get $a) (local.get $x) (i32.const 0))
            (call $push (i32.const 1) (call $w (i32.add (local.get $x) (i32.const 3))) (local.get $b) (i32.const 0))
            (br $task))
            ;; DEFPOST(case=a, default=b)
            (if (i32.ne (call $nodetype (call $w (i32.add (local.get $b) (i32.const 3)))) (call $nodetype (local.get $a)))
              (then (call $refuse (global.get $R_default_body_type))))
            (br $task))
            ;; CLOSE(closure=a, base=b, deepest=c): every capture used, exact
            ;; slots, a fitting body
            (local.set $cnt (call $w (i32.add (local.get $a) (i32.const 6))))
            (local.set $j (i32.const 0))
            (block $caps
              (loop $each
                (br_if $caps (i32.ge_u (local.get $j) (local.get $cnt)))
                (if (i32.eqz (i32.load8_u (i32.add (global.get $us) (i32.add (global.get $vbase) (local.get $j)))))
                  (then (call $refuse (global.get $R_capture_use))))
                (local.set $j (i32.add (local.get $j) (i32.const 1)))
                (br $each)))
            (if (i32.ne (global.get $vdeep) (call $w (i32.add (local.get $a) (i32.const 5))))
              (then (call $refuse (global.get $R_closure_slots))))
            (local.set $x (call $w (i32.add (local.get $a) (i32.sub (call $w (local.get $a)) (i32.const 1)))))
            (if (i32.eqz (call $fits (call $ty (call $nodetype (local.get $a)) (i32.const 3)) (call $nodetype (local.get $x))))
              (then (call $refuse (global.get $R_closure_result_type))))
            (global.set $vbase (local.get $b))
            (global.set $vdeep (local.get $c))
            (br $task))
          ;; END(function=a): exact slots, a fitting body
          (if (i32.ne (global.get $vdeep) (call $w (i32.add (local.get $a) (i32.const 4))))
            (then (call $refuse (global.get $R_function_slots))))
          (if (i32.eqz (call $fits (call $w (i32.add (local.get $a) (i32.const 2)))
                                   (call $nodetype (call $w (i32.add (local.get $a) (i32.const 5))))))
            (then (call $refuse (global.get $R_body_type)))))
        (br $next))))

  ;; the rules a gathering node or Let or Invoke checks after its operands
  (func $post (param $a i32)
    (local $op i32) (local $t i32) (local $cnt i32) (local $j i32) (local $rec i32) (local $nf i32)
    (local $id i32) (local $row i32) (local $f i32) (local $kd i32) (local $r i32)
    (local.set $op (call $w (i32.add (local.get $a) (i32.const 1))))
    (local.set $t (call $nodetype (local.get $a)))
    (local.set $cnt (call $w (i32.add (local.get $a) (i32.const 4))))
    (block $done
      (block $invoke (block $let (block $foreign (block $prim (block $call (block $con (block $zero
        (br_table $zero $prim $zero $zero $con $zero $call $let $zero $zero $zero $invoke $foreign (local.get $op)))
        (call $internal))
        ;; Construct: a fielded constructor, its exact arity, fitting fields
        (local.set $id (call $w (i32.add (local.get $a) (i32.const 3))))
        (if (call $kind (local.get $t)) (then (call $refuse (global.get $R_construct_tag))))
        (if (i32.ge_u (local.get $id) (call $ty (local.get $t) (i32.const 3))) (then (call $refuse (global.get $R_construct_tag))))
        (local.set $rec (call $ctorv (local.get $t) (local.get $id)))
        (local.set $nf (call $w (i32.add (local.get $rec) (i32.const 4))))
        (if (i32.or (i32.eqz (local.get $nf)) (i32.ne (local.get $nf) (local.get $cnt)))
          (then (call $refuse (global.get $R_construct_arity))))
        (local.set $j (i32.const 0))
        (block $fields
          (loop $field
            (br_if $fields (i32.ge_u (local.get $j) (local.get $cnt)))
            (if (i32.eqz (call $fits (call $w (i32.add (i32.add (local.get $rec) (i32.const 5)) (local.get $j)))
                                     (call $nodetype (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j))))))
              (then (call $refuse (global.get $R_construct_field_type))))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $field)))
        (br $done))
        ;; Application: the callee's exact live arity and fitting types
        (local.set $id (call $w (i32.add (local.get $a) (i32.const 3))))
        (if (i32.ge_u (local.get $id) (global.get $nF)) (then (call $refuse (global.get $R_function_index))))
        (local.set $f (call $tab (global.get $tF) (local.get $id)))
        (if (i32.ne (local.get $cnt) (call $w (i32.add (local.get $f) (i32.const 3))))
          (then (call $refuse (global.get $R_call_arity))))
        (if (i32.eqz (call $fits (call $w (i32.add (local.get $f) (i32.const 2))) (local.get $t)))
          (then (call $refuse (global.get $R_call_types))))
        (local.set $j (i32.const 0))
        (block $args
          (loop $arg
            (br_if $args (i32.ge_u (local.get $j) (local.get $cnt)))
            (if (i32.eqz (call $fits (call $w (i32.add (i32.add (local.get $f) (i32.const 6)) (local.get $j)))
                                     (call $nodetype (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j))))))
              (then (call $refuse (global.get $R_call_types))))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $arg)))
        (br $done))
        ;; Intrinsic: a registered prim at its pinned representations
        (local.set $id (call $w (i32.add (local.get $a) (i32.const 3))))
        (if (i32.ge_u (local.get $id) (i32.const 41)) (then (call $refuse (global.get $R_unknown_prim))))
        (local.set $row (i32.add (i32.const 3712) (i32.shl (local.get $id) (i32.const 2))))
        (if (i32.eq (i32.load8_u (local.get $row)) (i32.const 0xff)) (then (call $refuse (global.get $R_unknown_prim))))
        (if (i32.ne (i32.load8_u (local.get $row)) (local.get $cnt)) (then (call $refuse (global.get $R_prim_arity))))
        (call $operands (local.get $a) (local.get $row) (local.get $cnt) (global.get $R_prim_operand))
        (local.set $r (call $rep (i32.load8_u offset=3 (local.get $row))))
        (if (i32.or (i32.eq (local.get $r) (i32.const -1)) (i32.ne (local.get $t) (local.get $r)))
          (then (call $refuse (global.get $R_prim_result))))
        (br $done))
        ;; Foreign: a registered leaf returning IO of its output
        (local.set $id (call $w (i32.add (local.get $a) (i32.const 3))))
        (if (i32.ge_u (local.get $id) (i32.const 8)) (then (call $refuse (global.get $R_unknown_foreign))))
        (local.set $row (i32.add (i32.const 3880) (i32.shl (local.get $id) (i32.const 2))))
        (if (i32.ne (i32.load8_u (local.get $row)) (local.get $cnt)) (then (call $refuse (global.get $R_foreign_arity))))
        (call $operands (local.get $a) (local.get $row) (local.get $cnt) (global.get $R_foreign_operand))
        (if (i32.eqz (call $io (local.get $t) (call $rep (i32.load8_u offset=3 (local.get $row)))))
          (then (call $refuse (global.get $R_foreign_result))))
        (br $done))
        ;; Let: the body carries the Let's type
        (if (i32.ne (call $nodetype (call $w (i32.add (local.get $a) (i32.const 5)))) (local.get $t))
          (then (call $refuse (global.get $R_let_body_type))))
        (br $done))
      ;; Invoke: an arrow applied to exactly its live argument count
      (local.set $f (call $nodetype (call $w (i32.add (local.get $a) (i32.const 3)))))
      (local.set $kd (call $kind (local.get $f)))
      (if (i32.or (i32.or (i32.eqz (local.get $kd)) (i32.ge_u (local.get $kd) (i32.const 3)))
                  (i32.ne (local.get $cnt) (i32.eq (local.get $kd) (i32.const 1))))
        (then (call $refuse (global.get $R_invoke_arity))))
      (if (i32.eqz (call $fits (call $ty (local.get $f) (i32.const 3)) (local.get $t)))
        (then (call $refuse (global.get $R_invoke_types))))
      (if (local.get $cnt)
        (then (if (i32.eqz (call $fits (call $ty (local.get $f) (i32.const 2))
                                       (call $nodetype (call $w (i32.add (local.get $a) (i32.const 5))))))
                (then (call $refuse (global.get $R_invoke_types))))))))

  ;; each operand of a prim or foreign node has its pinned representation
  (func $operands (param $a i32) (param $row i32) (param $cnt i32) (param $code i32)
    (local $j i32) (local $r i32)
    (block $done
      (loop $each
        (br_if $done (i32.ge_u (local.get $j) (local.get $cnt)))
        (local.set $r (call $rep (i32.load8_u (i32.add (i32.add (local.get $row) (i32.const 1)) (local.get $j)))))
        (if (i32.or (i32.eq (local.get $r) (i32.const -1))
                    (i32.ne (call $nodetype (call $w (i32.add (i32.add (local.get $a) (i32.const 5)) (local.get $j))))
                            (local.get $r)))
          (then (call $refuse (local.get $code))))
        (local.set $j (i32.add (local.get $j) (i32.const 1)))
        (br $each))))

  ;; ---------------------------------------------------------------- canonical form (§4 step 5)
  ;; Beyond the walk's order checks: names interned in first-use order over
  ;; types, constructors and functions; the constructor table in type order;
  ;; constants all used and distinct; main in the header.
  (func $canonical
    (local $next i32) (local $i i32) (local $at i32) (local $x i32) (local $main i32)
    (if (i32.ne (global.get $nextConst) (global.get $nK)) (then (global.set $noncanon (i32.const 1))))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nT)))
        (if (i32.or (i32.eqz (call $kind (local.get $i))) (i32.eq (call $kind (local.get $i)) (i32.const 3)))
          (then (local.set $next (call $intern (call $ty (local.get $i) (i32.const 1)) (local.get $next)))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (local.set $at (i32.add (global.get $sC) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nC)))
        (if (i32.ne (call $tab (global.get $tC) (local.get $i)) (local.get $at)) (then (global.set $noncanon (i32.const 1))))
        (local.set $next (call $intern (call $w (i32.add (local.get $at) (i32.const 3))) (local.get $next)))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (local.set $main (i32.const -1))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nF)))
        (local.set $at (call $tab (global.get $tF) (local.get $i)))
        (local.set $next (call $intern (call $w (i32.add (local.get $at) (i32.const 1))) (local.get $next)))
        (if (i32.and (i32.eq (local.get $main) (i32.const -1)) (call $is_main (local.get $at)))
          (then (local.set $main (local.get $i))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (if (i32.ne (local.get $next) (global.get $nM)) (then (global.set $noncanon (i32.const 1))))
    (if (i32.ne (call $w (i32.const 4)) (local.get $main)) (then (global.set $noncanon (i32.const 1))))
    (if (call $duplicate (global.get $tK) (global.get $nK)) (then (global.set $noncanon (i32.const 1))))
    (if (global.get $noncanon) (then (call $refuse (global.get $R_noncanonical)))))

  ;; first-use interning: an index is either seen already or the next one
  (func $intern (param $name i32) (param $next i32) (result i32)
    (if (i32.gt_u (local.get $name) (local.get $next)) (then (global.set $noncanon (i32.const 1))))
    (i32.add (local.get $next) (i32.eq (local.get $name) (local.get $next))))

  ;; ---------------------------------------------------------------- words and cells (§5)
  ;; vm-rc gives these their counting; here they mark the spec's substeps.
  (func $dup (param $x i32))
  (func $drop (param $x i32))

  (func $wset (param $i i32) (param $v i32)
    (i32.store offset=4096 (i32.shl (local.get $i) (i32.const 2)) (local.get $v)))

  ;; A cell of 2 + payload words takes the smallest power of two not below
  ;; max(4, 2 + payload) words, from the bump pointer, zeroed, rc = 1.
  (func $alloc (param $payload i32) (param $class i32) (result i32)
    (local $words i32) (local $bytes i32) (local $p i32) (local $end i64)
    (local.set $words (i32.add (local.get $payload) (i32.const 2)))
    (local.set $bytes (if (result i32) (i32.le_u (local.get $words) (i32.const 4))
      (then (i32.const 16))
      (else (i32.shl (i32.const 4) (i32.sub (i32.const 32) (i32.clz (i32.sub (local.get $words) (i32.const 1))))))))
    (local.set $p (global.get $bump))
    (local.set $end (i64.add (i64.extend_i32_u (local.get $p)) (i64.extend_i32_u (local.get $bytes))))
    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))
    ;; a cell ending exactly at 4 GiB would wrap the bump pointer; no host grows that far
    (if (i64.ge_u (local.get $end) (i64.const 0x100000000)) (then unreachable))
    (if (i64.gt_u (local.get $end) (i64.shl (i64.extend_i32_u (memory.size)) (i64.const 16)))
      (then (call $grow (local.get $end))))
    (memory.fill (local.get $p) (i32.const 0) (local.get $bytes))
    (i32.store (local.get $p) (i32.const 1))
    (i32.store offset=4 (local.get $p) (i32.or (i32.shl (local.get $payload) (i32.const 3)) (local.get $class)))
    (global.set $bump (i32.wrap_i64 (local.get $end)))
    (local.get $p))

  ;; canonical boxing: below 2^31 immediate, else a Big cell
  (func $scalar (param $v i32) (result i32)
    (local $c i32)
    (if (i32.ge_u (local.get $v) (i32.const 0x80000000))
      (then
        (local.set $c (call $alloc (i32.const 1) (i32.const 2)))
        (i32.store offset=8 (local.get $c) (local.get $v))
        (return (local.get $c))))
    (i32.or (i32.shl (local.get $v) (i32.const 1)) (i32.const 1)))

  ;; §6 inspection of a word read at U32, Nat or Char: immediate or Big
  (func $num (param $x i32) (result i32)
    (if (i32.and (local.get $x) (i32.const 1)) (then (return (i32.shr_u (local.get $x) (i32.const 1)))))
    (if (i32.eqz (local.get $x)) (then (call $internal)))
    (if (i32.ne (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7)) (i32.const 2))
      (then (call $refuse (global.get $R_ill_typed))))
    (i32.load offset=8 (local.get $x)))

  ;; the linked constructor record of (t, tag): walk from the type's first
  (func $ctor (param $t i32) (param $tag i32) (result i32)
    (local $rec i32)
    (local.set $rec (call $ty (local.get $t) (i32.const 2)))
    (block $done
      (loop $next
        (br_if $done (i32.eqz (local.get $tag)))
        (local.set $rec (i32.add (local.get $rec) (call $w (local.get $rec))))
        (local.set $tag (i32.sub (local.get $tag) (i32.const 1)))
        (br $next)))
    (local.get $rec))

  ;; §6 inspection at an algebraic type t: the tag of an immediate naming a
  ;; nullary constructor, or of an Object of type t
  (func $tagof (param $x i32) (param $t i32) (result i32)
    (local $tag i32)
    (if (i32.and (local.get $x) (i32.const 1))
      (then
        (local.set $tag (i32.shr_u (local.get $x) (i32.const 1)))
        (if (i32.ge_u (local.get $tag) (call $ty (local.get $t) (i32.const 3)))
          (then (call $refuse (global.get $R_ill_typed))))
        (if (call $w (i32.add (call $ctor (local.get $t) (local.get $tag)) (i32.const 4)))
          (then (call $refuse (global.get $R_ill_typed))))
        (return (local.get $tag))))
    (if (i32.eqz (local.get $x)) (then (call $internal)))
    (if (i32.or (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7))
                (i32.ne (i32.load offset=8 (local.get $x)) (local.get $t)))
      (then (call $refuse (global.get $R_ill_typed))))
    (i32.load offset=12 (local.get $x)))

  ;; ---------------------------------------------------------------- strings (§9)
  ;; A String prim first inspects every cell it walks: SNil is the immediate
  ;; of tag 0, SCon an Object of the pinned String with a Char head.
  (func $slen (param $s i32) (result i32)
    (local $n i32)
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $s) (i32.const 1)))
        (if (i32.eqz (local.get $s)) (then (call $internal)))
        (if (i32.or (i32.and (local.get $s) (i32.const 1))
              (i32.or (i32.and (i32.load offset=4 (local.get $s)) (i32.const 7))
                (i32.or (i32.ne (i32.load offset=8 (local.get $s)) (global.get $rString))
                        (i32.ne (i32.load offset=12 (local.get $s)) (i32.const 1)))))
          (then (call $refuse (global.get $R_ill_typed))))
        (drop (call $num (i32.load offset=16 (local.get $s))))
        (local.set $n (i32.add (local.get $n) (i32.const 1)))
        (local.set $s (i32.load offset=20 (local.get $s)))
        (br $next)))
    (local.get $n))

  (func $scon (param $chr i32) (param $tail i32) (result i32)
    (local $c i32)
    (local.set $c (call $alloc (i32.const 4) (i32.const 0)))
    (i32.store offset=8 (local.get $c) (global.get $rString))
    (i32.store offset=12 (local.get $c) (i32.const 1))
    (i32.store offset=16 (local.get $c) (local.get $chr))
    (i32.store offset=20 (local.get $c) (local.get $tail))
    (local.get $c))

  ;; unsigned decimal, allocated from its last digit
  (func $show (param $v i32) (result i32)
    (local $s i32)
    (local.set $s (i32.const 1))
    (loop $digit
      (local.set $s (call $scon (i32.or (i32.shl (i32.add (i32.const 48) (i32.rem_u (local.get $v) (i32.const 10)))
                                                 (i32.const 1)) (i32.const 1))
                                (local.get $s)))
      (local.set $v (i32.div_u (local.get $v) (i32.const 10)))
      (br_if $digit (local.get $v)))
    (local.get $s))

  (func $seq (param $a i32) (param $b i32) (result i32)
    (if (i32.ne (call $slen (local.get $a)) (call $slen (local.get $b))) (then (return (i32.const 1))))
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $a) (i32.const 1)))
        (if (i32.ne (call $num (i32.load offset=16 (local.get $a))) (call $num (i32.load offset=16 (local.get $b))))
          (then (return (i32.const 1))))
        (local.set $a (i32.load offset=20 (local.get $a)))
        (local.set $b (i32.load offset=20 (local.get $b)))
        (br $next)))
    (i32.const 3))

  ;; append(a, b) copies a's cells onto the moved b from a's last character to
  ;; its first. On the bump arena those L cells are one block whose i-th
  ;; character sits (L-1-i) cells up, so one forward walk writes them.
  (func $append (param $a i32) (param $b i32) (result i32)
    (local $n i32) (local $base i32) (local $end i64) (local $c i32)
    (local.set $n (call $slen (local.get $a)))
    (if (i32.eqz (local.get $n)) (then (return (local.get $b))))
    (local.set $base (global.get $bump))
    (local.set $end (i64.add (i64.extend_i32_u (local.get $base)) (i64.shl (i64.extend_i32_u (local.get $n)) (i64.const 5))))
    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))
    (if (i64.ge_u (local.get $end) (i64.const 0x100000000)) (then unreachable))
    (call $grow (local.get $end))
    (memory.fill (local.get $base) (i32.const 0) (i32.shl (local.get $n) (i32.const 5)))
    (local.set $c (i32.add (local.get $base) (i32.shl (i32.sub (local.get $n) (i32.const 1)) (i32.const 5))))
    (block $done
      (loop $next
        (i32.store (local.get $c) (i32.const 1))
        (i32.store offset=4 (local.get $c) (i32.const 32))
        (i32.store offset=8 (local.get $c) (global.get $rString))
        (i32.store offset=12 (local.get $c) (i32.const 1))
        (call $dup (i32.load offset=16 (local.get $a)))
        (i32.store offset=16 (local.get $c) (i32.load offset=16 (local.get $a)))
        (local.set $a (i32.load offset=20 (local.get $a)))
        (if (i32.eq (local.get $c) (local.get $base))
          (then (i32.store offset=20 (local.get $c) (local.get $b)) (br $done)))
        (i32.store offset=20 (local.get $c) (i32.sub (local.get $c) (i32.const 32)))
        (local.set $c (i32.sub (local.get $c) (i32.const 32)))
        (br $next)))
    (global.set $bump (i32.wrap_i64 (local.get $end)))
    (i32.add (local.get $base) (i32.shl (i32.sub (local.get $n) (i32.const 1)) (i32.const 5))))

  ;; reverse(a) allocates from a's first character
  (func $reverse (param $a i32) (result i32)
    (local $s i32)
    (drop (call $slen (local.get $a)))
    (local.set $s (i32.const 1))
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $a) (i32.const 1)))
        (call $dup (i32.load offset=16 (local.get $a)))
        (local.set $s (call $scon (i32.load offset=16 (local.get $a)) (local.get $s)))
        (local.set $a (i32.load offset=20 (local.get $a)))
        (br $next)))
    (local.get $s))

  ;; is_empty reads only the head cell
  (func $sempty (param $a i32) (result i32)
    (if (i32.eq (local.get $a) (i32.const 1)) (then (return (i32.const 3))))
    (if (i32.eqz (local.get $a)) (then (call $internal)))
    (if (i32.or (i32.and (local.get $a) (i32.const 1))
          (i32.or (i32.and (i32.load offset=4 (local.get $a)) (i32.const 7))
            (i32.or (i32.ne (i32.load offset=8 (local.get $a)) (global.get $rString))
                    (i32.ne (i32.load offset=12 (local.get $a)) (i32.const 1)))))
      (then (call $refuse (global.get $R_ill_typed))))
    (i32.const 1))

  ;; ---------------------------------------------------------------- prims (§9)
  ;; Words for Bool (False 0, True 1) and Cmp (LT 0, EQ 1, GT 2) are immediates.
  (func $bool (param $c i32) (result i32)
    (i32.or (i32.shl (local.get $c) (i32.const 1)) (i32.const 1)))
  (func $cmp (param $x i32) (param $y i32) (result i32)
    (call $bool (i32.add (i32.gt_u (local.get $x) (local.get $y)) (i32.ge_u (local.get $x) (local.get $y)))))
  (func $nat (param $p i64) (result i32)
    (if (i64.gt_u (local.get $p) (i64.const 0xffffffff)) (then (call $exhaust (i32.const 2) (global.get $R_nat_range))))
    (call $scalar (i32.wrap_i64 (local.get $p))))

  ;; the prim's result from its gathered operands; scalar operands are
  ;; inspected in operand order before anything is allocated
  (func $prim (param $id i32) (param $ops i32) (param $n i32) (result i32)
    (local $a i32) (local $b i32) (local $x i32) (local $y i32)
    (local.set $a (i32.load (local.get $ops)))
    (if (i32.eq (local.get $n) (i32.const 2)) (then (local.set $b (i32.load offset=4 (local.get $ops)))))
    (if (i32.lt_u (local.get $id) (i32.const 34))
      (then
        (local.set $x (call $num (local.get $a)))
        (if (i32.eq (local.get $n) (i32.const 2)) (then (local.set $y (call $num (local.get $b)))))))
    (block $bad
      (block $empty (block $length (block $reverse (block $append (block $seq (block $show
      (block $nge (block $ngt (block $nle (block $nlt (block $nne (block $neq (block $ncmp (block $nmul (block $nsub (block $nadd
      (block $space (block $ceq (block $move (block $shr (block $shl
      (block $ge (block $gt (block $le (block $lt (block $ne (block $eq (block $wcmp (block $and (block $not
      (block $mod (block $div (block $mul (block $sub (block $add
        (br_table $add $sub $mul $div $mod $not $and $wcmp $eq $ne $lt $le $gt $ge $shl $shr
                  $move $move $move $move $ceq $space $nadd $nsub $nmul $ncmp $neq $nne $nlt $nle $ngt $nge
                  $show $show $seq $append $reverse $length $empty $bad (local.get $id)))
        (return (call $scalar (i32.add (local.get $x) (local.get $y)))))
        (return (call $scalar (i32.sub (local.get $x) (local.get $y)))))
        (return (call $scalar (i32.mul (local.get $x) (local.get $y)))))
        (return (call $scalar (if (result i32) (local.get $y) (then (i32.div_u (local.get $x) (local.get $y))) (else (i32.const 0))))))
        (return (call $scalar (if (result i32) (local.get $y) (then (i32.rem_u (local.get $x) (local.get $y))) (else (local.get $x))))))
        (return (call $scalar (i32.xor (local.get $x) (i32.const -1)))))
        (return (call $scalar (i32.and (local.get $x) (local.get $y)))))
        (return (call $cmp (local.get $x) (local.get $y))))
        (return (call $bool (i32.eq (local.get $x) (local.get $y)))))
        (return (call $bool (i32.ne (local.get $x) (local.get $y)))))
        (return (call $bool (i32.lt_u (local.get $x) (local.get $y)))))
        (return (call $bool (i32.le_u (local.get $x) (local.get $y)))))
        (return (call $bool (i32.gt_u (local.get $x) (local.get $y)))))
        (return (call $bool (i32.ge_u (local.get $x) (local.get $y)))))
        (return (call $scalar (if (result i32) (i32.ge_u (local.get $y) (i32.const 32)) (then (i32.const 0))
                                  (else (i32.shl (local.get $x) (local.get $y)))))))
        (return (call $scalar (if (result i32) (i32.ge_u (local.get $y) (i32.const 32)) (then (i32.const 0))
                                  (else (i32.shr_u (local.get $x) (local.get $y)))))))
        ;; to_nat, from_nat, from_u32, to_u32 move their word (§9 ownership)
        (return (local.get $a)))
        (return (call $bool (i32.eq (local.get $x) (local.get $y)))))
        (return (call $bool (i32.or (i32.le_u (i32.sub (local.get $x) (i32.const 9)) (i32.const 4))
                                    (i32.eq (local.get $x) (i32.const 32))))))
        (return (call $nat (i64.add (i64.extend_i32_u (local.get $x)) (i64.extend_i32_u (local.get $y))))))
        (return (call $scalar (select (i32.sub (local.get $x) (local.get $y)) (i32.const 0)
                                      (i32.gt_u (local.get $x) (local.get $y))))))
        (return (call $nat (i64.mul (i64.extend_i32_u (local.get $x)) (i64.extend_i32_u (local.get $y))))))
        (return (call $cmp (local.get $x) (local.get $y))))
        (return (call $bool (i32.eq (local.get $x) (local.get $y)))))
        (return (call $bool (i32.ne (local.get $x) (local.get $y)))))
        (return (call $bool (i32.lt_u (local.get $x) (local.get $y)))))
        (return (call $bool (i32.le_u (local.get $x) (local.get $y)))))
        (return (call $bool (i32.gt_u (local.get $x) (local.get $y)))))
        (return (call $bool (i32.ge_u (local.get $x) (local.get $y)))))
        (return (call $show (local.get $x))))
        (return (call $seq (local.get $a) (local.get $b))))
        (return (call $append (local.get $a) (local.get $b))))
        (return (call $reverse (local.get $a))))
        (return (call $nat (i64.extend_i32_u (call $slen (local.get $a))))))
        (return (call $sempty (local.get $a))))
    (call $internal)
    (i32.const 0))

  ;; ---------------------------------------------------------------- frames (§6)
  ;; A record is [value[n], node, aux, head] with head = kind | n << 4 on top.
  ;; Returns the address of value[0], zeroed.
  (func $frame (param $kind i32) (param $node i32) (param $aux i32) (param $n i32) (result i32)
    (local $p i32) (local $v i32)
    (local.set $v (global.get $top))
    (local.set $p (i32.add (local.get $v) (i32.shl (local.get $n) (i32.const 2))))
    (if (i32.gt_u (i32.add (local.get $p) (i32.const 12)) (global.get $FL))
      (then (call $exhaust (i32.const 3) (global.get $R_frames))))
    (memory.fill (local.get $v) (i32.const 0) (i32.shl (local.get $n) (i32.const 2)))
    (i32.store (local.get $p) (local.get $node))
    (i32.store offset=4 (local.get $p) (local.get $aux))
    (i32.store offset=8 (local.get $p) (i32.or (local.get $kind) (i32.shl (local.get $n) (i32.const 4))))
    (global.set $top (i32.add (local.get $p) (i32.const 12)))
    (local.get $v))

  ;; §6.2: a tail entry has only Scope frames between the top and the nearest
  ;; Call or Top; it pops them and releases the caller. Otherwise the Call
  ;; frame's room is checked now, before the callee is allocated.
  (func $tail (result i32)
    (local $p i32) (local $k i32)
    (local.set $p (global.get $top))
    (loop $scan
      (local.set $k (i32.and (i32.load (i32.sub (local.get $p) (i32.const 4))) (i32.const 15)))
      (if (i32.eq (local.get $k) (i32.const 3))
        (then (local.set $p (i32.sub (local.get $p) (i32.const 12))) (br $scan))))
    (if (i32.or (i32.eqz (local.get $k)) (i32.eq (local.get $k) (i32.const 4)))
      (then
        (global.set $top (local.get $p))
        (call $drop (global.get $act))
        (return (i32.const 1))))
    (if (i32.gt_u (i32.add (global.get $top) (i32.const 16)) (global.get $FL))
      (then (call $exhaust (i32.const 3) (global.get $R_frames))))
    (i32.const 0))

  ;; §7 fuel: one unit per entry, checked with the Enter still pending
  (func $debit
    (if (i32.eqz (global.get $fuel)) (then (call $exhaust (i32.const 1) (global.get $R_fuel))))
    (global.set $fuel (i32.sub (global.get $fuel) (i32.const 1)))
    (global.set $calls (i32.add (global.get $calls) (i32.const 1)))
    (global.set $quantum (i32.add (global.get $quantum) (i32.const 1))))

  ;; §7 step 3 after the body's slots are filled: a non-tail entry saves the
  ;; caller in a Call frame; the Activation becomes current.
  (func $activate (param $a i32) (param $tail i32)
    (if (i32.eqz (local.get $tail))
      (then (i32.store (call $frame (i32.const 4) (i32.const 0) (i32.const 0) (i32.const 1)) (global.get $act))))
    (global.set $act (local.get $a)))

  ;; §6 completing a gathered node whose n operands start at `ops`
  (func $complete (param $n i32) (param $ops i32) (param $cnt i32)
    (local $op i32) (local $t i32) (local $c i32) (local $j i32) (local $id i32) (local $v i32)
    (local.set $op (call $w (i32.add (local.get $n) (i32.const 1))))
    (if (i32.eq (local.get $op) (i32.const 6))
      (then
        (global.set $tgt (call $w (i32.add (local.get $n) (i32.const 3))))
        (global.set $tfn (i32.const 1))
        (global.set $ops (local.get $ops))
        (global.set $nops (local.get $cnt))
        (global.set $mode (i32.const 2))
        (return)))
    (if (i32.eq (local.get $op) (i32.const 1))
      (then
        (local.set $id (call $w (i32.add (local.get $n) (i32.const 3))))
        (global.set $val (call $prim (local.get $id) (local.get $ops) (local.get $cnt)))
        (if (i32.or (i32.lt_u (local.get $id) (i32.const 16)) (i32.gt_u (local.get $id) (i32.const 19)))
          (then
            (call $drop (i32.load (local.get $ops)))
            (if (i32.and (i32.eq (local.get $cnt) (i32.const 2)) (i32.ne (local.get $id) (i32.const 35)))
              (then (call $drop (i32.load offset=4 (local.get $ops)))))))
        (global.set $mode (i32.const 1))
        (return)))
    (local.set $t (call $nodetype (local.get $n)))
    (if (i32.eq (local.get $op) (i32.const 4))
      (then
        ;; Nat's Succ and Char's Chr act on words
        (if (i32.eq (local.get $t) (global.get $rNat))
          (then
            (local.set $v (call $num (i32.load (local.get $ops))))
            (if (i32.eq (local.get $v) (i32.const -1)) (then (call $exhaust (i32.const 2) (global.get $R_nat_range))))
            (global.set $val (call $scalar (i32.add (local.get $v) (i32.const 1))))
            (call $drop (i32.load (local.get $ops)))
            (global.set $mode (i32.const 1))
            (return)))
        (if (i32.eq (local.get $t) (global.get $rChar))
          (then (global.set $val (i32.load (local.get $ops))) (global.set $mode (i32.const 1)) (return)))
        (local.set $c (call $alloc (i32.add (local.get $cnt) (i32.const 2)) (i32.const 0)))
        (i32.store offset=8 (local.get $c) (local.get $t))
        (i32.store offset=12 (local.get $c) (call $w (i32.add (local.get $n) (i32.const 3))))
        (memory.copy (i32.add (local.get $c) (i32.const 16)) (local.get $ops) (i32.shl (local.get $cnt) (i32.const 2)))
        (global.set $val (local.get $c))
        (global.set $mode (i32.const 1))
        (return)))
    ;; Foreign: an inert Action holding its operands (§8)
    (local.set $c (call $alloc (i32.add (local.get $cnt) (i32.const 1)) (i32.const 3)))
    (i32.store offset=8 (local.get $c) (call $w (i32.add (local.get $n) (i32.const 3))))
    (memory.copy (i32.add (local.get $c) (i32.const 12)) (local.get $ops) (i32.shl (local.get $cnt) (i32.const 2)))
    (global.set $val (local.get $c))
    (global.set $mode (i32.const 1)))

  ;; ---------------------------------------------------------------- Case (§6.1)
  (func $select (param $n i32)
    (local $s i32) (local $scr i32) (local $cnt i32) (local $x i32) (local $v i32) (local $tag i32)
    (local $fields i32) (local $arm i32) (local $f i32) (local $d i32) (local $lo i32) (local $hi i32)
    (local $mid i32) (local $key i32) (local $j i32) (local $w i32) (local $imm i32)
    (local.set $s (call $w (i32.add (local.get $n) (i32.const 3))))
    (local.set $scr (call $w (i32.add (local.get $n) (i32.const 4))))
    (local.set $cnt (call $w (i32.add (local.get $n) (i32.const 6))))
    (local.set $x (i32.load offset=16 (i32.add (global.get $act) (i32.shl (local.get $s) (i32.const 2)))))
    (global.set $mode (i32.const 0))
    (if (call $w (i32.add (local.get $n) (i32.const 5)))
      (then
        ;; keys: binary search over strictly increasing keys, else the default
        (local.set $v (call $num (local.get $x)))
        (local.set $hi (local.get $cnt))
        (block $miss
          (loop $half
            (br_if $miss (i32.ge_u (local.get $lo) (local.get $hi)))
            (local.set $mid (i32.shr_u (i32.add (local.get $lo) (local.get $hi)) (i32.const 1)))
            (local.set $key (call $w (i32.add (i32.add (local.get $n) (i32.const 7)) (i32.shl (local.get $mid) (i32.const 1)))))
            (if (i32.eq (local.get $key) (local.get $v))
              (then
                (local.set $arm (call $w (i32.add (i32.add (local.get $n) (i32.const 8)) (i32.shl (local.get $mid) (i32.const 1)))))
                (global.set $node (call $w (i32.add (local.get $arm) (i32.const 6))))
                (return)))
            (if (i32.lt_u (local.get $key) (local.get $v))
              (then (local.set $lo (i32.add (local.get $mid) (i32.const 1))))
              (else (local.set $hi (local.get $mid))))
            (br $half)))
        (global.set $node (call $w (i32.add (call $w (i32.add (local.get $n) (i32.sub (call $w (local.get $n)) (i32.const 1))))
                                            (i32.const 3))))
        (return)))
    ;; tags: Nat's logical view, Char's Chr, or an algebraic word
    (if (i32.eq (local.get $scr) (global.get $rNat))
      (then (local.set $v (call $num (local.get $x))) (local.set $tag (i32.ne (local.get $v) (i32.const 0))))
      (else (if (i32.eq (local.get $scr) (global.get $rChar))
        (then (drop (call $num (local.get $x))))
        (else
          (if (i32.and (local.get $x) (i32.const 1))
            (then (local.set $imm (i32.const 1)) (local.set $tag (i32.shr_u (local.get $x) (i32.const 1))))
            (else
              (if (i32.eqz (local.get $x)) (then (call $internal)))
              (if (i32.or (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7))
                          (i32.ne (i32.load offset=8 (local.get $x)) (local.get $scr)))
                (then (call $refuse (global.get $R_ill_typed))))
              (local.set $tag (i32.load offset=12 (local.get $x)))
              (local.set $fields (i32.add (local.get $x) (i32.const 16)))))))))
    (if (i32.ge_u (local.get $tag) (local.get $cnt)) (then (call $refuse (global.get $R_ill_typed))))
    (local.set $arm (call $w (i32.add (i32.add (local.get $n) (i32.const 7)) (local.get $tag))))
    (if (local.get $imm)
      (then (if (if (result i32) (i32.eq (local.get $arm) (i32.const -1))
                  (then (call $w (i32.add (call $ctor (local.get $scr) (local.get $tag)) (i32.const 4))))
                  (else (call $w (i32.add (local.get $arm) (i32.const 5)))))
              (then (call $refuse (global.get $R_ill_typed))))))
    (if (i32.eq (local.get $arm) (i32.const -1))
      (then
        (global.set $node (call $w (i32.add (call $w (i32.add (local.get $n) (i32.sub (call $w (local.get $n)) (i32.const 1))))
                                            (i32.const 3))))
        (return)))
    (local.set $f (call $w (i32.add (local.get $arm) (i32.const 5))))
    (if (local.get $f)
      (then
        ;; Nat's field is the new word n - 1; Char's is its own code word
        (if (i32.eq (local.get $scr) (global.get $rNat))
          (then (local.set $w (call $scalar (i32.sub (local.get $v) (i32.const 1))))))
        (if (i32.eq (local.get $scr) (global.get $rChar))
          (then (call $dup (local.get $x)) (local.set $w (local.get $x))))
        (local.set $d (i32.load offset=12 (global.get $act)))
        (drop (call $frame (i32.const 3) (i32.const 0) (local.get $d) (i32.const 0)))
        (if (local.get $fields)
          (then
            (block $bound
              (loop $bind
                (br_if $bound (i32.ge_u (local.get $j) (local.get $f)))
                (local.set $w (i32.load (i32.add (local.get $fields) (i32.shl (local.get $j) (i32.const 2)))))
                (call $dup (local.get $w))
                (i32.store offset=16 (i32.add (global.get $act) (i32.shl (i32.add (local.get $d) (local.get $j)) (i32.const 2)))
                           (local.get $w))
                (local.set $j (i32.add (local.get $j) (i32.const 1)))
                (br $bind))))
          (else
            (i32.store offset=16 (i32.add (global.get $act) (i32.shl (local.get $d) (i32.const 2))) (local.get $w))))
        (i32.store offset=12 (global.get $act) (i32.add (local.get $d) (local.get $f)))))
    (global.set $node (call $w (i32.add (local.get $arm) (i32.const 6)))))

  ;; ---------------------------------------------------------------- Enter (§7)
  ;; A body gets an Activation [owner, depth, slot[capacity]] after §6.2.
  (func $enter
    (local $f i32) (local $x i32) (local $cn i32) (local $live i32) (local $ncap i32) (local $tail i32)
    (local $a i32) (local $j i32) (local $v i32) (local $k i32) (local $r i32)
    (if (global.get $tfn)
      (then
        (local.set $f (global.get $tgt))
        (call $debit)
        (local.set $tail (call $tail))
        (local.set $a (call $alloc (i32.add (call $w (i32.add (local.get $f) (i32.const 4))) (i32.const 2)) (i32.const 4)))
        (i32.store offset=8 (local.get $a) (call $w (i32.add (local.get $f) (i32.const 5))))
        (i32.store offset=12 (local.get $a) (global.get $nops))
        (memory.copy (i32.add (local.get $a) (i32.const 16)) (global.get $ops) (i32.shl (global.get $nops) (i32.const 2)))
        (call $activate (local.get $a) (local.get $tail))
        (global.set $node (call $w (i32.add (local.get $f) (i32.const 5))))
        (global.set $mode (i32.const 0))
        (return)))
    (local.set $x (global.get $tgt))
    (if (i32.or (i32.and (local.get $x) (i32.const 1)) (i32.eqz (local.get $x)))
      (then (call $refuse (global.get $R_ill_typed))))
    (block $bad
      (block $action
        (block $closure
          (br_table $bad $closure $bad $action $bad
            (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7))))
        (local.set $cn (i32.load offset=8 (local.get $x)))
        (if (i32.eq (local.get $cn) (i32.const -1))
          (then
            ;; the terminal continuation: Emit{x} of the pinned IO.OP
            (br_if $bad (i32.ne (global.get $nops) (i32.const 1)))
            (call $debit)
            (local.set $a (call $alloc (i32.const 3) (i32.const 0)))
            (i32.store offset=8 (local.get $a) (global.get $rIoop))
            (i32.store offset=16 (local.get $a) (i32.load (global.get $ops)))
            (global.set $val (local.get $a))
            (global.set $mode (i32.const 1))
            (return)))
        (local.set $live (call $w (i32.add (local.get $cn) (i32.const 4))))
        (br_if $bad (i32.ne (global.get $nops) (local.get $live)))
        (call $debit)
        (local.set $ncap (call $w (i32.add (local.get $cn) (i32.const 6))))
        (local.set $tail (call $tail))
        (local.set $a (call $alloc (i32.add (call $w (i32.add (local.get $cn) (i32.const 5))) (i32.const 2)) (i32.const 4)))
        (i32.store offset=8 (local.get $a) (local.get $cn))
        (i32.store offset=12 (local.get $a) (i32.add (local.get $ncap) (local.get $live)))
        (block $copied
          (loop $capture
            (br_if $copied (i32.ge_u (local.get $j) (local.get $ncap)))
            (local.set $v (i32.load offset=12 (i32.add (local.get $x) (i32.shl (local.get $j) (i32.const 2)))))
            (call $dup (local.get $v))
            (i32.store offset=16 (i32.add (local.get $a) (i32.shl (local.get $j) (i32.const 2))) (local.get $v))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $capture)))
        (if (local.get $live)
          (then (i32.store offset=16 (i32.add (local.get $a) (i32.shl (local.get $ncap) (i32.const 2)))
                           (i32.load (global.get $ops)))))
        (call $drop (local.get $x))
        (call $activate (local.get $a) (local.get $tail))
        (global.set $node (call $w (i32.add (local.get $cn) (i32.sub (call $w (local.get $cn)) (i32.const 1)))))
        (global.set $mode (i32.const 0))
        (return))
      ;; an Action: its erased R returns it; its continuation performs it once
      (br_if $bad (i32.gt_u (global.get $nops) (i32.const 1)))
      (call $debit)
      (if (i32.eqz (global.get $nops))
        (then (global.set $val (local.get $x)) (global.set $mode (i32.const 1)) (return)))
      (local.set $k (i32.load (global.get $ops)))
      (local.set $r (call $perform (local.get $x)))
      (call $drop (local.get $x))
      (i32.store (i32.const 32) (local.get $r))
      (global.set $tgt (local.get $k))
      (global.set $ops (i32.const 32))
      (return))
    (call $refuse (global.get $R_ill_typed)))

  ;; §10, vm-core subset: IO.print. Other foreign ids are refused at load.
  (func $perform (param $x i32) (result i32)
    (local $n i32)
    (if (i32.ne (i32.load offset=8 (local.get $x)) (i32.const 1)) (then (call $internal)))
    (local.set $n (call $utf8out (i32.load offset=12 (local.get $x)) (call $align8 (global.get $bump))))
    (call $io_print (call $align8 (global.get $bump)) (local.get $n))
    (i32.const 1))

  ;; a String as canonical UTF-8 at `dst`; only Unicode scalars cross (§10)
  (func $utf8out (param $s i32) (param $dst i32) (result i32)
    (local $o i32) (local $c i32)
    (call $grow (i64.add (i64.extend_i32_u (local.get $dst))
                         (i64.shl (i64.extend_i32_u (call $slen (local.get $s))) (i64.const 2))))
    (local.set $o (local.get $dst))
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $s) (i32.const 1)))
        (local.set $c (call $num (i32.load offset=16 (local.get $s))))
        (if (i32.or (i32.gt_u (local.get $c) (i32.const 0x10ffff))
                    (i32.eq (i32.and (local.get $c) (i32.const 0xfffff800)) (i32.const 0xd800)))
          (then (call $stop (i32.const 3) (i32.const 5) (i32.const 320) (global.get $R_non_scalar))))
        (if (i32.lt_u (local.get $c) (i32.const 0x80))
          (then (i32.store8 (local.get $o) (local.get $c)) (local.set $o (i32.add (local.get $o) (i32.const 1))))
          (else (if (i32.lt_u (local.get $c) (i32.const 0x800))
            (then
              (i32.store8 (local.get $o) (i32.or (i32.const 0xc0) (i32.shr_u (local.get $c) (i32.const 6))))
              (i32.store8 offset=1 (local.get $o) (i32.or (i32.const 0x80) (i32.and (local.get $c) (i32.const 0x3f))))
              (local.set $o (i32.add (local.get $o) (i32.const 2))))
            (else (if (i32.lt_u (local.get $c) (i32.const 0x10000))
              (then
                (i32.store8 (local.get $o) (i32.or (i32.const 0xe0) (i32.shr_u (local.get $c) (i32.const 12))))
                (i32.store8 offset=1 (local.get $o) (i32.or (i32.const 0x80) (i32.and (i32.shr_u (local.get $c) (i32.const 6)) (i32.const 0x3f))))
                (i32.store8 offset=2 (local.get $o) (i32.or (i32.const 0x80) (i32.and (local.get $c) (i32.const 0x3f))))
                (local.set $o (i32.add (local.get $o) (i32.const 3))))
              (else
                (i32.store8 (local.get $o) (i32.or (i32.const 0xf0) (i32.shr_u (local.get $c) (i32.const 18))))
                (i32.store8 offset=1 (local.get $o) (i32.or (i32.const 0x80) (i32.and (i32.shr_u (local.get $c) (i32.const 12)) (i32.const 0x3f))))
                (i32.store8 offset=2 (local.get $o) (i32.or (i32.const 0x80) (i32.and (i32.shr_u (local.get $c) (i32.const 6)) (i32.const 0x3f))))
                (i32.store8 offset=3 (local.get $o) (i32.or (i32.const 0x80) (i32.and (local.get $c) (i32.const 0x3f))))
                (local.set $o (i32.add (local.get $o) (i32.const 4)))))))))
        (local.set $s (i32.load offset=20 (local.get $s)))
        (br $next)))
    (i32.sub (local.get $o) (local.get $dst)))

  ;; ---------------------------------------------------------------- dispatch (§6, §7)
  ;; One br_table over Eval opcodes 0-12, Return frame kinds 13-19, Enter 20
  ;; and Halt 21. Returns 1 when the quantum is spent (the state is whole and
  ;; knot_main re-enters), 0 at Halt.
  (func $run (result i32)
    (local $na i32) (local $p i32) (local $h i32) (local $n i32) (local $aux i32) (local $c i32)
    (local $j i32) (local $v i32) (local $d i32)
    (loop $next
      (block $step
        (block $halt
          (block $enter
            (block $r_inva (block $r_invf (block $r_call (block $r_scope (block $r_bind (block $r_gather (block $r_top
            (block $e_invoke (block $e_closure (block $e_case (block $e_let (block $e_ref (block $e_value
            (block $e_gather (block $e_lit (block $e_arm
              (local.set $na (i32.shl (global.get $node) (i32.const 2)))
              (br_table $e_lit $e_gather $e_arm $e_value $e_gather $e_ref $e_gather $e_let $e_case $e_arm
                        $e_closure $e_invoke $e_gather
                        $r_top $r_gather $r_bind $r_scope $r_call $r_invf $r_inva $enter $halt
                (if (result i32) (i32.eqz (global.get $mode))
                  (then (i32.load offset=4100 (local.get $na)))
                  (else (if (result i32) (i32.eq (global.get $mode) (i32.const 1))
                    (then (i32.add (i32.const 13) (i32.and (i32.load (i32.sub (global.get $top) (i32.const 4))) (i32.const 15))))
                    (else (i32.add (i32.const 18) (global.get $mode))))))))
              ;; Branch and Default are entered only through their Case
              (call $internal))
              ;; Eval Literal: the linked pool word
              (global.set $val (i32.load offset=4108 (local.get $na)))
              (global.set $mode (i32.const 1))
              (br $step))
              ;; Eval Construct/Intrinsic/Application/Foreign: gather operands left to right
              (local.set $n (i32.load offset=4112 (local.get $na)))
              (if (i32.eqz (local.get $n))
                (then (call $complete (global.get $node) (global.get $top) (i32.const 0)) (br $step)))
              (drop (call $frame (i32.const 1) (global.get $node) (i32.const 0) (local.get $n)))
              (global.set $node (i32.load offset=4116 (local.get $na)))
              (br $step))
              ;; Eval Value: the immediate for its tag
              (global.set $val (i32.or (i32.shl (i32.load offset=4108 (local.get $na)) (i32.const 1)) (i32.const 1)))
              (global.set $mode (i32.const 1))
              (br $step))
              ;; Eval Reference: dup the slot
              (global.set $val (i32.load offset=16 (i32.add (global.get $act) (i32.shl (i32.load offset=4108 (local.get $na)) (i32.const 2)))))
              (if (i32.eqz (global.get $val)) (then (call $internal)))
              (call $dup (global.get $val))
              (global.set $mode (i32.const 1))
              (br $step))
              ;; Eval Let: Bind, then the value
              (drop (call $frame (i32.const 2) (global.get $node) (i32.const 0) (i32.const 0)))
              (global.set $node (i32.load offset=4112 (local.get $na)))
              (br $step))
              ;; Eval Case
              (call $select (global.get $node))
              (br $step))
              ;; Eval Closure: dup the captures into a new Closure
              (local.set $n (i32.load offset=4120 (local.get $na)))
              (local.set $c (call $alloc (i32.add (local.get $n) (i32.const 1)) (i32.const 1)))
              (i32.store offset=8 (local.get $c) (global.get $node))
              (local.set $j (i32.const 0))
              (block $captured
                (loop $capture
                  (br_if $captured (i32.ge_u (local.get $j) (local.get $n)))
                  (local.set $v (i32.load offset=16 (i32.add (global.get $act)
                    (i32.shl (i32.load offset=4124 (i32.add (local.get $na) (i32.shl (local.get $j) (i32.const 2)))) (i32.const 2)))))
                  (call $dup (local.get $v))
                  (i32.store offset=12 (i32.add (local.get $c) (i32.shl (local.get $j) (i32.const 2))) (local.get $v))
                  (local.set $j (i32.add (local.get $j) (i32.const 1)))
                  (br $capture)))
              (global.set $val (local.get $c))
              (global.set $mode (i32.const 1))
              (br $step))
              ;; Eval Invoke: InvokeFunction, then the function
              (drop (call $frame (i32.const 5) (global.get $node) (i32.const 0) (i32.const 0)))
              (global.set $node (i32.load offset=4108 (local.get $na)))
              (br $step))
            ;; Return to Top: release the activation, then §8's phase
            (call $drop (global.get $act))
            (global.set $act (i32.const 0))
            (local.set $aux (i32.load (i32.sub (global.get $top) (i32.const 8))))
            (if (i32.eqz (local.get $aux))
              (then (call $describe (global.get $val)) (return (i32.const 0))))
            (if (i32.eq (local.get $aux) (i32.const 3))
              (then (call $finish (global.get $val)) (return (i32.const 0))))
            (i32.store (i32.sub (global.get $top) (i32.const 8)) (i32.add (local.get $aux) (i32.const 1)))
            (i32.store (i32.const 32) (global.get $terminal))
            (global.set $tgt (global.get $val))
            (global.set $tfn (i32.const 0))
            (global.set $ops (i32.const 32))
            (global.set $nops (i32.sub (local.get $aux) (i32.const 1)))
            (global.set $mode (i32.const 2))
            (br $step))
            ;; Return to Gather: fill the next operand; the last completes the node
            (local.set $h (i32.load (i32.sub (global.get $top) (i32.const 4))))
            (local.set $n (i32.shr_u (local.get $h) (i32.const 4)))
            (local.set $aux (i32.load (i32.sub (global.get $top) (i32.const 8))))
            (local.set $p (i32.sub (i32.sub (global.get $top) (i32.const 12)) (i32.shl (local.get $n) (i32.const 2))))
            (i32.store (i32.add (local.get $p) (i32.shl (local.get $aux) (i32.const 2))) (global.get $val))
            (local.set $aux (i32.add (local.get $aux) (i32.const 1)))
            (if (i32.lt_u (local.get $aux) (local.get $n))
              (then
                (i32.store (i32.sub (global.get $top) (i32.const 8)) (local.get $aux))
                (global.set $node (i32.load offset=4116 (i32.shl (i32.add (i32.load (i32.sub (global.get $top) (i32.const 12)))
                                                                           (local.get $aux)) (i32.const 2))))
                (global.set $mode (i32.const 0))
                (br $step)))
            (local.set $c (i32.load (i32.sub (global.get $top) (i32.const 12))))
            (global.set $top (local.get $p))
            (call $complete (local.get $c) (local.get $p) (local.get $n))
            (br $step))
            ;; Return to Bind: the value takes slot `depth`; the body runs in a Scope
            (local.set $c (i32.load (i32.sub (global.get $top) (i32.const 12))))
            (global.set $top (i32.sub (global.get $top) (i32.const 12)))
            (local.set $d (i32.load offset=12 (global.get $act)))
            (i32.store offset=16 (i32.add (global.get $act) (i32.shl (local.get $d) (i32.const 2))) (global.get $val))
            (drop (call $frame (i32.const 3) (i32.const 0) (local.get $d) (i32.const 0)))
            (i32.store offset=12 (global.get $act) (i32.add (local.get $d) (i32.const 1)))
            (global.set $node (call $w (i32.add (local.get $c) (i32.const 5))))
            (global.set $mode (i32.const 0))
            (br $step))
            ;; Return to Scope: drop and zero the scope's slots, restore the depth
            (local.set $aux (i32.load (i32.sub (global.get $top) (i32.const 8))))
            (global.set $top (i32.sub (global.get $top) (i32.const 12)))
            (local.set $d (i32.load offset=12 (global.get $act)))
            (block $cleared
              (loop $clear
                (br_if $cleared (i32.le_u (local.get $d) (local.get $aux)))
                (local.set $d (i32.sub (local.get $d) (i32.const 1)))
                (local.set $p (i32.add (global.get $act) (i32.shl (local.get $d) (i32.const 2))))
                (call $drop (i32.load offset=16 (local.get $p)))
                (i32.store offset=16 (local.get $p) (i32.const 0))
                (br $clear)))
            (i32.store offset=12 (global.get $act) (local.get $aux))
            (br $step))
            ;; Return to Call: release the callee's activation, resume the caller's
            (local.set $c (i32.load (i32.sub (global.get $top) (i32.const 16))))
            (global.set $top (i32.sub (global.get $top) (i32.const 16)))
            (call $drop (global.get $act))
            (global.set $act (local.get $c))
            (br $step))
            ;; Return to InvokeFunction: a live arrow gathers its argument
            (local.set $c (i32.load (i32.sub (global.get $top) (i32.const 12))))
            (global.set $top (i32.sub (global.get $top) (i32.const 12)))
            (if (call $w (i32.add (local.get $c) (i32.const 4)))
              (then
                (i32.store (call $frame (i32.const 6) (local.get $c) (i32.const 0) (i32.const 1)) (global.get $val))
                (global.set $node (call $w (i32.add (local.get $c) (i32.const 5))))
                (global.set $mode (i32.const 0))
                (br $step)))
            (global.set $tgt (global.get $val))
            (global.set $tfn (i32.const 0))
            (global.set $nops (i32.const 0))
            (global.set $mode (i32.const 2))
            (br $step))
            ;; Return to InvokeArgument: apply the function to the argument
            (global.set $tgt (i32.load (i32.sub (global.get $top) (i32.const 16))))
            (global.set $top (i32.sub (global.get $top) (i32.const 16)))
            (i32.store (i32.const 32) (global.get $val))
            (global.set $tfn (i32.const 0))
            (global.set $ops (i32.const 32))
            (global.set $nops (i32.const 1))
            (global.set $mode (i32.const 2))
            (br $step))
          ;; Enter; a spent quantum yields with the entry complete (§7)
          (call $enter)
          (if (i32.eq (global.get $quantum) (i32.const 65536)) (then (return (i32.const 1))))
          (br $step))
        (return (i32.const 0)))
      ;;TEST (if (global.get $single) (then (return (i32.const 2))))
      (br $next))
    (i32.const 0))

  ;; §8 Program phase 3: Emit completes, Halt calls die
  (func $finish (param $x i32)
    (local $code i32) (local $n i32) (local $dst i32)
    (if (i32.or (i32.or (i32.and (local.get $x) (i32.const 1)) (i32.eqz (local.get $x)))
          (i32.or (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7))
                  (i32.ne (i32.load offset=8 (local.get $x)) (global.get $rIoop))))
      (then (call $refuse (global.get $R_ill_typed))))
    (if (i32.eqz (i32.load offset=12 (local.get $x)))
      (then
        (call $drop (local.get $x))
        (global.set $oc (i32.const 1))
        (global.set $mode (i32.const 3))
        (return)))
    (local.set $code (call $num (i32.load offset=16 (local.get $x))))
    (local.set $dst (call $align8 (global.get $bump)))
    (local.set $n (call $utf8out (i32.load offset=20 (local.get $x)) (local.get $dst)))
    (call $drop (local.get $x))
    (global.set $oc (i32.const 2))
    (global.set $okind (local.get $code))
    (global.set $mode (i32.const 3))
    (call $io_die (local.get $code) (local.get $dst) (local.get $n))
    unreachable)

  ;; ---------------------------------------------------------------- describe (§8)
  ;; `Evaluated<TAB>type<TAB>tag<TAB>tree`. The tree renders from a worklist of
  ;; (word, type) items and two separators; a Nat word n is n Succ layers
  ;; around Zero and counts n + 1 visits. Bounds: 1,048,576 visits and 16 MiB
  ;; of tree text, else Exhausted kind 2 (display).
  (global $resT (mut i32) (i32.const 0))
  (global $o (mut i32) (i32.const 0))
  (global $olimit (mut i32) (i32.const 0))

  (func $emit (param $src i32) (param $n i32)
    (if (i32.gt_u (local.get $n) (i32.sub (global.get $olimit) (global.get $o)))
      (then (call $exhaust (i32.const 2) (global.get $R_display))))
    (call $grow (i64.extend_i32_u (i32.add (global.get $o) (local.get $n))))
    (memory.copy (global.get $o) (local.get $src) (local.get $n))
    (global.set $o (i32.add (global.get $o) (local.get $n))))

  (func $emitdec (param $v i32)
    (local $p i32)
    (local.set $p (i32.const 80))
    (loop $digit
      (local.set $p (i32.sub (local.get $p) (i32.const 1)))
      (i32.store8 (local.get $p) (i32.add (i32.const 48) (i32.rem_u (local.get $v) (i32.const 10))))
      (local.set $v (i32.div_u (local.get $v) (i32.const 10)))
      (br_if $digit (local.get $v)))
    (call $emit (local.get $p) (i32.sub (i32.const 80) (local.get $p))))

  (func $describe (param $x i32)
    (local $out i32) (local $sp i32) (local $base i32) (local $visits i32) (local $w i32) (local $t i32)
    (local $tag i32) (local $rec i32) (local $name i32) (local $nf i32) (local $j i32) (local $v i32)
    (local.set $out (call $align8 (global.get $bump)))
    (global.set $o (local.get $out))
    (global.set $olimit (i32.add (local.get $out) (i32.const 0x1000100)))
    (call $emit (i32.const 352) (i32.const 10))
    (call $emitdec (global.get $resT))
    (i32.store8 (i32.const 96) (i32.const 9))
    (call $emit (i32.const 96) (i32.const 1))
    (if (i32.eq (global.get $resT) (global.get $rNat))
      (then (call $emitdec (i32.ne (call $num (local.get $x)) (i32.const 0))))
      (else (call $emitdec (call $tagof (local.get $x) (global.get $resT)))))
    (call $emit (i32.const 96) (i32.const 1))
    (global.set $olimit (i32.add (global.get $o) (i32.const 0x1000000)))
    (local.set $base (call $align8 (i32.add (global.get $olimit) (i32.const 8))))
    (local.set $sp (local.get $base))
    (call $grow (i64.add (i64.extend_i32_u (local.get $sp)) (i64.const 8)))
    (i32.store (local.get $sp) (local.get $x))
    (i32.store offset=4 (local.get $sp) (global.get $resT))
    (local.set $sp (i32.add (local.get $sp) (i32.const 8)))
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $sp) (local.get $base)))
        (local.set $sp (i32.sub (local.get $sp) (i32.const 8)))
        (local.set $w (i32.load (local.get $sp)))
        (local.set $t (i32.load offset=4 (local.get $sp)))
        ;; separators: -2 is ",", -3 is "}"
        (if (i32.eq (local.get $t) (i32.const -2))
          (then (i32.store8 (i32.const 97) (i32.const 44)) (call $emit (i32.const 97) (i32.const 1)) (br $next)))
        (if (i32.eq (local.get $t) (i32.const -3))
          (then (i32.store8 (i32.const 97) (i32.const 125)) (call $emit (i32.const 97) (i32.const 1)) (br $next)))
        (if (i32.eq (local.get $t) (global.get $rNat))
          (then
            (local.set $v (call $num (local.get $w)))
            (if (i64.gt_u (i64.add (i64.add (i64.extend_i32_u (local.get $visits)) (i64.extend_i32_u (local.get $v))) (i64.const 1))
                          (i64.const 1048576))
              (then (call $exhaust (i32.const 2) (global.get $R_display))))
            (local.set $visits (i32.add (i32.add (local.get $visits) (local.get $v)) (i32.const 1)))
            (if (i64.gt_u (i64.add (i64.mul (i64.extend_i32_u (local.get $v)) (i64.const 6)) (i64.const 6))
                          (i64.extend_i32_u (i32.sub (global.get $olimit) (global.get $o))))
              (then (call $exhaust (i32.const 2) (global.get $R_display))))
            (call $grow (i64.add (i64.extend_i32_u (global.get $o))
                                 (i64.add (i64.mul (i64.extend_i32_u (local.get $v)) (i64.const 6)) (i64.const 6))))
            (local.set $j (local.get $v))
            (block $opened
              (loop $open
                (br_if $opened (i32.eqz (local.get $j)))
                (i32.store (global.get $o) (i32.const 0x63637553))
                (i32.store8 offset=4 (global.get $o) (i32.const 123))
                (global.set $o (i32.add (global.get $o) (i32.const 5)))
                (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                (br $open)))
            (i32.store (global.get $o) (i32.const 0x6f72655a))
            (i32.store16 offset=4 (global.get $o) (i32.const 0x7d7b))
            (global.set $o (i32.add (global.get $o) (i32.const 6)))
            (memory.fill (global.get $o) (i32.const 125) (local.get $v))
            (global.set $o (i32.add (global.get $o) (local.get $v)))
            (br $next)))
        (local.set $visits (i32.add (local.get $visits) (i32.const 1)))
        (if (i32.gt_u (local.get $visits) (i32.const 1048576)) (then (call $exhaust (i32.const 2) (global.get $R_display))))
        (local.set $tag (call $tagof (local.get $w) (local.get $t)))
        (local.set $rec (call $ctor (local.get $t) (local.get $tag)))
        (local.set $name (call $w (i32.add (local.get $rec) (i32.const 3))))
        (call $emit (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $name) (i32.const 2)) (i32.const 2)))
                    (call $w (i32.add (local.get $name) (i32.const 1))))
        (i32.store8 (i32.const 97) (i32.const 123))
        (call $emit (i32.const 97) (i32.const 1))
        (if (i32.and (local.get $w) (i32.const 1))
          (then (i32.store8 (i32.const 97) (i32.const 125)) (call $emit (i32.const 97) (i32.const 1)) (br $next)))
        ;; fields in order: push "}", then fields last to first with "," between
        (local.set $nf (i32.sub (i32.shr_u (i32.load offset=4 (local.get $w)) (i32.const 3)) (i32.const 2)))
        (call $grow (i64.add (i64.extend_i32_u (local.get $sp)) (i64.shl (i64.extend_i32_u (i32.add (local.get $nf) (i32.const 1))) (i64.const 4))))
        (i32.store (local.get $sp) (i32.const 0))
        (i32.store offset=4 (local.get $sp) (i32.const -3))
        (local.set $sp (i32.add (local.get $sp) (i32.const 8)))
        (local.set $j (local.get $nf))
        (block $pushed
          (loop $field
            (br_if $pushed (i32.eqz (local.get $j)))
            (local.set $j (i32.sub (local.get $j) (i32.const 1)))
            (i32.store (local.get $sp) (i32.load offset=16 (i32.add (local.get $w) (i32.shl (local.get $j) (i32.const 2)))))
            (i32.store offset=4 (local.get $sp) (call $w (i32.add (i32.add (local.get $rec) (i32.const 5)) (local.get $j))))
            (local.set $sp (i32.add (local.get $sp) (i32.const 8)))
            (if (local.get $j)
              (then
                (i32.store (local.get $sp) (i32.const 0))
                (i32.store offset=4 (local.get $sp) (i32.const -2))
                (local.set $sp (i32.add (local.get $sp) (i32.const 8)))))
            (br $field)))
        (br $next)))
    (call $drop (local.get $x))
    (global.set $oc (i32.const 1))
    (global.set $mode (i32.const 3))
    (call $io_print (local.get $out) (i32.sub (global.get $o) (local.get $out))))

  ;; ---------------------------------------------------------------- entry (§8)
  ;; argument i as an unsigned decimal, or -1
  (func $u32arg (param $i i32) (result i64)
    (local $p i32) (local $n i32) (local $j i32) (local $v i64) (local $b i32)
    (local.set $p (i32.load (i32.add (global.get $argv) (i32.shl (local.get $i) (i32.const 3)))))
    (local.set $n (i32.load offset=4 (i32.add (global.get $argv) (i32.shl (local.get $i) (i32.const 3)))))
    (if (i32.eqz (local.get $n)) (then (return (i64.const -1))))
    (block $done
      (loop $digit
        (br_if $done (i32.ge_u (local.get $j) (local.get $n)))
        (local.set $b (i32.sub (i32.load8_u (i32.add (local.get $p) (local.get $j))) (i32.const 48)))
        (if (i32.gt_u (local.get $b) (i32.const 9)) (then (return (i64.const -1))))
        (local.set $v (i64.add (i64.mul (local.get $v) (i64.const 10)) (i64.extend_i32_u (local.get $b))))
        (if (i64.gt_u (local.get $v) (i64.const 0xffffffff)) (then (return (i64.const -1))))
        (local.set $j (i32.add (local.get $j) (i32.const 1)))
        (br $digit)))
    (local.get $v))

  (func $u32must (param $i i32) (result i32)
    (local $v i64)
    (local.set $v (call $u32arg (local.get $i)))
    (if (i64.lt_s (local.get $v) (i64.const 0))
      (then (call $stop (i32.const 3) (i32.const 5) (i32.const 192) (global.get $R_expected_u32))))
    (i32.wrap_i64 (local.get $v)))

  ;; argument i equals the bytes of name record `n`
  (func $argis (param $i i32) (param $p0 i32) (param $n i32) (result i32)
    (local $p i32) (local $len i32)
    (local.set $p (i32.load (i32.add (global.get $argv) (i32.shl (local.get $i) (i32.const 3)))))
    (local.set $len (i32.load offset=4 (i32.add (global.get $argv) (i32.shl (local.get $i) (i32.const 3)))))
    (if (i32.ne (local.get $len) (local.get $n)) (then (return (i32.const 0))))
    (block $done
      (loop $byte
        (br_if $done (i32.eqz (local.get $len)))
        (local.set $len (i32.sub (local.get $len) (i32.const 1)))
        (if (i32.ne (i32.load8_u (i32.add (local.get $p) (local.get $len))) (i32.load8_u (i32.add (local.get $p0) (local.get $len))))
          (then (return (i32.const 0))))
        (br $done)))
    (loop $byte
      (if (local.get $len)
        (then
          (local.set $len (i32.sub (local.get $len) (i32.const 1)))
          (if (i32.ne (i32.load8_u (i32.add (local.get $p) (local.get $len))) (i32.load8_u (i32.add (local.get $p0) (local.get $len))))
            (then (return (i32.const 0))))
          (br $byte))))
    (i32.const 1))

  ;; §8 describable: algebraic, every live field of every constructor in turn
  (func $describable (param $t i32) (result i32)
    (local $seen i32) (local $stack i32) (local $sp i32) (local $u i32) (local $c i32) (local $rec i32) (local $j i32)
    (local.set $seen (call $take (i32.add (global.get $nT) (i32.const 8))))
    (local.set $stack (call $take (i32.shl (i32.add (global.get $W) (i32.const 8)) (i32.const 2))))
    (i32.store (local.get $stack) (local.get $t))
    (local.set $sp (i32.add (local.get $stack) (i32.const 4)))
    (block $done
      (loop $next
        (br_if $done (i32.eq (local.get $sp) (local.get $stack)))
        (local.set $sp (i32.sub (local.get $sp) (i32.const 4)))
        (local.set $u (i32.load (local.get $sp)))
        (if (i32.eq (local.get $u) (i32.const -1)) (then (return (i32.const 0))))
        (br_if $next (i32.load8_u (i32.add (local.get $seen) (local.get $u))))
        (i32.store8 (i32.add (local.get $seen) (local.get $u)) (i32.const 1))
        (if (call $kind (local.get $u)) (then (return (i32.const 0))))
        (local.set $c (i32.const 0))
        (block $ctors
          (loop $ctor
            (br_if $ctors (i32.ge_u (local.get $c) (call $ty (local.get $u) (i32.const 3))))
            (local.set $rec (call $ctorv (local.get $u) (local.get $c)))
            (local.set $j (i32.const 0))
            (block $fields
              (loop $field
                (br_if $fields (i32.ge_u (local.get $j) (call $w (i32.add (local.get $rec) (i32.const 4)))))
                (i32.store (local.get $sp) (call $w (i32.add (i32.add (local.get $rec) (i32.const 5)) (local.get $j))))
                (local.set $sp (i32.add (local.get $sp) (i32.const 4)))
                (local.set $j (i32.add (local.get $j) (i32.const 1)))
                (br $field)))
            (local.set $c (i32.add (local.get $c) (i32.const 1)))
            (br $ctor)))
        (br $next)))
    (i32.const 1))

  ;; Book: IMAGE FN FUEL ORDINALS; Program: IMAGE FUEL -- ARGS. Returns the
  ;; entered function's record; Book ordinals go to the frame region at F0+64.
  (func $entry (result i32)
    (local $f i32) (local $i i32) (local $n i32) (local $o i32) (local $p i32) (local $name i32)
    (if (i32.eq (call $w (i32.const 3)) (i32.const 1))
      (then
        (if (i32.lt_u (global.get $argc) (i32.const 3))
          (then (call $stop (i32.const 3) (i32.const 5) (i32.const 192) (global.get $R_usage))))
        (if (i32.eqz (call $argis (i32.const 2) (i32.const 40) (i32.const 2)))
          (then (call $stop (i32.const 3) (i32.const 5) (i32.const 192) (global.get $R_usage))))
        (global.set $fuel (call $u32must (i32.const 1)))
        (return (call $tab (global.get $tF) (call $w (i32.const 4))))))
    (if (i32.lt_u (global.get $argc) (i32.const 3))
      (then (call $stop (i32.const 3) (i32.const 5) (i32.const 192) (global.get $R_usage))))
    (global.set $fuel (call $u32must (i32.const 2)))
    (local.set $i (i32.const 3))
    (block $parsed
      (loop $each
        (br_if $parsed (i32.ge_u (local.get $i) (global.get $argc)))
        (drop (call $u32must (local.get $i)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (local.set $f (i32.const -1))
    (local.set $i (i32.const 0))
    (block $found
      (loop $each
        (br_if $found (i32.ge_u (local.get $i) (global.get $nF)))
        (local.set $name (call $tab (global.get $tM) (call $w (i32.add (call $tab (global.get $tF) (local.get $i)) (i32.const 1)))))
        (if (call $argis (i32.const 1) (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $name) (i32.const 2)) (i32.const 2)))
                         (call $w (i32.add (local.get $name) (i32.const 1))))
          (then (local.set $f (call $tab (global.get $tF) (local.get $i))) (br $found)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (if (i32.eq (local.get $f) (i32.const -1))
      (then (call $stop (i32.const 3) (i32.const 5) (i32.const 160) (global.get $R_unknown_export))))
    (local.set $n (call $w (i32.add (local.get $f) (i32.const 3))))
    (if (i32.ne (i32.sub (global.get $argc) (i32.const 3)) (local.get $n))
      (then (call $stop (i32.const 3) (i32.const 5) (i32.const 160) (global.get $R_argument_arity))))
    (local.set $i (i32.const 0))
    (block $done
      (loop $each
        (br_if $done (i32.ge_u (local.get $i) (local.get $n)))
        (local.set $o (call $u32must (i32.add (local.get $i) (i32.const 3))))
        (local.set $p (call $w (i32.add (i32.add (local.get $f) (i32.const 6)) (local.get $i))))
        (if (i32.or (i32.ne (call $kind (local.get $p)) (i32.const 0))
                    (i32.ge_u (local.get $o) (call $ty (local.get $p) (i32.const 3))))
          (then (call $stop (i32.const 3) (i32.const 5) (i32.const 160) (global.get $R_argument_range))))
        (if (call $w (i32.add (call $ctorv (local.get $p) (local.get $o)) (i32.const 4)))
          (then (call $stop (i32.const 3) (i32.const 5) (i32.const 160) (global.get $R_structured_argument))))
        (i32.store (i32.add (i32.add (global.get $F0) (i32.const 64)) (i32.shl (local.get $i) (i32.const 2)))
                   (i32.or (i32.shl (local.get $o) (i32.const 1)) (i32.const 1)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (if (i32.eqz (call $describable (call $w (i32.add (local.get $f) (i32.const 2)))))
      (then (call $stop (i32.const 4) (i32.const 3) (i32.const 224) (global.get $R_result_type))))
    (global.set $resT (call $w (i32.add (local.get $f) (i32.const 2))))
    (local.get $f))

  ;; ---------------------------------------------------------------- materialize and link (§5)
  (func $immortal (param $c i32) (result i32)
    (i32.store (local.get $c) (i32.const -1))
    (local.get $c))

  ;; a pool scalar: immediate below 2^31, else an immortal Big
  (func $constant (param $v i32) (result i32)
    (if (result i32) (i32.ge_u (local.get $v) (i32.const 0x80000000))
      (then (call $immortal (call $scalar (local.get $v))))
      (else (call $scalar (local.get $v)))))

  (func $materialize
    (local $i i32) (local $rec i32) (local $j i32) (local $s i32) (local $at i32)
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nK)))
        (local.set $rec (call $tab (global.get $tK) (local.get $i)))
        (if (i32.eq (call $w (i32.add (local.get $rec) (i32.const 1))) (i32.const 3))
          (then
            ;; a String: SCon chain from the last character, ending in SNil
            (local.set $s (i32.const 1))
            (local.set $j (call $w (i32.add (local.get $rec) (i32.const 2))))
            (block $built
              (loop $char
                (br_if $built (i32.eqz (local.get $j)))
                (local.set $j (i32.sub (local.get $j) (i32.const 1)))
                (local.set $s (call $immortal (call $scon (call $constant (call $w (i32.add (i32.add (local.get $rec) (i32.const 3)) (local.get $j))))
                                                          (local.get $s))))
                (br $char)))
            (call $tabset (global.get $tK) (local.get $i) (local.get $s)))
          (else (call $tabset (global.get $tK) (local.get $i) (call $constant (call $w (i32.add (local.get $rec) (i32.const 3)))))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    ;; a Program's terminal continuation: an immortal Closure with node none
    (if (i32.eq (call $w (i32.const 3)) (i32.const 1))
      (then
        (global.set $terminal (call $immortal (call $alloc (i32.const 1) (i32.const 1))))
        (i32.store offset=8 (global.get $terminal) (i32.const -1))))
    ;; link in place: Literal constants become pool words, Application indices
    ;; function records, a data type's first constructor and each
    ;; constructor's name their records
    (local.set $at (i32.add (global.get $sN) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nN)))
        (local.set $j (call $w (i32.add (local.get $at) (i32.const 1))))
        (if (i32.eqz (local.get $j))
          (then (call $wset (i32.add (local.get $at) (i32.const 3))
                  (call $tab (global.get $tK) (call $w (i32.add (local.get $at) (i32.const 3)))))))
        (if (i32.eq (local.get $j) (i32.const 6))
          (then (call $wset (i32.add (local.get $at) (i32.const 3))
                  (call $tab (global.get $tF) (call $w (i32.add (local.get $at) (i32.const 3)))))))
        (if (i32.eq (local.get $j) (i32.const 12))
          (then (if (i32.ne (call $w (i32.add (local.get $at) (i32.const 3))) (i32.const 1))
                  (then (call $stop (i32.const 4) (i32.const 3) (i32.const 256) (global.get $R_foreign))))))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nT)))
        (if (i32.and (i32.eqz (call $kind (local.get $i))) (i32.ne (call $ty (local.get $i) (i32.const 3)) (i32.const 0)))
          (then (call $wset (i32.add (i32.add (global.get $sT) (i32.const 4)) (i32.mul (local.get $i) (i32.const 5)))
                  (call $tab (global.get $tC) (call $ty (local.get $i) (i32.const 2))))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each)))
    (local.set $at (i32.add (global.get $sC) (i32.const 1)))
    (local.set $i (i32.const 0))
    (block $end
      (loop $each
        (br_if $end (i32.ge_u (local.get $i) (global.get $nC)))
        (call $wset (i32.add (local.get $at) (i32.const 3))
          (call $tab (global.get $tM) (call $w (i32.add (local.get $at) (i32.const 3)))))
        (local.set $at (i32.add (local.get $at) (call $w (local.get $at))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $each))))

  ;; ---------------------------------------------------------------- boot
  (func $boot
    (local $f i32)
    (call $read_image)
    (call $decode)
    (call $validate)
    (call $canonical)
    (local.set $f (call $entry))
    (call $grow (i64.extend_i32_u (global.get $H0)))
    (call $materialize)
    ;; §8: Top(phase), then the first entry
    (global.set $top (global.get $F0))
    (drop (call $frame (i32.const 0) (i32.const 0) (i32.eq (call $w (i32.const 3)) (i32.const 1)) (i32.const 0)))
    (global.set $tgt (local.get $f))
    (global.set $tfn (i32.const 1))
    (global.set $ops (i32.add (global.get $F0) (i32.const 64)))
    (global.set $nops (call $w (i32.add (local.get $f) (i32.const 3))))
    (global.set $mode (i32.const 2)))

  (func (export "knot_main")
    (call $boot)
    (loop $again
      (if (call $run)
        (then
          (global.set $quantum (i32.const 0))
          (global.set $yields (i32.add (global.get $yields) (i32.const 1)))
          (br $again)))))

  ;; ---------------------------------------------------------------- test build only
  ;; vm_limits lowers the frame region or heap before boot; vm_boot loads;
  ;; vm_step runs one transition (0 halted, 1 yield, 2 stepped); vm_dump
  ;; writes the registers at 3920 and returns that address.
  ;;TEST (func (export "vm_limits") (param $frames i32) (param $heap i64)
  ;;TEST   (global.set $frameBytes (local.get $frames))
  ;;TEST   (global.set $heapBytes (local.get $heap)))
  ;;TEST (func (export "vm_boot") (call $boot))
  ;;TEST (func (export "vm_step") (result i32)
  ;;TEST   (local $r i32)
  ;;TEST   (global.set $single (i32.const 1))
  ;;TEST   (local.set $r (call $run))
  ;;TEST   (if (i32.eq (local.get $r) (i32.const 1))
  ;;TEST     (then (global.set $quantum (i32.const 0)) (global.set $yields (i32.add (global.get $yields) (i32.const 1)))))
  ;;TEST   (local.get $r))
  ;;TEST (func (export "vm_dump") (result i32)
  ;;TEST   (i32.store (i32.const 3920) (global.get $mode))
  ;;TEST   (i32.store (i32.const 3924) (global.get $node))
  ;;TEST   (i32.store (i32.const 3928) (global.get $val))
  ;;TEST   (i32.store (i32.const 3932) (global.get $tgt))
  ;;TEST   (i32.store (i32.const 3936) (global.get $tfn))
  ;;TEST   (i32.store (i32.const 3940) (global.get $ops))
  ;;TEST   (i32.store (i32.const 3944) (global.get $nops))
  ;;TEST   (i32.store (i32.const 3948) (global.get $act))
  ;;TEST   (i32.store (i32.const 3952) (global.get $top))
  ;;TEST   (i32.store (i32.const 3956) (global.get $F0))
  ;;TEST   (i32.store (i32.const 3960) (global.get $FL))
  ;;TEST   (i32.store (i32.const 3964) (global.get $H0))
  ;;TEST   (i32.store (i32.const 3968) (global.get $bump))
  ;;TEST   (i32.store (i32.const 3972) (global.get $fuel))
  ;;TEST   (i32.store (i32.const 3976) (global.get $calls))
  ;;TEST   (i32.store (i32.const 3980) (global.get $quantum))
  ;;TEST   (i32.store (i32.const 3984) (global.get $oc))
  ;;TEST   (i32.store (i32.const 3988) (global.get $okind))
  ;;TEST   (i32.store (i32.const 3992) (global.get $ocause))
  ;;TEST   (i32.store (i32.const 3996) (global.get $W))
  ;;TEST   (i32.store (i32.const 4000) (global.get $terminal))
  ;;TEST   (i32.store (i32.const 4004) (global.get $yields))
  ;;TEST   (i32.store (i32.const 4008) (i32.wrap_i64 (global.get $HL)))
  ;;TEST   (i32.const 3920))
)
