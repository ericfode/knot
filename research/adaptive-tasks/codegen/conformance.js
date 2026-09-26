function word_to_u32(w) {
  let x = 0;
  for (let i = 0; w.$ === "WCon"; i++) {
    x |= Number(w.head) << i;
    w = w.tail;
  }
  return x >>> 0;
}

function u32_to_word(x) {
  let w = {$: "WNil"};
  for (let i = 31; i >= 0; i--) {
    w = {$: "WCon", head: ((x >>> i) & 1) === 1, tail: w};
  }
  return w;
}

function cmp_new(a, b) {
  return {$: a < b ? "LT"
    : a === b ? "EQ" : "GT"};
}

function nat_divmod(a, b) {
  return b === 0 ? {$: "Tuple", fst: 0, snd: a}
    : {$: "Tuple", fst: Math.trunc(a / b), snd: a % b};
}

function nat_chk(n) {
  if (n > 281474976710655) {
    throw "bend: a Nat past the largest immediate 2^48-1";
  }
  return n;
}

function nat_host(n) {
  const int = typeof n === "bigint" || Number.isInteger(n);
  if (int && n >= 0 && n <= 2 ** 53) {
    return Number(n);
  }
  return { [Symbol.toPrimitive]() { throw "bend: a Nat past the largest immediate 2^48-1"; } };
}

function f32_show(x) {
  if (x !== x) {
    return "nan";
  }
  if (!Number.isFinite(x) || Object.is(x, -0)) {
    return x < 0 ? "-inf"
      : x === 0 ? "-0" : "inf";
  }
  let s = "x";
  for (let p = 1; p <= 9 && Math.fround(Number(s)) !== x; p += 1) {
    s = String(Number(x.toExponential(p - 1)));
  }
  return s;
}

function f32_bits(x) {
  return new Uint32Array(new Float32Array([x]).buffer)[0];
}

function f32_from_bits(u) {
  return new Float32Array(new Uint32Array([u]).buffer)[0];
}

function f32_read(s) {
  const re = /^\s*[+-]?((\d+\.?\d*|\.\d+)(e[+-]?\d+)?|inf(inity)?|nan)$/i;
  const v = Number(s.replace(/inf\w*/i, "Infinity"));
  return re.test(s) ? {$: "Some", value: Math.fround(v)} : {$: "None"};
}

function char_new(code) {
  if (code > 0x10FFFF || (code >= 0xD800 && code <= 0xDFFF)) {
    throw "bend: " + code + " is not a Unicode scalar value";
  }
  return String.fromCodePoint(code);
}

// Array
// =====

function array_new(d, v) {
  if (d > 31) {
    throw "bend: an array past the deepest block class 31";
  }
  return Array(2 ** d).fill(v);
}

function array_node(a, b) {
  if (a.length !== b.length) {
    throw "bend: runtime fail-stop";
  }
  return a.concat(b);
}

function array_rmw(a, i, f) {
  const at = i % a.length;
  const old = a[at];
  a[at] = f(old);
  return {$: "Tuple", fst: a, snd: old};
}

// Run
// ===

function run_tail(f, x) {
  return {$: "$JMP", f: f.j?.f === f ? f.j : f, x: [x]};
}

function run_clo(j) {
  const f = (x) => run_loop(j(x));
  f.j = j;
  j.f = f;
  return f;
}

function run_loop(r) {
  while (r !== null && typeof r === "object" && r.$ === "$JMP") {
    r = r.f(...r.x);
  }
  return r;
}

function run_lib(f, n) {
  return (...a) => a.length < n ? run_lib((...b) => f(...a, ...b), n - a.length)
    : f(...a);
}

// Effect
// ======

// An effect source registers each effect under its def's key, as in C.
const $0eff = Object.create(null);

function io_eff(k, run, need) {
  if (k in $0eff) {
    throw new Error("bend: two effects register " + k);
  }
  $0eff[k] = { run, need };
}
(() => {
// IO
// ==

function io_print(text) {
  io_out(1, io_bytes(text + "\n"));
  return { $: "Unit" };
}

io_eff("IO.print", io_print);

})();

