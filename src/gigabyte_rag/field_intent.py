
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
        "儲存裝置", "儲存空間", "硬碟", "SSD", "storage"
    ]
}



FIELD_ALIASES.update({
    "作業系統": ["作業系統", "Windows", "OS", "operating system"],
    "鍵盤種類": ["鍵盤", "鍵程", "keyboard", "key travel"],
    "連接埠": ["連接埠", "連接孔", "插孔", "ports", "port", "USB", "Type-C", "HDMI", "Thunderbolt", "RJ-45"],
    "音效": ["音效", "喇叭", "麥克風", "speaker", "audio", "microphone"],
    "通訊": ["通訊", "網路", "Wi-Fi", "WiFi", "藍牙", "Bluetooth", "wireless", "Ethernet"],
    "視訊鏡頭": ["視訊鏡頭", "鏡頭", "攝影機", "webcam", "camera"],
    "安全裝置": ["安全裝置", "安全晶片", "TPM", "PTT", "security chip"],
    "電池": ["電池", "續航", "battery"],
    "變壓器": ["變壓器", "充電器", "電源供應器", "AC adapter", "charger"],
    "尺寸": ["尺寸", "長寬高", "厚度", "dimensions", "thickness"],
    "重量": ["重量", "多重", "幾公斤", "weight", "weighs"],
    "顏色": ["顏色", "配色", "color", "colour"],
})

def detect_fields(query):
    matched = []

    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            pattern = re.escape(alias)

            if alias.isascii():
                pattern = rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])"

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

