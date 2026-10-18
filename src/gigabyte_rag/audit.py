
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_FILE = ROOT / "logs" / "moderation_audit.jsonl"


def new_request_id():
    return uuid.uuid4().hex


def write_audit(
    stage,
    category,
    decision,
    reason,
    request_id=None,
    latency_ms=None,
    evidence_ids=None,
):
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id or new_request_id(),
        "stage": stage,
        "category": category,
        "decision": decision,
        "reason": reason,
    }

    if latency_ms is not None:
        record["latency_ms"] = round(latency_ms, 3)

    if evidence_ids is not None:
        record["evidence_ids"] = evidence_ids

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


if __name__ == "__main__":
    result = write_audit(
        stage="SELF_TEST",
        category="PRODUCT_QUERY",
        decision="ALLOW",
        reason="Audit logging smoke test",
        latency_ms=0.25,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("Saved to:", AUDIT_FILE)

