
import sys

from retrieval import retrieve
from field_intent import detect_fields


def retrieve_hybrid(query, top_k=3, field_bonus=0.10):
    # Step 1: Get semantic retrieval candidates
    candidates = retrieve(query, top_k=51)

    # Step 2: Detect specification field intent
    matched_fields = set(detect_fields(query))

    # Step 3: Field-aware reranking
    results = []

    for chunk in candidates:
        semantic_score = chunk["score"]

        bonus = (
            field_bonus
            if chunk["category"] in matched_fields
            else 0.0
        )

        results.append({
            **chunk,
            "semantic_score": semantic_score,
            "hybrid_score": semantic_score + bonus
        })

    # Step 4: Sort by hybrid score
    results.sort(
        key=lambda x: x["hybrid_score"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])

    if not query:
        raise SystemExit("Please provide a question.")

    print("Question:", query)

    results = retrieve_hybrid(query)

    for rank, item in enumerate(results, 1):
        print(f"\nRank {rank}")
        print("Model:", item["model_code"])
        print("Category:", item["category"])
        print("Semantic Score:", round(item["semantic_score"], 4))
        print("Hybrid Score:", round(item["hybrid_score"], 4))
        print("Content:", item["text"][:180])

