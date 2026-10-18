
import re

FIELD_ALIASES = {
    "顯示晶片": [
        "顯示卡", "顯卡", "顯示晶片",
        "GPU", "graphics card", "graphics chip",
        "RTX"
    ],
    "顯示器": [
        "螢幕", "顯示器", "screen",
        "display", "OLED", "refresh rate"
    ],
    "中央處理器": [
        "處理器", "CPU", "processor"
    ],
    "記憶體": [
        "記憶體", "RAM", "memory", "DDR5"
    ],
    "儲存裝置": [
        "儲存空間", "硬碟", "SSD", "storage"
    ]
}


def detect_fields(query):
    matched = []

    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            pattern = re.escape(alias)

            if alias.isascii():
                pattern = rf"(?<!\w){pattern}(?!\w)"

            if re.search(pattern, query, re.IGNORECASE):
                matched.append(field)
                break

    return matched


if __name__ == "__main__":
    questions = [
        "BZH 的顯示卡是什麼？",
        "What GPU does BZH use?",
        "BZH 的螢幕幾 Hz？",
        "BZH 的顯示卡和螢幕規格？",
        "BZH 有什麼規格？"
    ]

    for question in questions:
        print(question, "->", detect_fields(question))

