
# Moderation Benchmark

## 1. Environment

- Device: MacBook Pro, Apple M2 Pro, 32GB unified memory
- Language: Python 3.11
- Dependency manager: uv
- Inference engine: llama.cpp
- Generation model: Qwen3-1.7B-Q4_K_M GGUF
- Embedding model: Qwen3-Embedding-0.6B-Q8_0 GGUF
- Supported product: GIGABYTE AORUS MASTER 16 AM6H

## 2. Moderation Architecture

The RAG pipeline uses four moderation stages:

1. Input Moderation
2. Retrieval Filtering
3. Generation Guard
4. Output Moderation

Each stage records its decision, category, reason,
latency, and request ID in a JSONL audit log.

## 3. Input Moderation Evaluation

### Regression Benchmark

Test set: 16 previously used development cases.

- Normal product queries: 5
- Competitor queries: 4
- Sensitive topics: 3
- Prompt injections: 2
- Out-of-scope queries: 2

| Metric | Result |
|---|---:|
| Decision and category accuracy | 16/16 (100%) |
| Refusal TPR | 9/9 (100%) |
| Normal false-block FPR | 0/5 (0%) |
| Out-of-scope redirect rate | 2/2 (100%) |
| Mean classification latency | 0.027 ms |
| Median classification latency | 0.030 ms |
| P95 classification latency | 0.051 ms |

Each question was warmed up once and measured 30 times,
for 480 timed classification calls.

These timings exclude audit logging, retrieval,
model inference, and process startup.

### Earlier Evaluation Results

| Evaluation | Result |
|---|---:|
| Initial 16-case baseline (decision only) | 12/16 |
| Edge test, v1 | 5/11 |
| Edge regression, v2 | 11/11 |
| New 12-case test, v2 | 6/12 |
| Regression, v3 | 9/12 |
| Regression, v4 | 12/12 |
| 17-case holdout, v4 | 11/17 |

The 17-case holdout was evaluated before subsequent fixes.
Results must not be interpreted as the current version's
independent generalization accuracy.

## 4. Failure Analysis

### Indirect Competitor Query

An indirect comparison involving another manufacturer's
gaming laptop initially bypassed Input Moderation.

The competitor intent detector returned False, causing
the product query to be allowed.

After extending indirect competitor detection,
the known end-to-end failure case was correctly refused
before retrieval and generation.

### Unsupported Qualitative Claims

The original Output Guard checked numerical facts but
failed to reject unsupported market-performance claims.

Comparative-claim rules were added.
An English regular-expression escaping error caused
two additional failures, which were subsequently fixed.

Output qualitative regression improved from 4/6 to 6/6.

These are regression results on known cases, not
independent estimates of generalization performance.

## 5. RAG Performance

| Metric | Result |
|---|---:|
| Mean end-to-end latency | 826.78 ms |
| Median end-to-end latency | 826.68 ms |
| Mean first-content latency, direct LLM API | 47.36 ms |
| Mean generation throughput, direct LLM API | 117.45 tokens/s |

The end-to-end benchmark used five measured runs after
one warm-up.

The direct LLM benchmark also used five measured runs
after one warm-up. First-content latency is a TTFT proxy.

The direct LLM benchmark and full RAG benchmark measure
different workloads and should not be directly compared.

## 6. Resource Constraints

The generation model used 29/29 Metal GPU layers.

The main reported Metal buffers were:

- Model: 1217.35 MiB
- KV cache: 224.00 MiB
- Compute: 54.01 MiB
- Sum: 1495.36 MiB

This sum is not a measurement of peak GPU memory usage.

The system was tested on Apple unified memory.
Deployment on a discrete 4GB VRAM GPU remains unverified.

## 7. Known Limitations

- Rule-based moderation can miss unseen paraphrases.
- Qualitative factual grounding is not fully verified.
- The output guard may incorrectly block valid statements.
- Streamed tokens are buffered until full output moderation
  finishes; user-visible token-by-token streaming is disabled.
- Input classification latency excludes audit logging.
- No directly comparable before/after moderation latency
  experiment has been completed yet.
- Discrete 4GB GPU deployment has not been verified.

## 8. Reproducibility

Relevant artifacts:

- eval_moderation.py
- scripts/benchmark_input_moderation.py
- docs/evaluation/input_moderation_benchmark_v1.json
- docs/evaluation/moderation_holdout_v4.json
- docs/evaluation/e2e_latency_v1.json
- docs/evaluation/llm_ttft_tps_v1.json
- docs/evaluation/metal_memory_budget_v1.md

Reproduce the current input moderation benchmark:

    uv run python scripts/benchmark_input_moderation.py

By default, the benchmark prints results without saving a JSON file.
Use `--save` to create a new timestamped JSON result without
overwriting previous records.

## 9. Follow-up Adversarial Regression

Additional Chinese, English, and mixed-context test cases
were used to investigate input moderation weaknesses.

| Test set | Before fixes | After fixes |
|---|---:|---:|
| Holdout regression (17 cases) | 13/17 (76.5%) | 17/17 (100%) |
| Adversarial regression (10 cases) | 6/10 (60.0%) | 10/10 (100%) |

### Failure Analysis and Fixes

- **Quoted instructions:** A legitimate keyboard-typing question
  containing a quoted instruction was initially refused.
  Quoted text handling was introduced to reduce false refusals.
- **Unsafe quoted-text bypass:** A subsequent adversarial test
  demonstrated that an execution request appended outside
  the quoted text could be incorrectly allowed. An additional
  execution-intent check was introduced.
- **Multilingual coverage:** English content-generation verbs
  and Chinese/English role-spoofing patterns were expanded
  to improve detection of safety and instruction-override requests.
- **English false refusal:** Keyboard questions using "typing"
  were initially misclassified and subsequently addressed.

### Interpretation

These test cases were used to diagnose and modify the rules.
Therefore, the post-fix scores are regression results, not
independent estimates of performance on unseen attacks.

The initial 6/10 adversarial result included one unsafe
ALLOW decision on an instruction-override request.
The corrected case subsequently returned REFUSE.

Rule-based input moderation remains vulnerable to unseen
paraphrases, context-dependent intent, and novel prompt
injection strategies. Further independent testing is required.