for (const k of ["IO.print"]) {
  if (!(k in $0eff)) {
    throw new Error("bend: no effect registers " + k);
  }
}

// Program
// =======

function $main$() {
  return run_clo((_x_0) => {
  return $IO$bind$((_x_1) => $IO$print$(($show_observation$(($task$observe$(($task$run$(0, ($sample$()))))))), _x_1), run_clo((_x_2) => {
  return run_clo((_x_3) => {
  return $IO$bind$((_x_4) => $IO$print$(($show_observation$(($task$observe$(($task$run$(5, ($sample$()))))))), _x_4), run_clo((_x_5) => {
  return run_clo((_x_6) => {
  return $IO$bind$((_x_7) => $IO$print$(($show_observation$(($task$observe$(($task$run$(6, ($sample$()))))))), _x_7), run_clo((_x_8) => {
  return run_clo((_x_9) => {
  return $IO$bind$((_x_10) => $IO$print$(($show_observation$(($task$observe$(($task$slices$(6, 1, ($sample$()))))))), _x_10), run_clo((_x_11) => {
  return run_clo((_x_12) => {
  return $IO$bind$((_x_13) => $IO$print$(($show_observation$(($task$observe$(($task$slices$(2, 3, ($sample$()))))))), _x_13), run_clo((_x_14) => {
  return run_clo((_x_15) => {
  return $IO$bind$((_x_16) => $IO$print$(($show_observation$(($task$observe$(($task$slices$(9, 0, ($sample$()))))))), _x_16), run_clo((_x_17) => {
  return run_clo((_x_18) => {
  return $IO$bind$((_x_19) => $IO$print$(($show_observation$(($task$observe$(($task$run$(9, ($task$run$(6, ($sample$()))))))))), _x_19), run_clo((_x_20) => {
  return run_clo((_x_21) => {
  return $IO$bind$((_x_22) => $IO$print$(($show_observation$(($task$observe$(($task$run$(2, ($task$start$(41, 0, 9, {$: "Con", "head": {$: "task.Binary", "left": {$: "task.OwnedWord", "value": 7}}, "tail": {$: "Nil"}})))))))), _x_22), run_clo((_x_23) => {
  return run_clo((_x_24) => {
  return $IO$bind$((_x_25) => $IO$print$(($show_put$(($slot$put$({$: "slot.Occupied", "value": {$: "task.OwnedWord", "value": 7}}, {$: "task.OwnedWord", "value": 9})))), _x_25), run_clo((_x_26) => {
  return run_clo((_x_27) => {
  return $IO$bind$((_x_28) => $IO$print$(($show_take$(($slot$take$(($slot$put_slot$(($slot$put$({$: "slot.Vacant"}, {$: "task.OwnedWord", "value": 7})))))))), _x_28), run_clo((_x_29) => {
  return (_x_30) => $IO$print$(($show_take$(($slot$take$(($slot$take_slot$(($slot$take$({$: "slot.Occupied", "value": {$: "task.OwnedWord", "value": 7}})))))))), _x_30);
}), _x_27);
});
}), _x_24);
});
}), _x_21);
});
}), _x_18);
});
}), _x_15);
});
}), _x_12);
});
}), _x_9);
});
}), _x_6);
});
}), _x_3);
});
}), _x_0);
});
}

function $IO$bind$(_m_0, _f_0, _k_0) {
  return run_tail(_m_0, run_clo((_x_0) => {
  return run_tail(_f_0(_x_0), _k_0);
}));
}

function $IO$print$(_text_0, _k_0) {
  return { $: "$FFI", run: $0eff["IO.print"].run, need: $0eff["IO.print"].need, args: [(_text_0)], kont: (_k_0) };
}
function $show_observation$(_o_0) {
  const _tag_0 = _o_0["fst"];
  const _t_0 = _o_0["snd"];
  const _dest_0 = _t_0["fst"];
  const _value_0 = _t_0["snd"];
  return $String$concat$({$: "Con", "head": ($U32$show$(_tag_0)), "tail": {$: "Con", "head": ",", "tail": {$: "Con", "head": ($U32$show$(_dest_0)), "tail": {$: "Con", "head": ",", "tail": {$: "Con", "head": ($U32$show$(_value_0)), "tail": {$: "Nil"}}}}}});
}

