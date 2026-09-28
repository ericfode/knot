import Base

# SHA-256 of 65,536 ASCII bytes ('a' + i mod 26). The compression function is
# modules' base-pin.bend verbatim; only its input and output wrappers differ.
type Digest is Data:
  Digest{a: U32, b: U32, c: U32, d: U32, e: U32, f: U32, g: U32, h: U32}

type Packing is Data:
  Packing{left: Nat, reversed: List<&2,U32>, state: Digest}

def initial() -> Digest:
  Digest{1779033703,3144134277,1013904242,2773480762,1359893119,2600822924,528734635,1541459225}

def constants() -> List<&2,U32>:
  [1116352408,1899447441,3049323471,3921009573,961987163,1508970993,2453635748,2870763221,
   3624381080,310598401,607225278,1426881987,1925078388,2162078206,2614888103,3248222580,
   3835390401,4022224774,264347078,604807628,770255983,1249150122,1555081692,1996064986,
   2554220882,2821834349,2952996808,3210313671,3336571891,3584528711,113926993,338241895,
   666307205,773529912,1294757372,1396182291,1695183700,1986661051,2177026350,2456956037,
   2730485921,2820302411,3259730800,3345764771,3516065817,3600352804,4094571909,275423344,
   430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,
   1955562222,2024104815,2227730452,2361852424,2428436474,2756734187,3204031479,3329325298]

def rotate(+word: U32, right: Nat, left: Nat) -> U32:
  U32.or(U32.shrn(word,right),U32.shln(word,left))

def sum0(+word: U32) -> U32:
  U32.xor(rotate(word,2n,30n),U32.xor(rotate(word,13n,19n),rotate(word,22n,10n)))

def sum1(+word: U32) -> U32:
  U32.xor(rotate(word,6n,26n),U32.xor(rotate(word,11n,21n),rotate(word,25n,7n)))

def sigma0(+word: U32) -> U32:
  U32.xor(rotate(word,7n,25n),U32.xor(rotate(word,18n,14n),U32.shrn(word,3n)))

def sigma1(+word: U32) -> U32:
  U32.xor(rotate(word,17n,15n),U32.xor(rotate(word,19n,13n),U32.shrn(word,10n)))

def choose(+x: U32, y: U32, z: U32) -> U32:
  U32.xor(U32.and(x,y),U32.and(U32.not(x),z))

def majority(+x: U32, +y: U32, +z: U32) -> U32:
  U32.xor(U32.and(x,y),U32.xor(U32.and(x,z),U32.and(y,z)))

def nth(index: Nat, words: List<&2,U32>) -> U32:
  match index words:
    case _ Nil{}: 0
    case 0n Con{word,tail}: word
    case 1n+n Con{word,tail}: nth(n,tail)

# The schedule is reversed: offsets 1,6,14,15 are t-2,t-7,t-15,t-16.
def schedule(fuel: Nat, +reversed: List<&2,U32>) -> List<&2,U32>:
  match fuel:
    case 0n: List.reverse(&2,U32,reversed)
    case 1n+n:
      word = U32.add(U32.add(sigma1(nth(1n,reversed)),nth(6n,reversed)),U32.add(sigma0(nth(14n,reversed)),nth(15n,reversed)))
      schedule(n,Con{word,reversed})

def round(word: U32, constant: U32, state: Digest) -> Digest:
  match state:
    case Digest{+a,+b,+c,d,+e,+f,+g,h}:
      +t1 = U32.add(U32.add(U32.add(h,sum1(e)),choose(e,f,g)),U32.add(constant,word))
      t2 = U32.add(sum0(a),majority(a,b,c))
      Digest{U32.add(t1,t2),a,b,c,U32.add(d,t1),e,f,g}

def rounds(words: List<&2,U32>, keys: List<&2,U32>, state: Digest) -> Digest:
  match words keys:
    case Con{word,rest} Con{key,tail}: rounds(rest,tail,round(word,key,state))
    case _ _: state

def add(left: Digest, right: Digest) -> Digest:
  match left right:
    case Digest{a,b,c,d,e,f,g,h} Digest{i,j,k,l,m,n,o,p}:
      Digest{U32.add(a,i),U32.add(b,j),U32.add(c,k),U32.add(d,l),U32.add(e,m),U32.add(f,n),U32.add(g,o),U32.add(h,p)}

def compress(reversed: List<&2,U32>, +state: Digest) -> Digest:
  add(state,rounds(schedule(48n,reversed),constants(),state))

def word(a: U32, b: U32, c: U32, d: U32) -> U32:
  U32.or(U32.shln(a,24n),U32.or(U32.shln(b,16n),U32.or(U32.shln(c,8n),d)))

def absorb(packing: Packing, word: U32) -> Packing:
  match packing:
    case Packing{1n+0n,reversed,state}: Packing{16n,Nil{},compress(Con{word,reversed},state)}
    case Packing{1n+(1n+n),reversed,state}: Packing{1n+n,Con{word,reversed},state}
    case Packing{0n,reversed,state}: Packing{0n,reversed,state}

def unpack(packing: Packing) -> Digest:
  match packing:
    case Packing{left,reversed,state}: state

def blocks(bytes: List<&2,U32>, packing: Packing) -> Digest:
  match bytes:
    case Con{a,Con{b,Con{c,Con{d,tail}}}}:
      blocks(tail,absorb(packing,word(a,b,c,d)))
    case _: unpack(packing)

def octets(+value: U32) -> List<&2,U32>:
  [U32.shrn(value,24n),U32.and(U32.shrn(value,16n),255),U32.and(U32.shrn(value,8n),255),U32.and(value,255)]

def zeros(count: Nat, tail: List<&2,U32>) -> List<&2,U32>:
  match count:
    case 0n: tail
    case 1n+n: zeros(n,Con{0,tail})

# The input is far below 2^29 bytes, so the high length word is 0.
def padded(+size: U32, reversed: List<&2,U32>) -> List<&2,U32>:
  padding = U32.to_nat(U32.mod(U32.sub(119,U32.mod(size,64)),64))
  List.reverse.go(&2,U32,reversed,Con{128,zeros(padding,List.append(&2,U32,[0,0,0,0],octets(U32.mul(size,8))))})

def nibble(+value: U32) -> Char:
  Char.from_u32(U32.add(value,Bool.pick(U32,U32.is_lt(value,10),48,87)))

def hex_word(left: Nat, +value: U32, text: String) -> String:
  match left:
    case 0n: text
    case 1n+n: hex_word(n,U32.shrn(value,4n),SCon{nibble(U32.and(value,15)),text})

def show(value: Digest) -> String:
  match value:
    case Digest{a,b,c,d,e,f,g,h}:
      String.concat([hex_word(8n,a,""),hex_word(8n,b,""),hex_word(8n,c,""),hex_word(8n,d,""),
        hex_word(8n,e,""),hex_word(8n,f,""),hex_word(8n,g,""),hex_word(8n,h,"")])

# Reversed input: the last byte first, as padded expects.
def input(n: Nat, +i: U32, acc: List<&2,U32>) -> List<&2,U32>:
  match n:
    case 0n: acc
    case 1n+p: input(p,U32.add(i,1),Con{U32.add(97,U32.mod(i,26)),acc})

# The expected digest is Python's hashlib.sha256 of the same 65,536 bytes.
def main() -> Bool:
  String.eq(show(blocks(padded(65536,input(65536n,0,Nil{})),Packing{16n,Nil{},initial()})),
    "62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f")
