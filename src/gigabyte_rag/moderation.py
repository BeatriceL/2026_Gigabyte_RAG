

import re
import unicodedata
from competitor_intent import detect_competitor_query
from safety_intent import detect_safety_intent

# Maintainable entity and intent lists
COMPETITOR_BRANDS = {
    "asus", "rog", "msi", "lenovo", "legion",
    "dell", "alienware", "acer", "predator", "razer"
}

COMPETITOR_REFERENCES = {
    "競品", "其他品牌筆電", "別牌筆電", "對手筆電",
    "competing laptop", "competing laptops",
    "rival notebook", "rival laptop",
    "competitor laptop", "other laptop brands"
}

COMPARISON_TERMS = {
    "比較", "對比", "更快", "更便宜", "哪台比較好",
    "compare", "versus", "vs", "better than",
    "faster than", "cheaper than"
}

SPEC_TERMS = {
    "規格", "價格", "售價", "效能", "跑分",
    "gpu", "cpu", "specs", "price", "performance"
}

TARGET_TERMS = {
    "aorus", "gigabyte", "bzh", "byh", "bxh"
}

HARDWARE_TERMS = TARGET_TERMS | {
    "gpu", "cpu", "ram", "ssd", "rtx",
    "螢幕", "顯示卡", "顯卡", "顯示晶片",
    "處理器", "記憶體", "電池", "筆電",
    "鍵盤", "thunderbolt", "usb", "hdmi", "wifi",
    "screen", "display", "keyboard", "laptop"
}

HARMFUL_CONTENT = {
    "仇恨", "歧視", "hate speech",
    "hateful", "discriminatory"
}

CONTENT_REQUEST = {
    "幫我寫", "寫一篇", "生成", "創作",
    "write", "generate", "create"
}

CONTROVERSY_TOPICS = {
    "政治爭議", "宗教爭議",
    "political controversy", "religious controversy"
}

DISCUSSION_INTENT = {
    "請討論", "討論", "辯論",
    "debate", "argue about"
}


def normalize(text):
    return unicodedata.normalize(
        "NFKC", text
    ).casefold().strip()


def contains_term(text, term):
    term = normalize(term)

    if re.search(r"[a-z]", term):
        pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
        return re.search(pattern, text) is not None

    return term in text


def has_any(text, terms):
    return any(contains_term(text, term) for term in terms)


def decision(category, action, reason):
    return {
        "category": category,
        "decision": action,
        "reason": reason
    }


def moderate_input(question):
    q = normalize(question)

    if not q:
        return decision(
            "OUT_OF_SCOPE", "REDIRECT", "Empty question"
        )

    # Treat quoted text as data in explicit keyboard-typing questions.
    # Instructions outside the quoted span remain subject to moderation.
    safety_q = q
    keyboard_question = re.search(
        r"(鍵盤|keyboard).{0,40}(輸入|打出|打字|type|typing|enter)", q
    )
    literal_text_question = re.search(
        r"(這串字|字串|文字|text|string|characters?)", q
    )

    # Inspect instructions outside quoted text before masking it.
    unquoted_q = re.sub(
        r'"[^"\n]{1,200}"|“[^”\n]{1,200}”|「[^」\n]{1,200}」',
        " ",
        q,
    )

    execute_request = re.search(
        r"照做|照著做|遵守|服從|執行|"
        r"\b(?:obey|execute)\b|"
        r"\bdo\s+(?:it|so)\b|"
        r"\bfollow\s+(?:them|it)\b",
        unquoted_q,
    )

    if keyboard_question and literal_text_question and not execute_request:
        safety_q = re.sub(
            r'"[^"\n]{1,200}"|“[^”\n]{1,200}”|「[^」\n]{1,200}」',
            " quoted_literal ",
            q,
        )

    # Safety intent classification before retrieval
    safety_category = detect_safety_intent(safety_q)

    if safety_category is not None:
        return decision(
            safety_category,
            "REFUSE",
            "Detected prohibited safety or policy override intent"
        )

    # 1. Detect policy override intent
    injection_patterns = [
        r"(ignore|disregard|override).{0,40}(instructions|rules|policy)",
        r"(reveal|show|print).{0,40}(system prompt|system instructions)",
        r"(忽略|無視|繞過|覆蓋).{0,30}(規則|指令|政策|審查|限制)"
    ]

    if any(re.search(p, safety_q) for p in injection_patterns):
        return decision(
            "PROMPT_INJECTION",
            "REFUSE",
            "Policy override or instruction disclosure request"
        )

    # 2. Detect harmful content generation intent
    harmful_request = (
        has_any(q, HARMFUL_CONTENT)
        and has_any(q, CONTENT_REQUEST)
    )

    controversy_request = (
        has_any(q, CONTROVERSY_TOPICS)
        and has_any(q, DISCUSSION_INTENT)
    )

    if harmful_request or controversy_request:
        return decision(
            "SENSITIVE_TOPIC",
            "REFUSE",
            "Disallowed sensitive content request"
        )

    # 3. Competitor detection
    if detect_competitor_query(question):
        return decision(
            "COMPETITOR_QUERY",
            "REFUSE",
            "Competitor information or comparison request"
        )

    # 4. Allow legitimate hardware questions
    if has_any(q, HARDWARE_TERMS):
        return decision(
            "PRODUCT_QUERY",
            "ALLOW",
            "Hardware request within supported scope"
        )

    # 5. Redirect unrelated questions
    return decision(
        "OUT_OF_SCOPE",
        "REDIRECT",
        "Question outside supported product scope"
    )

