import json
import time
import urllib.request

url = "http://127.0.0.1:8080/v1/chat/completions"

payload = {
    "messages": [
        {
            "role": "user",
            "content": "請用繁體中文，以三句話簡短比較 CPU 與 GPU 的主要差異，不要列點。/no_think"
        }
    ],
    "max_tokens": 256,
    "stream": True
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

start = time.perf_counter()
first_token_time = None

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
            if first_token_time is None:
                first_token_time = time.perf_counter()

            print(content, end="", flush=True)

end = time.perf_counter()

print("\n--- Performance ---")

if first_token_time is not None:
    ttft = (first_token_time - start) * 1000
    print(f"First Content Latency: {ttft:.2f} ms")
else:
    print("No content received")

print(f"Total Latency: {end - start:.2f} s")
