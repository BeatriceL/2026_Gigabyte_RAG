
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/chunks.jsonl"
OUTPUT = ROOT / "data/processed/vector_index.json"

API = "http://127.0.0.1:8081/v1/embeddings"
MODEL = "Qwen3-Embedding-0.6B"
OFFICIAL_URL = "https://www.gigabyte.com/tw/Laptop/AORUS-MASTER-16-AM6H/sp"

chunks = [
    json.loads(line)
    for line in SOURCE.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

if len(chunks) != 51:
    raise ValueError(f"Expected 51 chunks, got {len(chunks)}")

index = []

for i, chunk in enumerate(chunks, start=1):
    if chunk["model_code"] not in {"BZH", "BYH", "BXH"}:
        raise ValueError("Unexpected product model")

    if chunk["source_url"] != OFFICIAL_URL:
        raise ValueError("Unapproved data source")

    payload = json.dumps({
        "model": MODEL,
        "input": chunk["text"]
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

    index.append({
        **chunk,
        "embedding": vector
    })

    print(f"[{i}/{len(chunks)}] Embedded {chunk['chunk_id']}", flush=True)

OUTPUT.write_text(
    json.dumps(index, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"\nSuccessfully indexed {len(index)} chunks")
print(f"Saved to: {OUTPUT}")


