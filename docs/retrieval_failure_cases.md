
# Retrieval Failure Analysis

## Case R001: GPU Specification Retrieval

### Test Configuration
- Product: AORUS MASTER 16 AM6H
- Generation Model: Qwen3-1.7B Q4_K_M
- Embedding Model: Qwen3-Embedding-0.6B Q8_0
- Retrieval: Cosine Similarity (Exact Search)
- Dataset: 51 structure-aware chunks
- Model filter: BZH
- Test type: Baseline

### Query
AORUS MASTER 16 BZH 的顯示卡是什麼？

### Expected
- Model: BZH
- Category: 顯示晶片
- GPU: NVIDIA GeForce RTX 5090 Laptop GPU

### Actual Results

| Rank | Category | Similarity |
|---|---|---|
| 1 | 顯示器 | 0.7709 |
| 2 | 顏色 | 0.7682 |
| 3 | 通訊 | 0.7229 |
| 11 | 顯示晶片 | 0.6962 |

### Metrics
- Hit@1: 0
- Hit@3: 0
- Reciprocal Rank: 0.0909

### Potential Causes
1. Semantic ambiguity between 顯示卡 and 顯示器.
2. Repeated product information across chunks.
3. Embedding query formatting may be suboptimal.
4. Semantic-only retrieval lacks field-aware matching.

### Improvement Plan
- Test Qwen3 query instructions.
- Implement field synonym normalization.
- Evaluate hybrid retrieval.
- Compare baseline and improved rankings.

### Status
Baseline failure recorded; improvements not yet tested.

