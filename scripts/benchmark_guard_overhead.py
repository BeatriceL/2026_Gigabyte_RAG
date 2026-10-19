import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "gigabyte_rag"))

from field_intent import detect_fields
from hybrid_retrieval import retrieve_hybrid
from moderation import moderate_input
from retrieval_filter import filter_evidence
from generation_guard import prepare_generation
from output_guard import moderate_output

QUESTION = "AORUS MASTER 16 AM6H BZH 的 GPU 規格是什麼？"
MODEL = "BZH"
ANSWER = (
    "AORUS MASTER 16 AM6H BZH 搭載 NVIDIA GeForce "
    "RTX 5090 Laptop GPU，配備 24GB GDDR7 顯示記憶體，"
    "最高 GPU 功耗為 175W。"
)
STAGES = ["INPUT", "RETRIEVAL", "GENERATION", "OUTPUT"]
WARMUP = 5
RUNS = 100

fields = set(detect_fields(QUESTION))
candidates = retrieve_hybrid(QUESTION, top_k=51)
approved_evidence, _ = filter_evidence(candidates, MODEL, fields)
approved_guard = prepare_generation(
    QUESTION, MODEL, fields, approved_evidence
)

assert approved_evidence
assert approved_guard["decision"] == "ALLOW"
assert moderate_output(ANSWER, approved_evidence)["decision"] == "ALLOW"


def run_once(enabled):
    t0 = time.perf_counter_ns()

    if enabled:
        input_result = moderate_input(QUESTION)
    else:
        input_result = {"decision": "ALLOW"}
    t1 = time.perf_counter_ns()

    if enabled:
        evidence, _ = filter_evidence(candidates, MODEL, fields)
    else:
        evidence = approved_evidence
    t2 = time.perf_counter_ns()

    if enabled:
        guard = prepare_generation(QUESTION, MODEL, fields, evidence)
    else:
        guard = approved_guard
    t3 = time.perf_counter_ns()

    if enabled:
        output = moderate_output(ANSWER, evidence)
    else:
        output = {"decision": "ALLOW"}
    t4 = time.perf_counter_ns()

    assert input_result["decision"] == "ALLOW"
    assert guard["decision"] == "ALLOW"
    assert output["decision"] == "ALLOW"
    assert [e["chunk_id"] for e in evidence] == [
        e["chunk_id"] for e in approved_evidence
    ]

    timestamps = [t0, t1, t2, t3, t4]
    return [
        (timestamps[i + 1] - timestamps[i]) / 1_000_000
        for i in range(4)
    ]


def summarize(values):
    ordered = sorted(values)
    return {
        "mean_ms": round(statistics.mean(values), 5),
        "median_ms": round(statistics.median(values), 5),
        "p95_ms": round(ordered[int(0.95 * len(ordered)) - 1], 5),
    }


on_runs = []
off_runs = []

for i in range(WARMUP + RUNS):
    order = [True, False] if i % 2 == 0 else [False, True]

    results = {enabled: run_once(enabled) for enabled in order}

    if i >= WARMUP:
        on_runs.append(results[True])
        off_runs.append(results[False])

on_totals = [sum(row) for row in on_runs]
off_totals = [sum(row) for row in off_runs]

report = {
    "benchmark": "fixed-input guard function overhead",
    "warmup": WARMUP,
    "measured_runs": RUNS,
    "question": QUESTION,
    "evidence_ids": [e["chunk_id"] for e in approved_evidence],
    "excludes": ["embedding", "retrieval", "LLM", "audit", "I/O"],
    "guard_on_total": summarize(on_totals),
    "guard_off_passthrough": summarize(off_totals),
    "guard_on_stages": {
        stage: summarize([row[i] for row in on_runs])
        for i, stage in enumerate(STAGES)
    },
}

print("=== FIXED-INPUT GUARD MICROBENCHMARK ===")
print("Warmup:", WARMUP, "| Measured:", RUNS)
print("Evidence:", report["evidence_ids"])
print("Guard ON:", report["guard_on_total"])
print("Guard OFF (pass-through):", report["guard_off_passthrough"])
print("\n=== GUARD ON BY STAGE ===")

for stage, result in report["guard_on_stages"].items():
    print(stage, result)

if "--save" in sys.argv[1:]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "docs" / "evaluation" / (
        f"guard_microbenchmark_{timestamp}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nSaved:", output)
else:
    print("\nResults not saved. Use --save to export JSON.")
