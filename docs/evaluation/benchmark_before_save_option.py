
import ast
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "gigabyte_rag"))

from moderation import moderate_input

# Read test cases without executing the old evaluation script.
source = (ROOT / "eval_moderation.py").read_text(
    encoding="utf-8"
)
tree = ast.parse(source)

case_assignment = next(
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name)
        and target.id == "CASES"
        for target in node.targets
    )
)

cases = ast.literal_eval(case_assignment.value)

expected_categories = {
    "NORMAL": "PRODUCT_QUERY",
    "COMPETITOR": "COMPETITOR_QUERY",
    "SENSITIVE": "SENSITIVE_TOPIC",
    "INJECTION": "PROMPT_INJECTION",
    "OUT_OF_SCOPE": "OUT_OF_SCOPE",
}

REPEATS = 30
results = []

for group, question, expected_decision in cases:
    # One warm-up invocation per question.
    moderate_input(question)

    latencies = []
    actual = None

    for _ in range(REPEATS):
        start = time.perf_counter_ns()
        actual = moderate_input(question)
        elapsed_ms = (
            time.perf_counter_ns() - start
        ) / 1_000_000
        latencies.append(elapsed_ms)

    expected_category = expected_categories[group]

    passed = (
        actual["decision"] == expected_decision
        and actual["category"] == expected_category
    )

    results.append({
        "group": group,
        "question": question,
        "expected_decision": expected_decision,
        "expected_category": expected_category,
        "actual": actual,
        "passed": passed,
        "latencies_ms": latencies,
    })

def ratio(numerator, denominator):
    return round(numerator / denominator * 100, 2) if denominator else None

def latency_stats(values):
    sorted_values = sorted(values)
    p95_index = math.ceil(0.95 * len(sorted_values)) - 1

    return {
        "mean_ms": round(statistics.mean(values), 3),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": round(sorted_values[p95_index], 3),
    }

allowed = [r for r in results if r["expected_decision"] == "ALLOW"]
refused = [r for r in results if r["expected_decision"] == "REFUSE"]
redirected = [r for r in results if r["expected_decision"] == "REDIRECT"]

true_refuses = sum(
    r["actual"]["decision"] == "REFUSE" for r in refused
)

false_blocks = sum(
    r["actual"]["decision"] != "ALLOW" for r in allowed
)

correct_redirects = sum(
    r["actual"]["decision"] == "REDIRECT" for r in redirected
)

correct = sum(r["passed"] for r in results)
all_latencies = [
    value
    for result in results
    for value in result["latencies_ms"]
]

summary = {
    "total_cases": len(results),
    "correct_decision_and_category": correct,
    "accuracy_pct": ratio(correct, len(results)),
    "refusal_tpr_pct": ratio(true_refuses, len(refused)),
    "normal_false_block_fpr_pct": ratio(false_blocks, len(allowed)),
    "out_of_scope_redirect_pct": ratio(
        correct_redirects, len(redirected)
    ),
    "latency": latency_stats(all_latencies),
}

report = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "suite": "Existing 16-case development/regression set",
    "repeats_per_case": REPEATS,
    "summary": summary,
    "results": results,
}

output = ROOT / "docs/evaluation" / (
    "input_moderation_benchmark_"
    + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    + ".json"
)
output.parent.mkdir(parents=True, exist_ok=True)

# Exclusive creation prevents overwriting existing results.
with output.open("x", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("=== INPUT MODERATION BENCHMARK ===")
print(f"Accuracy: {correct}/{len(results)} ({summary['accuracy_pct']}%)")
print("Refusal TPR:", summary["refusal_tpr_pct"], "%")
print("Normal False-Block FPR:", summary["normal_false_block_fpr_pct"], "%")
print("Out-of-Scope Redirect:", summary["out_of_scope_redirect_pct"], "%")

print("\n=== LATENCY ===")
for key, value in summary["latency"].items():
    print(f"{key}: {value} ms")

print("\n=== FAILED CASES ===")
failures = [r for r in results if not r["passed"]]

if not failures:
    print("No failures.")

for r in failures:
    print("Question:", r["question"])
    print("Expected:", r["expected_decision"], r["expected_category"])
    print("Actual:", r["actual"]["decision"], r["actual"]["category"])
    print()

print("Saved:", output)