function $task$observe$(_r_0) {
  if (_r_0.$ === "task.Checkpoint") {
    const _t_0 = _r_0["task"];
    const _dest_0 = _t_0["destination"];
    const _p_0 = _t_0["payload"];
    return {$: "Tuple", "fst": 0, "snd": {$: "Tuple", "fst": _dest_0, "snd": ($task$observe_payload$(_p_0))}};
  } else {
    const _dest_1 = _r_0["destination"];
    const _p_1 = _r_0["payload"];
    return {$: "Tuple", "fst": 1, "snd": {$: "Tuple", "fst": _dest_1, "snd": ($task$observe_payload$(_p_1))}};
  }
}

function $task$run$($0, $1) {
  for (;;) {
    {
      const _fuel_0 = $0;
      const _state_0 = $1;
      if (_fuel_0 === 0) {
        return _state_0;
      } else {
        const _n_0 = (_fuel_0 - 1);
        if (_state_0.$ === "task.Checkpoint") {
          const _task_0 = _state_0["task"];
          $0 = _n_0;
          $1 = ($task$step$(_task_0));
          continue;
        } else {
          const _dest_0 = _state_0["destination"];
          const _payload_0 = _state_0["payload"];
          return {$: "task.Delivered", "destination": _dest_0, "payload": _payload_0};
        }
      }
    }
  }
}

function $sample$() {
  return $task$start$(73, 3, 11, {$: "Con", "head": {$: "task.Unary", "factor": 3, "bias": 5}, "tail": {$: "Con", "head": {$: "task.Binary", "left": {$: "task.OwnedWord", "value": 7}}, "tail": {$: "Nil"}}});
}

function $task$slices$($0, $1, $2) {
  for (;;) {
    {
      const _count_0 = $0;
      const _quantum_0 = $1;
      const _state_0 = $2;
      if (_count_0 === 0) {
        return _state_0;
      } else {
        const _n_0 = (_count_0 - 1);
        $0 = _n_0;
        $1 = _quantum_0;
        $2 = ($task$run$(_quantum_0, _state_0));
        continue;
      }
    }
  }
}

function $task$start$(_dest_0, _ticks_0, _seed_0, _frames_0) {
  return {$: "task.Checkpoint", "task": {$: "task.Work", "destination": _dest_0, "remaining": _ticks_0, "payload": {$: "task.OwnedWord", "value": _seed_0}, "frames": _frames_0}};
}

function $show_put$(_p_0) {
  if (_p_0.$ === "slot.Inserted") {
    return "inserted";
  } else {
    const _t_0 = _p_0["slot"];
    if (_t_0.$ === "slot.Occupied") {
      const _t_1 = _t_0["value"];
      const _old_0 = _t_1["value"];
      const _t_2 = _p_0["value"];
      const _new_0 = _t_2["value"];
      return $String$concat$({$: "Con", "head": "rejected:", "tail": {$: "Con", "head": ($U32$show$(_old_0)), "tail": {$: "Con", "head": ",", "tail": {$: "Con", "head": ($U32$show$(_new_0)), "tail": {$: "Nil"}}}}});
    } else {
      return "invalid-empty-rejection";
    }
  }
}

function $slot$put$(_s_0, _x_0) {
  if (_s_0.$ === "slot.Vacant") {
    return {$: "slot.Inserted", "slot": {$: "slot.Occupied", "value": _x_0}};
  } else {
    const _value_0 = _s_0["value"];
    return {$: "slot.Rejected", "slot": {$: "slot.Occupied", "value": _value_0}, "value": _x_0};
  }
}

function $show_take$(_p_0) {
  if (_p_0.$ === "slot.Missing") {
    const _t_0 = _p_0["slot"];
    if (_t_0.$ === "slot.Vacant") {
      return "missing";
    } else {
      return "invalid-full-missing";
    }
  } else {
    const _t_1 = _p_0["slot"];
    if (_t_1.$ === "slot.Vacant") {
      const _t_2 = _p_0["value"];
      const _x_0 = _t_2["value"];
      const _x_1 = ($U32$show$(_x_0));
      return ("extracted:" + _x_1);
    } else {
      return "invalid-retained-owner";
    }
  }
}

