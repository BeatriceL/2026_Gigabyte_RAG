
import re
import unicodedata

COMPETITOR_ALIASES = {
    "ASUS": [
        r"\basus\b",
        r"華碩",
        r"(?<![a-z])r[.\s]*o[.\s]*g\.?(?![a-z])",
    ],
    "MSI": [r"\bmsi\b", r"微星"],
    "Lenovo": [r"\blenovo\b", r"\blegion\b", r"聯想"],
    "Dell": [r"\bdell\b", r"\balienware\b"],
    "Acer": [r"\bacer\b", r"\bpredator\b", r"宏碁"],
    "Razer": [r"\brazer\b"],
}

INDIRECT_PATTERNS = [
    r"其他.{0,60}筆電.{0,24}(相比|比較|更好)",
    r"another manufacturer",
    r"other laptop brands",
    r"(rival|competing|competitor)\s+(laptop|notebook)",
    r"(別家|其他品牌|競品|對手)(電競)?筆電",
    r"(?:其他|別家|別的|不同)(?:品牌|廠商|牌子)(?:的)?(?:遊戲|電競)?筆電",
]

COMPARISON_PATTERNS = [
    r"比較|對比|更快|更便宜|哪台比較好",
    r"compare|versus|better than|faster than",
    r"cheaper than|\bvs\.?\b",
    r"和.{0,20}比|跟.{0,20}比",
]

SPEC_PATTERNS = [
    r"規格|價格|售價|效能|跑分",
    r"\bgpu\b|\bcpu\b|\bspecs\b",
    r"\bprice\b|\bperformance\b",
]

TARGET_PATTERN = r"aorus|gigabyte|\bbzh\b|\bbyh\b|\bbxh\b"

COMPATIBILITY_PATTERN = (
    r"能接|可以接|可接|相容|支援|外接|"
    r"connect|compatible|support"
)

PERIPHERAL_PATTERN = (
    r"螢幕|顯示器|鍵盤|滑鼠|"
    r"monitor|display|keyboard|mouse"
)


def normalize(text):
    return unicodedata.normalize("NFKC", text).casefold()


def matches(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def detect_competitor_query(question):
    q = normalize(question)

    indirect = matches(q, INDIRECT_PATTERNS)
    comparison = matches(q, COMPARISON_PATTERNS)
    specification = matches(q, SPEC_PATTERNS)

    brands = [
        brand
        for brand, aliases in COMPETITOR_ALIASES.items()
        if matches(q, aliases)
    ]

    target = bool(re.search(TARGET_PATTERN, q))

    # Indirect competitor laptop requests
    if indirect:
        return True

    if not brands:
        return False

    # Legitimate third-party peripheral compatibility
    compatibility = (
        target
        and re.search(COMPATIBILITY_PATTERN, q)
        and re.search(PERIPHERAL_PATTERN, q)
        and not comparison
    )

    if compatibility:
        return False

    # Competitor comparisons or specification requests
    if comparison:
        return True

    if specification and not target:
        return True

    return False


if __name__ == "__main__":
    cases = [
        ("Which laptop from another manufacturer is faster than BZH?", True),
        ("R.O.G. Strix laptop 的 GPU 規格？", True),
        ("這台 AORUS 和別家電競筆電比，誰的效能更好？", True),
        ("Compare ASUS ROG and GIGABYTE laptops", True),
        ("AORUS 可以接 ASUS 螢幕嗎？", False),
        ("Does AORUS support NVIDIA G-SYNC?", False),
    ]

    passed = 0

    for question, expected in cases:
        actual = detect_competitor_query(question)
        success = actual == expected
        passed += success

        print("PASS" if success else "FAIL", question)

    print(f"\nTOTAL: {passed}/{len(cases)} passed")

