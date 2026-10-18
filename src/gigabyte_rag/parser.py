
import json
from pathlib import Path
from bs4 import BeautifulSoup

SOURCE = Path("data/raw/aorus_master_16_am6h.html")
OUTPUT = Path("data/processed/aorus_master_16_am6h.json")

html = SOURCE.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

wrapper = soup.select_one(".multiple-spec-content-wrapper")
if wrapper is None:
    raise ValueError("Specification section not found")

keys = list(wrapper.select_one(".spec-column").stripped_strings)
slides = wrapper.select(
    ".content-column .swiper-wrapper > .swiper-slide"
)

products = []

for i, slide in enumerate(slides, start=1):
    values = [
        item.get_text(" ", strip=True)
        for item in slide.select(".spec-item-list")
    ]

    if len(keys) != len(values):
        raise ValueError(f"Slide {i}: Key-Value mismatch")

    gpu = dict(zip(keys, values))["顯示晶片"]

    if "5090" in gpu:
        model_code = "BZH"
    elif "5080" in gpu:
        model_code = "BYH"
    elif "5070 Ti" in gpu:
        model_code = "BXH"
    else:
        raise ValueError(f"Unknown GPU in slide {i}: {gpu}")

    products.append({
        "variant_id": f"slide_{i}",
        "model_code": model_code,
        "specifications": dict(zip(keys, values))
    })

result = {
    "product": "AORUS MASTER 16 AM6H",
    "source_url": "https://www.gigabyte.com/tw/Laptop/AORUS-MASTER-16-AM6H/sp",
    "variants": products
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"Parsed {len(products)} variants")
print(f"Each variant has {len(keys)} specifications")
print(f"Saved to {OUTPUT}")

