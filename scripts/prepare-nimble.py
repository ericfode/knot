#!/usr/bin/env python3
"""Merge the pinned Nimble adapter on CPU using its published preparation recipe."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / ".local/nimble"
PIN = json.loads((ROOT / "tools/local-models/pins.json").read_text())["nimble"]
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
sys.path.insert(0, str(DIRECTORY / "repo"))


def main():
    import torch
    from peft import PeftModel
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    from nimble.training.candidate_schema import validate_contract
    adapter, destination = DIRECTORY / "adapter", DIRECTORY / "model"
    if destination.exists():
        raise FileExistsError("Refusing to replace an existing merged model")
    adapter_hash = hashlib.sha256((adapter / "adapter_model.safetensors").read_bytes()).hexdigest()
    if adapter_hash != PIN["adapter_sha256"]:
        raise ValueError("Adapter weights differ from the published pin")
    contract = json.loads((adapter / "schema_config.json").read_text())
    if (contract["model"], contract["revision"]) != (PIN["base"], PIN["base_revision"]):
        raise ValueError("Adapter base does not match the pin")
    tokenizer = AutoTokenizer.from_pretrained(adapter, local_files_only=True)
    validate_contract(contract, tokenizer)
    torch.set_num_threads(8)
    base = Qwen3_5ForConditionalGeneration.from_pretrained(
        DIRECTORY / "base", dtype=torch.bfloat16, device_map="cpu", local_files_only=True)
    trained = PeftModel.from_pretrained(base, adapter, local_files_only=True)
    merged = trained.merge_and_unload(safe_merge=True)
    merged.save_pretrained(destination)
    tokenizer.save_pretrained(destination)
    shutil.copy2(adapter / "schema_config.json", destination / "schema_config.json")
    (destination / "READY.json").write_text(json.dumps({
        "model": PIN["repo"], "revision": PIN["revision"], "base": PIN["base"],
        "base_revision": PIN["base_revision"], "adapter_sha256": adapter_hash,
    }, indent=2) + "\n")
    print("Merged:", destination)


if __name__ == "__main__":
    main()
