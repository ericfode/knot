#!/usr/bin/env python3
"""Pack Φ prompts behind 🪢 using FRV1T's variation-selector envelope."""

import argparse
import gzip
from pathlib import Path
import sys


MARKER = b"\x0fFRV2"
CARRIER = "🪢"
LEGACY_CARRIER = "🫐"


def encode(payload: bytes) -> str:
    payload.decode("utf-8")
    packed = MARKER + gzip.compress(payload, mtime=0)
    selectors = "".join(
        chr(0xFE00 + byte) if byte < 16 else chr(0xE0100 + byte - 16)
        for byte in packed
    )
    return CARRIER + selectors + "\n"


def decode(envelope: str) -> bytes:
    envelope = envelope.removesuffix("\n")
    carrier = next(
        (mark for mark in (CARRIER, LEGACY_CARRIER) if envelope.startswith(mark)),
        None,
    )
    if carrier is None:
        raise ValueError("Missing knot or legacy blueberry marker")
    packed = bytearray()
    for char in envelope[len(carrier):]:
        point = ord(char)
        if 0xFE00 <= point <= 0xFE0F:
            packed.append(point - 0xFE00)
        elif 0xE0100 <= point <= 0xE01EF:
            packed.append(point - 0xE0100 + 16)
        else:
            raise ValueError("Unexpected character outside variation-selector ranges")
    if not packed.startswith(MARKER):
        raise ValueError("Missing FRV2 header")
    payload = gzip.decompress(packed[len(MARKER):])
    payload.decode("utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["encode", "decode"])
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, nargs="?")
    args = parser.parse_args()
    if args.operation == "encode":
        result = encode(args.source.read_bytes()).encode("utf-8")
    else:
        result = decode(args.source.read_text(encoding="utf-8"))
    if args.destination is None:
        sys.stdout.buffer.write(result)
    else:
        args.destination.write_bytes(result)


if __name__ == "__main__":
    main()
