
# GIGABYTE AI Lab — On-Premises RAG

An on-premises, moderation-aware Retrieval-Augmented Generation
(RAG) prototype for the official specifications of
GIGABYTE AORUS MASTER 16 AM6H.

Implemented in Python using `uv` and `llama.cpp`,
without LangChain or LlamaIndex.

## 1. Features

- Traditional Chinese, English, and mixed-language queries
- Product-specific structured chunking
- Qwen3 embedding with cosine-similarity retrieval
- Field-aware hybrid reranking
- Official-source and product-variant filtering
- Four-stage moderation with audit logging
- Local LLM inference using llama.cpp
- Reproducible evaluation artifacts

Supported product variants: BZH, BYH, BXH.

## 2. Architecture

User Query
    |
    v
Input Moderation
    |
    v
Embedding + Hybrid Retrieval
    |
    v
Retrieval Filtering
    |
    v
Generation Guard
    |
    v
llama.cpp Generation
    |
    v
Output Moderation
    |
    v
Approved Answer

Moderation decisions are recorded in JSONL audit logs with
a shared request ID, category, decision, reason, and latency.

Default mode buffers the full answer for output moderation.
Optional --stream mode reviews and displays completed segments.
The complete answer is reviewed again after generation.
Emitted text cannot be recalled; streaming is not token-by-token.

## 3. Tested Environment

- macOS on Apple M2 Pro
- 32GB unified memory
- Python 3.11
- uv 0.13.1
- llama.cpp build 11429, commit d81235049
- Generation: Qwen3-1.7B-Q4_K_M GGUF
- Embedding: Qwen3-Embedding-0.6B-Q8_0 GGUF

The reported performance results were measured in this
environment and may differ on other hardware.

## 4. Installation

Install the prerequisites on macOS:

```bash
brew install uv llama.cpp
```

From the project root, install Python dependencies:

```bash
uv sync
```

## 5. Download Models

Create the local model directory:

```bash
mkdir -p models
```

Download the generation model:

```bash
curl -fL --retry 3 \
  -o models/Qwen3-1.7B-Q4_K_M.gguf \
  "https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF/resolve/daeb8e2d528a760970442092f6bf1e55c3b659eb/Qwen3-1.7B-Q4_K_M.gguf"
```

Download the embedding model:

```bash
curl -fL --retry 3 \
  -o models/Qwen3-Embedding-0.6B-Q8_0.gguf \
  "https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf"
```

Verify both models:

```bash
shasum -a 256 models/*.gguf
```

Expected SHA-256:

Generation:
d2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5

Embedding:
06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439

Model files are excluded from Git.

## 6. Start the Inference Servers

Open separate terminals from the project root.

### Terminal 1 — Generation Server

```bash
llama-server \
  -m models/Qwen3-1.7B-Q4_K_M.gguf \
  -ngl 99 \
  -c 2048 \
  -np 1 \
  -lv 4 \
  --host 127.0.0.1 \
  --port 8080
```

### Terminal 2 — Embedding Server

```bash
llama-server \
  -m models/Qwen3-Embedding-0.6B-Q8_0.gguf \
  --embedding \
  --pooling last \
  -ngl 0 \
  -c 2048 \
  -np 1 \
  --cache-ram 0 \
  --host 127.0.0.1 \
  --port 8081
```

The embedding model runs on CPU to reduce GPU memory
requirements.

## 7. Official Data and Index

Official product specification source:

https://www.gigabyte.com/tw/Laptop/AORUS-MASTER-16-AM6H/sp

The original HTML snapshot is excluded from the repository.
During development, direct command-line retrieval returned
HTTP 403, so the page source was saved manually using Safari.

Preprocessed data and the generated vector index are included:

- `data/processed/aorus_master_16_am6h.json`
- `data/processed/chunks.jsonl`
- `data/processed/vector_index.json`

These artifacts allow retrieval evaluation without
repeating the original website extraction.

To rebuild the data, obtain the official HTML through
an authorized method and save it as:

`data/raw/aorus_master_16_am6h.html`

Then run:

```bash
uv run python src/gigabyte_rag/parser.py
uv run python src/gigabyte_rag/chunking.py
uv run python scripts/build_index.py
```

The embedding server on port 8081 must be running
before building the index.

The resulting index contains 51 structured chunks,
with 1024-dimensional embedding vectors.

## 8. Run the RAG Pipeline

With both servers running:

```bash
uv run python src/gigabyte_rag/generation.py \
  "AORUS MASTER 16 BZH 的顯示卡是什麼？"
```

Another example:

```bash
uv run python src/gigabyte_rag/generation.py \
  "What GPU does the BYH model use?"
```

The current CLI prototype requires exactly one supported
variant code and at least one recognized specification
field to proceed with retrieval and generation.

Questions outside the supported scope may be refused
or redirected according to the moderation policy.

## 9. Moderation and Security