function $slot$take$(_s_0) {
  if (_s_0.$ === "slot.Vacant") {
    return {$: "slot.Missing", "slot": {$: "slot.Vacant"}};
  } else {
    const _value_0 = _s_0["value"];
    return {$: "slot.Extracted", "slot": {$: "slot.Vacant"}, "value": _value_0};
  }
}

function $slot$put_slot$(_p_0) {
  if (_p_0.$ === "slot.Inserted") {
    const _s_0 = _p_0["slot"];
    return _s_0;
  } else {
    const _s_1 = _p_0["slot"];
    return _s_1;
  }
}

function $slot$take_slot$(_t_0) {
  if (_t_0.$ === "slot.Missing") {
    const _s_0 = _t_0["slot"];
    return _s_0;
  } else {
    const _s_1 = _t_0["slot"];
    return _s_1;
  }
}

function $String$concat$(_xs_0) {
  if (_xs_0.$ === "Nil") {
    return "";
  } else {
    const _h_0 = _xs_0["head"];
    const _t_0 = _xs_0["tail"];
    const _x_0 = ($String$concat$(_t_0));
    return (_h_0 + _x_0);
  }
}

function $U32$show$(_a_0) {
  const _b_0 = _a_0;
  return $U32$show$if$(_b_0, (_b_0 === 0));
}

function $task$observe_payload$(_p_0) {
  const _x_0 = _p_0["value"];
  return _x_0;
}

function $task$step$(_t_0) {
  const _dest_0 = _t_0["destination"];
  const _n_0 = _t_0["remaining"];
  const _p_0 = _t_0["payload"];
  const _frames_0 = _t_0["frames"];
  return $task$step_parts$(_dest_0, _n_0, _p_0, _frames_0);
}

function $U32$show$if$(_a_0, _z_0) {
  if (_z_0) {
    return "0";
  } else {
    return $U32$show$go$(10, _a_0, "");
  }
}

function $task$step_parts$(_dest_0, _n_0, _p_0, _frames_0) {
  if (_n_0 === 0) {
    if (_frames_0.$ === "Nil") {
      return {$: "task.Delivered", "destination": _dest_0, "payload": _p_0};
    } else {
      const _frame_0 = _frames_0["head"];
      const _rest_0 = _frames_0["tail"];
      return {$: "task.Checkpoint", "task": {$: "task.Work", "destination": _dest_0, "remaining": 0, "payload": ($task$apply$(_frame_0, _p_0)), "frames": _rest_0}};
    }
  } else {
    const _k_0 = (_n_0 - 1);
    return {$: "task.Checkpoint", "task": {$: "task.Work", "destination": _dest_0, "remaining": _k_0, "payload": ($task$tick_owned$(_p_0)), "frames": _frames_0}};
  }
}

function $U32$show$go$($0, $1, $2, $3) {
  let $pc = 0;
  for (;;) switch ($pc) {
    case 0: {
      const _f_0 = $0;
      const _n_0 = $1;
      const _acc_0 = $2;
      if (_f_0 === 0) {
        return _acc_0;
      } else {
        const _g_0 = (_f_0 - 1);
        $0 = _g_0;
        $1 = _acc_0;
        $2 = _n_0;
        $3 = (_n_0 === 0);
        $pc = 1; continue;
      }
    }
    case 1: {
      const _g_0 = $0;
      const _acc_0 = $1;
      const _n_0 = $2;
      const _z_0 = $3;
      if (_z_0) {
        return _acc_0;
      } else {
        const _x_0 = (10 === 0 ? _n_0 : _n_0 % 10);
        $0 = _g_0;
        $1 = (10 === 0 ? 0 : (_n_0 / 10) >>> 0);
        $2 = (char_new(((48 + _x_0) >>> 0)) + _acc_0);
        $pc = 0; continue;
      }
    }
  }
}

