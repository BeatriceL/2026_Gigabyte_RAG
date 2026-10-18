
# Experiment Log

## Environment
- Device: Apple MacBook Pro M2 Pro, 32GB Unified Memory
- Python: 3.11.6
- Package manager: uv 0.13.1
- Inference engine: llama.cpp 0.6.0, build 11429
- Generation model: Qwen3-1.7B Q4_K_M
- Embedding model: Qwen3-Embedding-0.6B Q8_0

## 1. Initial Inference Results
- First Content Latency: 101.03 ms, 93.33 ms
- Generation TPS: 116.35, 115.00 tokens/s
- Tests used different prompts and output lengths.
- Results are preliminary, not standardized benchmarks.

## 2. GPU Memory Analysis
- GPU: Apple M2 Pro (Metal)
- GPU offloading: 29/29 layers
- Metal model buffer: 1217.35 MiB
- Metal KV cache: 224 MiB
- Metal compute buffer: 54.01 MiB
- Sum of main Metal buffers: 1495.36 MiB
- Configuration: 2048 context, 1 slot
- Independent 4GB VRAM validation: NOT completed
- These figures do not represent total peak GPU usage.

## 3. Data Processing
- Source: GIGABYTE official AORUS MASTER 16 AM6H page
- curl requests returned HTTP 403.
- HTML was saved manually using Safari.
- Parsed 3 variants, 17 specification fields each.
- Created 51 structure-aware chunks.
- Model mappings: BZH/5090, BYH/5080, BXH/5070 Ti.

## 4. Retrieval Experiments

Query: AORUS MASTER 16 BZH 的顯示卡是什麼？

Expected category: 顯示晶片

| Method | Rank | Hit@1 | Hit@3 |
|---|---:|---:|---:|
| Semantic baseline | 11 | 0 | 0 |
| Query instruction | 2 | 0 | 1 |
| Field-aware reranking (+0.10) | 1 | 1 | 1 |

Results are from one query only.
The query instruction and field bonus were tested separately.

## 5. End-to-End RAG Test
- Query: AORUS MASTER 16 BZH 的顯示卡是什麼？
- Retrieved evidence: BZH_002
- Answer: NVIDIA GeForce RTX 5090 Laptop GPU, 24GB GDDR7, 175W
- Result: Correct against retrieved official specifications
- Streaming: Successful

## 6. Known Limitations
- Broad specification questions are not handled comprehensively.
- Retrieval evaluation dataset is not yet complete.
- Full moderation pipeline is not yet implemented.
- Output moderation cannot safely validate tokens already streamed.
- 4GB VRAM deployment has not been independently verified.

## 7. Next Steps
- Build moderation test cases and audit logs.
- Integrate all moderation stages.
- Benchmark retrieval quality and moderation accuracy.
- Measure full-pipeline latency and memory.
- Complete reproducibility documentation.

