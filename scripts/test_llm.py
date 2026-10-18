import json
import urllib.request

url = "http://127.0.0.1:8080/v1/chat/completions"

payload = {
    "messages": [
        {
            "role": "user",
            "content": "請用繁體中文簡短解釋什麼是 RAG。/no_think"
        }
    ],
    "max_tokens": 128,
    "stream": True
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("LLM 回答：")

with urllib.request.urlopen(request, timeout=120) as response:
    for line in response:
        line = line.decode("utf-8").strip()

        if not line.startswith("data: "):
            continue

        data = line[6:]

        if data == "[DONE]":
            break

        chunk = json.loads(data)
        content = chunk["choices"][0].get("delta", {}).get("content")

        if content:
            print(content, end="", flush=True)

print()