function $task$tick_owned$(_p_0) {
  const _x_0 = _p_0["value"];
  return {$: "task.OwnedWord", "value": ($task$tick$(_x_0))};
}

function $task$apply$(_frame_0, _value_0) {
  if (_frame_0.$ === "task.Unary") {
    const _factor_0 = _frame_0["factor"];
    const _bias_0 = _frame_0["bias"];
    return $task$unary$(_value_0, _factor_0, _bias_0);
  } else {
    const _left_0 = _frame_0["left"];
    return $task$combine$(_left_0, _value_0);
  }
}

function $U32$show$fin$($0, $1, $2, $3) {
  let $pc = 1;
  for (;;) switch ($pc) {
    case 0: {
      const _f_0 = $0;
      const _n_0 = $1;
      const _acc_0 = $2;
      if (_f_0 === 0) {
        return _acc_0;
      } else {
        const _g_0 = (_f_0 - 1);
        $0 = _g_0;
        $1 = _acc_0;
        $2 = _n_0;
        $3 = (_n_0 === 0);
        $pc = 1; continue;
      }
    }
    case 1: {
      const _g_0 = $0;
      const _acc_0 = $1;
      const _n_0 = $2;
      const _z_0 = $3;
      if (_z_0) {
        return _acc_0;
      } else {
        const _x_0 = (10 === 0 ? _n_0 : _n_0 % 10);
        $0 = _g_0;
        $1 = (10 === 0 ? 0 : (_n_0 / 10) >>> 0);
        $2 = (char_new(((48 + _x_0) >>> 0)) + _acc_0);
        $pc = 0; continue;
      }
    }
  }
}

function $task$tick$(_x_0) {
  const _x_1 = (Math.imul(_x_0, 1664525) >>> 0);
  return ((_x_1 + 1013904223) >>> 0);
}

function $task$unary$(_p_0, _factor_0, _bias_0) {
  const _x_0 = _p_0["value"];
  const _x_1 = (Math.imul(_x_0, _factor_0) >>> 0);
  return {$: "task.OwnedWord", "value": ((_x_1 + _bias_0) >>> 0)};
}

function $task$combine$(_left_0, _right_0) {
  const _a_0 = _left_0["value"];
  const _b_0 = _right_0["value"];
  const _x_0 = (Math.imul(_a_0, 31) >>> 0);
  return {$: "task.OwnedWord", "value": ((_x_0 + _b_0) >>> 0)};
}

// Cli
// ===

// A JS program runs one thread and no GPU: --threads and --gpu do nothing.
let cli_args = [];

function cli(argv) {
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--") {
      cli_args.push(...argv.slice(i + 1));
      break;
    } else if (argv[i] === "--bend-help") {
      io_out(1, io_bytes("usage: " + process.argv[1] + "\n"));
      process.exit(0);
    } else if (argv[i] === "--threads" || argv[i] === "--gpu") {
      i += 1;
    } else {
      cli_args.push(argv[i]);
    }
  }
}

// Show
// ====

// show_val prints a pure main's value as term_show does (see show_main);
// chain is the bracket it continues, or 0. show_chr escapes as char_show.

function show_chr(c, q) {
  const k = { 10: "n", 9: "t", 13: "r", 0: "0", 92: "\\" }[c]
    ?? (c === q.codePointAt(0) ? q : null);
  return k !== null ? "\\" + k : c < 32 || c === 127
    || (c >= 0xD800 && c <= 0xDFFF) || c > 0x10FFFF
    ? "\\u{" + c.toString(16) + "}" : String.fromCodePoint(c);
}

