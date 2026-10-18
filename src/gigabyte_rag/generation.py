
import json
from collections import Counter
import re
import sys
import urllib.request

from field_intent import detect_fields
from hybrid_retrieval import retrieve_hybrid
from retrieval_filter import filter_evidence
from output_guard import moderate_output
from generation_guard import prepare_generation
import time
from audit import new_request_id, write_audit
from moderation import moderate_input

API = "http://127.0.0.1:8080/v1/chat/completions"
SOURCE = "https://www.gigabyte.com/tw/Laptop/AORUS-MASTER-16-AM6H/sp"


def answer(question):
    request_id = new_request_id()
    moderation_start = time.perf_counter()

    moderation = moderate_input(question)

    moderation_latency_ms = (
        time.perf_counter() - moderation_start
    ) * 1000

    write_audit(
        stage="INPUT",
        category=moderation["category"],
        decision=moderation["decision"],
        reason=moderation["reason"],
        request_id=request_id,
        latency_ms=moderation_latency_ms,
    )

    print(
        "Input Moderation:",
        moderation["decision"],
        moderation["category"]
    )

    if moderation["decision"] != "ALLOW":
        print("目前無法處理此問題，請詢問 AORUS MASTER 16 AM6H 的產品規格。")
        return
   
    # Identify the requested product variant
    models = set(re.findall(
        r"(?<![A-Z0-9])(BZH|BYH|BXH)(?![A-Z0-9])",
        question.upper()
    ))
    fields = set(detect_fields(question))

    if len(models) != 1 or not fields:
        print("目前測試版請指定單一型號及規格欄位。")
        return

    model = next(iter(models))

    # Retrieve candidate chunks
    candidates = retrieve_hybrid(question, top_k=51)

    # Filter all retrieved evidence before generation
    filter_start = time.perf_counter()
    evidence, rejected = filter_evidence(
        candidates, model, fields
    )
    filter_latency_ms = (
        time.perf_counter() - filter_start
    ) * 1000

    rejection_counts = dict(
        Counter(item["reason"] for item in rejected)
    )

    write_audit(
        stage="RETRIEVAL",
        category="EVIDENCE_FILTER",
        decision="ALLOW" if evidence else "REFUSE",
        reason=(
            f"approved={len(evidence)}, "
            f"rejected={len(rejected)}, "
            f"reasons={rejection_counts}"
        ),
        request_id=request_id,
        latency_ms=filter_latency_ms,
        evidence_ids=[
            item["chunk_id"] for item in evidence
        ],
    )

    print(
        f"Retrieval Filtering: "
        f"{len(evidence)} approved, "
        f"{len(rejected)} rejected"
    )

    if not evidence:
        print("根據目前核准的產品資料，無法確認答案。")
        return

    # Generation Guard: validate evidence before LLM call
    guard_start = time.perf_counter()

    guard = prepare_generation(
        question, model, fields, evidence
    )

    guard_latency_ms = (
        time.perf_counter() - guard_start
    ) * 1000

    write_audit(
        stage="GENERATION",
        category=guard["category"],
        decision=guard["decision"],
        reason=guard["reason"],
        request_id=request_id,
        latency_ms=guard_latency_ms,
        evidence_ids=[
            item["chunk_id"] for item in evidence
        ],
    )

    print(
        "Generation Guard:",
        guard["decision"],
        guard["reason"]
    )

    if guard["decision"] != "ALLOW":
        print("目前無足夠且安全的官方資料可生成回答。")
        return

    payload = {
        "messages": guard["messages"],
        "max_tokens": 256,
        "temperature": 0,
        "stream": True,
    }

    request = urllib.request.Request(
        API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    generated_parts = []

    with urllib.request.urlopen(request, timeout=120) as response:
        for line in response:
            line = line.decode("utf-8").strip()

            if not line.startswith("data: "):
                continue

            data = line[6:]

            if data == "[DONE]":
                break

            chunk = json.loads(data)
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content")

            if content:
                generated_parts.append(content)

    generated_answer = "".join(generated_parts)

    output_start = time.perf_counter()

    output_review = moderate_output(
        generated_answer, evidence
    )

    output_latency_ms = (
        time.perf_counter() - output_start
    ) * 1000

    write_audit(
        stage="OUTPUT",
        category=output_review["category"],
        decision=output_review["decision"],
        reason=output_review["reason"],
        request_id=request_id,
        latency_ms=output_latency_ms,
        evidence_ids=[
            item["chunk_id"] for item in evidence
        ],
    )

    print(
        "Output Moderation:",
        output_review["decision"],
        output_review["category"]
    )

    if output_review["decision"] != "ALLOW":
        print("回答未通過輸出審查，已停止顯示。")
        return

    print("\nLLM Answer:\n")
    print(generated_answer)

    print("\n\nRetrieved evidence:")
    for item in evidence:
        print(item["chunk_id"], item["category"])


if __name__ == "__main__":
    question = " ".join(sys.argv[1:])

    if not question:
        raise SystemExit("Please provide a question.")

    answer(question)