The implementation uses four defenses:

1. Input Moderation — classifies user intent and
   handles competitor, sensitive, injection, and
   out-of-scope requests.

2. Retrieval Filtering — enforces the approved source,
   model variant, specification fields, and basic
   content-safety checks.

3. Generation Guard — revalidates approved evidence
   and constructs a constrained generation prompt.

4. Output Moderation — checks generated content
   before displaying it.

Audit records are written to:

`logs/moderation_audit.jsonl`

Runtime logs are excluded from Git.

See `moderation_policy.md` for policy definitions.

These are lightweight, rule-based safeguards and do not
provide a formal guarantee against all prompt injections,
hallucinations, or adversarial paraphrases.

## 10. Evaluation

Input moderation test cases:

```bash
uv run python tests/check_moderation_edges.py
uv run python tests/check_moderation_unseen.py
uv run python tests/check_moderation_holdout.py
```

Additional module self-tests:

```bash
uv run python src/gigabyte_rag/competitor_intent.py
uv run python src/gigabyte_rag/safety_intent.py
uv run python src/gigabyte_rag/retrieval_filter.py
uv run python src/gigabyte_rag/generation_guard.py
uv run python src/gigabyte_rag/output_guard.py
```

Run the input moderation benchmark without saving results:

    uv run python scripts/benchmark_input_moderation.py

To save a new timestamped JSON result:

    uv run python scripts/benchmark_input_moderation.py --save

Existing evaluation records are never overwritten.

Full results, historical failures, latency measurements,
and methodological limitations are documented in:

- `benchmark_moderation.md`
- `docs/experiment_log.md`
- `docs/retrieval_failure_cases.md`
- `docs/evaluation/`

Regression tests that informed development are
distinguished from previously unseen evaluation cases.

## 11. Selected Performance Results

MacBook M2 Pro, 32GB unified memory:

| Metric | Result |
|---|---:|
| Mean RAG end-to-end latency | 826.78 ms |
| Mean direct LLM first-content latency | 47.36 ms |
| Mean direct LLM throughput | 117.45 tokens/s |
| Input moderation regression accuracy | 16/16 |
| Input moderation classification mean | 0.027 ms |

End-to-end RAG and direct LLM API benchmarks represent
different workloads.

First-content latency is a client-side TTFT proxy.
The reported throughput comes from llama.cpp timings.

The 16-case moderation score is a development/regression
result, not an independent generalization estimate.

## 12. 4GB VRAM Considerations

On Apple Metal, the main reported generation buffers were:

| Buffer | Size |
|---|---:|
| Model | 1217.35 MiB |
| KV cache | 224.00 MiB |
| Compute | 54.01 MiB |
| Sum | 1495.36 MiB |

The sum is not a peak GPU memory measurement.

The system was tested on Apple unified memory.
Deployment on a discrete 4GB VRAM GPU has not been
verified.

Tesla T4 CUDA test: 1,453 MiB observed across 163 samples.
Not a guaranteed peak or full 4GB GPU RAG validation.
See benchmark_moderation.md Section 13.

## 13. Known Limitations

- Unseen competitor paraphrases may bypass rules.
- Normal hardware questions may be falsely refused.
- Qualitative factual grounding remains incomplete.
- Optional --stream emits reviewed segments, not individual tokens.
- Emitted text cannot be recalled if later moderation rejects.
- The current retrieval and generation interface is
  restricted to supported model codes and recognized fields.
- Moderation evaluation contains small test sets.
- Independent 4GB VRAM deployment remains unverified.

## 14. Repository Structure

- `src/gigabyte_rag/`: RAG and moderation implementation
- `scripts/`: indexing and benchmarking utilities
- `tests/`: moderation tests
- `data/processed/`: structured product data and index
- `docs/evaluation/`: recorded experimental evidence
- `moderation_policy.md`: policy and decisions
- `benchmark_moderation.md`: measurements and analysis
- `pyproject.toml`, `uv.lock`: reproducible dependencies


## 15. Additional Evaluations

    uv run python tests/check_moderation_adversarial.py
    uv run python scripts/eval_retrieval.py
    uv run python scripts/benchmark_guard_overhead.py

The latter two require the embedding server on port 8081.
See benchmark_moderation.md for results and limitations.

## 16. Streaming CLI Example

    uv run python src/gigabyte_rag/generation.py --stream "What GPU does the AORUS MASTER 16 BYH use?"

## 17. Model Selection and Quantization

- Generation: Qwen3-1.7B Q4_K_M was selected for compact multilingual local inference and reduced model memory.
- Embedding: Qwen3-Embedding-0.6B Q8_0 uses higher precision for retrieval; the embedding server runs on CPU to conserve GPU VRAM.
- Trade-offs: quantization reduces memory requirements but may affect quality. No quantization ablation was performed, and full RAG deployment on a discrete 4GB GPU remains unverified.