function show_val(D, N, d, v, chain) {
  if (D[d] === 7) {
    const fs = Object.values(typeof v === "boolean"
      ? { $: v ? "True" : "False" } : v);
    let a = d + 3;
    for (; N[D[a]] !== fs[0]; a += 4 + 2 * D[a + 2]) {}
    const o = "{[("[D[a + 3]];
    let s = o === "{" ? fs[0] + "{" : chain === o ? "" : o;
    for (const [j, f] of fs.slice(1).entries()) {
      if (o === "[" ? j === 0 && chain === o : j > 0) {
        s += ", ";
      }
      s += show_val(D, N, D[a + 5 + 2 * j], f, j === 1 && o !== "{" ? o : 0);
    }
    return o === "{" || chain !== o ? s + "}])"[D[a + 3]] : s;
  }
  return D[d] === 0 ? String(v)
    : D[d] === 1 ? f32_show(v).replace(/^-?\d+(?=e|$)/, "$&.0")
    : D[d] === 2 ? v + "n"
    : D[d] === 3 ? "'" + show_chr(v.codePointAt(0), "'") + "'"
    : D[d] === 4 ? "\"" + [...v].map((c) =>
      show_chr(c.codePointAt(0), "\"")).join("") + "\""
    : D[d] === 5 ? "{==}"
    : "[" + v.map((x) => show_val(D, N, D[d + 1], x, 0)).join(", ") + "]";
}

// Io
// ==

// Apple arm64 passes variadic fcntl flags on the stack, so io_sys
// binds fcntl there with the flags as the ninth fixed argument. A
// parked effect waits for fd (a write when out) or until at
// (performance.now()), either one undefined when unused; io_wake
// resumes k with the value of more, and undefined parks it again.

function io_exit(main, show) {
  try {
    if (show !== null) {
      io_out(1, io_bytes(show_val(...show, 0, run_loop(main()), 0) + "\n"));
      process.exit(0);
    }
    process.exit(io_run(main));
  } catch (e) {
    io_errs(String(e));
    process.exit(1);
  }
}

function io_out(fd, data) {
  const fs = require("fs");
  let at = 0;
  while (at < data.length) {
    try {
      at += fs.writeSync(fd, data, at, data.length - at);
    } catch (e) {
      if (e.code === "EAGAIN" || e.code === "EINTR") {
        continue;
      }
      try {
        fs.writeSync(2, "bend: a short write on a standard stream\n");
      } catch (o) {
      }
      process.exit(1);
    }
  }
}

function io_errs(message) {
  io_out(2, io_bytes(message + "\n"));
}

function io_sys() {
  if (globalThis.BEND_SYS === undefined) {
    const ffi = require("bun:ffi");
    const mac = process.platform === "darwin";
    const err = mac ? "__error" : "__errno_location";
    const sel = mac ? "select$DARWIN_EXTSN" : "select";
    const T = { i: "i32", u: "u32", U: "u64", I: "i64", p: "ptr",
      c: "cstring" };
    const vari = mac && process.arch === "arm64";
    const lib = ffi.dlopen(mac ? "libSystem.dylib" : "libc.so.6",
      Object.fromEntries(("socket:iii>i bind:ipu>i listen:ii>i connect:ipu>i"
        + " accept:ipp>i send:ipUi>I recv:ipUi>I read:ipU>I pread:ipUI>I"
        + " sendto:ipUipu>I recvfrom:ipUipp>I close:i>i setsockopt:iiipu>i"
        + " " + sel + ":ipppp>i"
        + (vari ? " fcntl:iiiiiiiii>i" : " fcntl:iii>i") + " getsockopt:iiipp>i"
        + " strerror:i>c " + err + ":>p").split(" ").map((s) => {
        const [name, args, ret] = s.split(/[:>]/);
        return [name, { args: [...args].map((a) => T[a]), returns: T[ret] }];
      }))).symbols;
    const fcntl = (fd, cmd, arg) => vari
      ? lib.fcntl(fd, cmd, 0, 0, 0, 0, 0, 0, arg)
      : lib.fcntl(fd, cmd, arg);
    globalThis.BEND_SYS = { ...lib, fcntl, select: lib[sel],
      ptr: ffi.ptr, mac,
      errno: () => ffi.read.i32(lib[err](), 0) };
  }
  return globalThis.BEND_SYS;
}

function io_fail(code) {
  return { $: "Fail",
    error: io_tup(code >>> 0, String(io_sys().strerror(code))) };
}

function io_done(value) {
  return { $: "Done", value };
}

