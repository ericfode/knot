#!/usr/bin/env python3
"""Summarize complete frozen-control receipts; never tune the decision threshold."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
FAMILY_QUESTION = {"growing-prefix-copy": "prefix_copy", "invariant-summary": "invariant_work",
                   "indexed-linked-list": "linked_index"}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def summarize(report, requests):
    if report["input_sha256"] != digest(requests):
        raise ValueError("Receipt does not use the frozen input")
    if [r["id"] for r in report["rows"]] != [r["id"] for r in requests]:
        raise ValueError("Receipt is incomplete or reordered")
    narrow, full, sanity, style = [], [], [], []
    for row, request in zip(report["rows"], requests):
        if row["status"] != "inferred":
            raise ValueError("Not every request completed inference")
        if row["input_sha256"] != digest({k: request[k] for k in ("state", "questions")}):
            raise ValueError("Per-request input differs")
        answers = row["result"]["answers"]
        if set(answers) != set(request["questions"]):
            raise ValueError("Missing answers")
        if request.get("phase") == "native-narrow":
            p = answers[FAMILY_QUESTION[request["family"]]]["noul"]
            expected = "broken" in request["label"]
            narrow.append({"id": row["id"], "family": request["family"], "label": request["label"],
                           "probability_defect": p, "expected_defect": expected,
                           "predicted_defect": p >= .5, "correct": (p >= .5) == expected})
        elif request.get("phase") == "full-rule":
            p = answers["prefix"]["noul"]
            expected = "broken" not in request["label"]
            full.append({"id": row["id"], "probability_requirement_holds": p,
                         "correct": (p >= .5) == expected})
        elif row["id"].startswith("sanity-"):
            sanity.append({"id": row["id"], "answers": answers})
        elif row["id"] == "unchanged-style-rubrics":
            for name, answer in answers.items():
                p = answer["probabilities"]
                style.append({"axis": name, "mean": answer["score"], "probabilities": p,
                              "probability_level_at_least_3": sum(v for k, v in p.items() if int(k) >= 3),
                              "frozen_target": .6})
    if len(narrow) != 8 or len(full) != 4 or len(style) != 3:
        raise ValueError("Wrong control coverage")
    timings = [row["elapsed_ms"] for row in report["rows"] if row.get("phase") == "native-narrow"]
    return {"model": report["model"], "input_sha256": report["input_sha256"],
            "threshold": .5, "threshold_tuned": False, "narrow": {
                "correct": sum(r["correct"] for r in narrow), "total": len(narrow),
                "false_positives": sum(r["predicted_defect"] and not r["expected_defect"] for r in narrow),
                "false_negatives": sum(not r["predicted_defect"] and r["expected_defect"] for r in narrow),
                "rows": narrow}, "full_rule": {"correct": sum(r["correct"] for r in full), "total": len(full), "rows": full},
            "sanity": sanity, "frozen_style": style,
            "timings_ms": {"load": report["load_ms"], "first_request": report["rows"][0]["elapsed_ms"],
                           "narrow_min": min(timings), "narrow_median": statistics.median(timings),
                           "narrow_max": max(timings)},
            "promoted_to_default": False,
            "limits": "Eight correlated controls; previously exposed during Laya development. Not fresh qualification, calibration, a current style campaign gate, or a controlled throughput benchmark."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    requests = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())
    comparisons = [summarize(json.loads(path.read_text()), requests) for path in args.receipts]
    with args.output.open("x") as output:
        json.dump(comparisons, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
