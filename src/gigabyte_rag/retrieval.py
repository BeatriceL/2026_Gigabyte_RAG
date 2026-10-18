
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "data/processed/vector_index.json"

API = "http://127.0.0.1:8081/v1/embeddings"
MODEL = "Qwen3-Embedding-0.6B"
SOURCE_URL = "https://www.gigabyte.com/tw/Laptop/AORUS-MASTER-16-AM6H/sp"
ALLOWED_MODELS = {"BZH", "BYH", "BXH"}


def embed(text):
    payload = json.dumps({
        "model": MODEL,
        "input": text
    }).encode("utf-8")

    request = urllib.request.Request(
        API,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)

    vector = result["data"][0]["embedding"]

    if len(vector) != 1024:
        raise ValueError("Unexpected embedding dimension")

    return vector


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def retrieve(query, top_k=3):
    index = json.loads(INDEX.read_text(encoding="utf-8"))

    match = re.search(
        r"(?<![A-Z0-9])(BZH|BYH|BXH)(?![A-Z0-9])",
        query.upper()
    )
    target_model = match.group(1) if match else None

    # Retrieval Filtering: source and product scope
    allowed = [
        chunk for chunk in index
        if chunk["source_url"] == SOURCE_URL
        and chunk["model_code"] in ALLOWED_MODELS
        and (
            target_model is None
            or chunk["model_code"] == target_model
        )
    ]

    if not allowed:
        return []

    query_vector = embed(query)

    results = []

    for chunk in allowed:
        score = cosine_similarity(
            query_vector,
            chunk["embedding"]
        )

        results.append({
            "chunk_id": chunk["chunk_id"],
            "model_code": chunk["model_code"],
            "category": chunk["category"],
            "text": chunk["text"],
            "source_url": chunk["source_url"],
            "score": score
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])

    if not query:
        raise SystemExit(
            'Usage: uv run python src/gigabyte_rag/retrieval.py "問題"'
        )

    print(f"Question: {query}")

    for rank, result in enumerate(retrieve(query), 1):
        print(f"\n=== Rank {rank} ===")
        print("Model:", result["model_code"])
        print("Category:", result["category"])
        print("Similarity:", round(result["score"], 4))
        print("Content:", result["text"][:250])