function io_tup(...xs) {
  return xs.reduceRight((snd, fst) => ({ $: "Tuple", fst, snd }));
}

function io_bytes(text) {
  return new TextEncoder().encode(text);
}

function io_text(b, n) {
  return new TextDecoder("utf-8", { ignoreBOM: true }).decode(b.subarray(0, n));
}

function io_addr(host, port) {
  const part = host.split(".");
  const deci = (p) => /^(0|[1-9]\d{0,2})$/.test(p) && Number(p) < 256;
  if (port > 65535 || part.length !== 4 || !part.every(deci)) {
    return null;
  }
  const b = new Uint8Array(16);
  const head = io_sys().mac ? [16, 2] : [2, 0];
  b.set([...head, port >> 8, port & 255, ...part.map(Number)]);
  return b;
}

function io_push(fun, arg, fresh) {
  const io = globalThis.BEND_IO;
  io.runs.push({ fun, arg });
  io.live += fresh ? 1 : 0;
}

function io_wait(io) {
  const soon = io.waits.reduce((m, w) => Math.min(m, w.at ?? m), Infinity);
  const ms = soon === Infinity ? -1
    : Math.max(0, Math.ceil(soon - performance.now()));
  const fds = io.waits.filter((w) => w.fd !== undefined);
  const top = fds.reduce((m, w) => Math.max(m, w.fd), 0);
  const len = (top >> 6 << 3) + 8;
  const set = new Uint8Array(2 * len);
  const at = (w) => (w.out ? len : 0) + (w.fd >> 3);
  for (const w of fds) {
    set[at(w)] |= 1 << (w.fd & 7);
  }
  const tv = new BigInt64Array([BigInt(ms / 1000 | 0),
    BigInt(ms % 1000 * 1000)]);
  const sys = io_sys();
  if (sys.select(top + 1, sys.ptr(set), sys.ptr(set, len), null,
    ms < 0 ? null : sys.ptr(tv)) < 0) {
    if (sys.errno() !== 4) {
      throw "bend: the poller failed";
    }
    set.fill(0);
  }
  const now = performance.now();
  io.waits = io.waits.filter((w) => {
    const ready = w.at <= now || w.fd !== undefined
      && set[at(w)] & 1 << (w.fd & 7);
    if (ready) {
      io_push(io_wake, w, false);
    }
    return !ready;
  });
}

function io_wake(w) {
  const x = w.more();
  return x === undefined ? undefined : w.k(x);
}

function io_park_on(fd, out, k, more, at) {
  globalThis.BEND_IO.waits.push({ fd, out, k, more, at });
}

function io_run(m) {
  const io = { runs: [], live: 0, waits: [] };
  globalThis.BEND_IO = io;
  try {
    io_push(run_loop(m()), (x) => ({ $: "Emit", value: x }), true);
    for (;;) {
      if (io.runs.length === 0) {
        if (io.live === 0) {
          return 0;
        }
        if (io.waits.length === 0) {
          io_errs("bend: deadlock: every computation waits on a channel");
          return 1;
        }
        io_wait(io);
        continue;
      }
      const s = io.runs.shift();
      let op = s.fun(s.arg);
      while (op !== undefined) {
        if (op.$ === "Emit") {
          io.live -= 1;
          break;
        }
        if (op.$ === "Halt") {
          io_errs(op.message);
          return op.code;
        }
        const need = op.need?.() ?? {};
        if (need.time || need.read) {
          const more = () => op.run(...op.args, op.kont);
          io_park_on(need.read ? op.args[0] : undefined, false, op.kont, more,
            need.read ? undefined : performance.now() + Number(op.args[0]));
          break;
        }
        const x = op.run(...op.args, op.kont);
        if (x === undefined) {
          break;
        }
        op = op.kont(x);
      }
    }
  } catch (req) {
    if (req instanceof RangeError) {
      throw "bend: memory fault (machine stack overflow?)";
    }
    if (req?.$ !== "$FFI") {
      throw req;
    }
    io_errs("bend: runtime fail-stop");
    return 1;
  }
}

cli(process.argv.slice(2));
io_exit($main$, null);