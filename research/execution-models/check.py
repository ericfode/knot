#!/usr/bin/env python3
"""Drive Bend checks; all protocol semantics and witnesses live in Bend.

No network, package edits, publication, or GPU-performance claims. Mutants are
isolated temporary copies. A type error in a mutant model is NOT a killed mutant.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BEND = ROOT / "scripts/bend-reference"
PIN = "574b6d39a235b539eb19a5c532993a0abb3d11ad"
FILES = ["model.bend", "LAWS.bend", "PROOF.bend", "conformance.bend", "check.py", "reference-hashes.json"]
EXPECTED = "\n".join([
    "7,9", "7,9", "rejected:left:7", "rejected:right:9",
    "yield:7,9;taken", "denied:taken", "waiting:left:7", "waiting:right:9",
    "waiting:open", "yield:0,4294967295;taken", "",
])


def run(args):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, text=True,
                       capture_output=True, timeout=60)
    return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def checked(result):
    assert result["exit"] == 0 and "All terms check." in result["stdout"], result


def main():
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_commit": PIN,
        "scope": "Abstract sequential Data-payload join, not a concrete runtime refinement",
        "hashes": {f: sha256((HERE / f).read_bytes()).hexdigest() for f in FILES},
        "law_count": sum(line.startswith("law ") for line in (HERE / "LAWS.bend").read_text().splitlines()),
    }
    reference = json.loads((HERE / "reference-hashes.json").read_text())
    assert reference["commit"] == PIN
    for f, digest in reference["files"].items():
        actual = sha256((ROOT / ".toolchain/bend-2.0.29-574b6d3" / f).read_bytes()).hexdigest()
        assert actual == digest, f
    report["reference_core_hashes_verified"] = reference["files"]
    report["proof_check"] = run([BEND, HERE / "PROOF.bend"])
    checked(report["proof_check"])
    report["js_fixture"] = run([BEND, HERE / "conformance.bend"])
    assert report["js_fixture"]["exit"] == 0 and report["js_fixture"]["stdout"] == EXPECTED, report["js_fixture"]
    original = (HERE / "model.bend").read_text()
    mutations = [
        ("swap_result_slots", "finish_right", "left=7, right=9 must deliver (7,9)",
         "case JLeft{value}:\n      JAccept{JReady{value, x}}",
         "case JLeft{value}:\n      JAccept{JReady{x, value}}"),
        ("overwrite_duplicate", "duplicate_left", "left=7 then left=9 must reject and retain 7",
         "case JLeft{value}:\n      JReject{JLeft{value}}",
         "case JLeft{value}:\n      JAccept{JLeft{x}}"),
        ("allow_second_take", "take_ready", "take (7,9) twice must deny the second take",
         "case JReady{left, right}: JYield{JTaken{}, left, right}",
         "case JReady{+left, +right}: JYield{JReady{left,right}, left, right}"),
        ("finish_without_right", "take_left", "take left=7 while right absent must wait",
         "case JLeft{value}: JWait{JLeft{value}}",
         "case JLeft{+value}: JYield{JTaken{},value,value}"),
    ]
    report["mutants"] = []
    with tempfile.TemporaryDirectory(prefix="knot-join-laws-") as td:
        tmp = Path(td)
        report["native_build"] = run([BEND, HERE / "conformance.bend", "-o", tmp / "conformance"])
        assert report["native_build"]["exit"] == 0, report["native_build"]
        report["native_fixture"] = run([tmp / "conformance"])
        assert report["native_fixture"]["exit"] == 0 and report["native_fixture"]["stdout"] == EXPECTED, report["native_fixture"]
        for name, law, witness, old, new in mutations:
            assert original.count(old) == 1, name
            folder = tmp / name
            folder.mkdir()
            for f in FILES[:4]:
                shutil.copy2(HERE / f, folder / f)
            (folder / "model.bend").write_text(original.replace(old, new))
            model_check = run([BEND, folder / "model.bend"])
            checked(model_check)
            proof_check = run([BEND, folder / "PROOF.bend"])
            diagnostic = proof_check["stdout"] + proof_check["stderr"]
            assert proof_check["exit"] != 0 and law in diagnostic and "expected" in diagnostic and "observed" in diagnostic, proof_check
            fixture = run([BEND, folder / "conformance.bend"])
            assert fixture["exit"] == 0 and fixture["stdout"] != EXPECTED, fixture
            report["mutants"].append({
                "name": name, "witness": witness, "law": law,
                "model_typechecks": True, "proof_rejected": True,
                "runtime_witness_differs": True,
                "diagnostic": diagnostic, "witness_stdout": fixture["stdout"],
            })
    report["status"] = "pass"
    (HERE / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {report['law_count']} Bend laws; JS and native fixtures; {len(mutations)} type-valid semantic mutants rejected.")
    print("No Wasm, WebGPU, allocator, concurrent-memory, or scheduler implementation was tested.")


if __name__ == "__main__":
    main()
