
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCE = ROOT / "data/processed/aorus_master_16_am6h.json"
OUTPUT = ROOT / "data/processed/chunks.jsonl"

data = json.loads(SOURCE.read_text(encoding="utf-8"))

chunks = []

for variant in data["variants"]:
    model_code = variant["model_code"]

    for key, value in variant["specifications"].items():
        chunk = {
            "chunk_id": f"{model_code}_{len(chunks):03d}",
            "model_code": model_code,
            "category": key,
            "text": (
                f"產品：{data['product']}\n"
                f"型號：AORUS MASTER 16 {model_code}\n"
                f"規格欄位：{key}\n"
                f"規格內容：{value}"
            ),
            "source_url": data["source_url"]
        }

        chunks.append(chunk)

with OUTPUT.open("w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"Created {len(chunks)} chunks")
print(f"Saved to {OUTPUT}")

for chunk in chunks:
    if chunk["category"] == "顯示晶片":
        print(chunk["model_code"], chunk["text"][:120])

