import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "gigabyte_rag"))

from field_intent import detect_fields
from hybrid_retrieval import retrieve_hybrid

MODELS = ["BZH", "BYH", "BXH"]

FIELDS = [
    ("中央處理器", "處理器", "CPU"),
    ("顯示晶片", "顯示卡", "GPU"),
    ("顯示器", "螢幕", "screen"),
    ("記憶體", "記憶體", "RAM"),
    ("儲存裝置", "SSD", "SSD"),
]

chunks = [
    json.loads(line)
    for line in (
        ROOT / "data/processed/chunks.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    if line.strip()
]

ground_truth = {
    (chunk["model_code"], chunk["category"]): chunk["chunk_id"]
    for chunk in chunks
}

KS = [1, 3, 5]
scores = {
    method: {k: 0 for k in KS}
    for method in ["Semantic", "Hybrid"]
}

failures = []
total = 0

for model in MODELS:
    for category, zh_alias, en_alias in FIELDS:
        expected = ground_truth[(model, category)]

        questions = [
            f"AORUS MASTER 16 AM6H {model} 的{zh_alias}規格是什麼？",
            f"What are the {en_alias} specifications of AORUS MASTER 16 AM6H {model}?",
        ]

        for question in questions:
            detected = detect_fields(question)

            if detected != [category]:
                raise ValueError(
                    f"Unexpected field detection: {question} -> {detected}"
                )

            # One embedding call; both methods share identical candidates.
            results = retrieve_hybrid(question, top_k=51)

            semantic = sorted(
                results,
                key=lambda item: item["semantic_score"],
                reverse=True,
            )

            rankings = {
                "Semantic": [item["chunk_id"] for item in semantic],
                "Hybrid": [item["chunk_id"] for item in results],
            }

            total += 1

            for method, ranked_ids in rankings.items():
                for k in KS:
                    if expected in ranked_ids[:k]:
                        scores[method][k] += 1
                    elif k == 5:
                        failures.append(
                            (method, question, expected, ranked_ids[:5])
                        )

print("=== RETRIEVAL RECALL@K ===")
print("Questions:", total)
print("Models:", ", ".join(MODELS))
print("Fields:", len(FIELDS))
print()

for method in ["Semantic", "Hybrid"]:
    print(method)
    for k in KS:
        count = scores[method][k]
        print(f"  Recall@{k}: {count}/{total} ({count / total:.1%})")

print("\n=== RECALL@5 FAILURES ===")

if failures:
    for method, question, expected, retrieved in failures:
        print(f"[{method}] {question}")
        print("  Expected:", expected)
        print("  Retrieved:", retrieved)
else:
    print("No Recall@5 failures.")
