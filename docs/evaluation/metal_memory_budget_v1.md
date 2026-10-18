# Metal Memory Budget — Qwen3-1.7B

## Environment
- Device: Apple M2 Pro, 32GB unified memory
- Inference: llama.cpp with Metal
- Model: Qwen3-1.7B-Q4_K_M GGUF
- GPU layers: 29/29
- Context length: 2048
- Flash Attention: enabled

## Startup Log Measurements

| Buffer | Size |
|---|---:|
| MTL0_Mapped model buffer | 1217.35 MiB |
| MTL0 KV buffer | 224.00 MiB |
| MTL0 compute buffer | 54.01 MiB |
| Total of listed buffers | 1495.36 MiB |

CPU_Mapped model buffer: 166.92 MiB (reported separately).

## Interpretation
The three listed Metal buffers sum to approximately 1.46 GiB.

This is a buffer allocation estimate, NOT a measurement
of peak GPU memory usage.

The system was tested on Apple unified memory.
Deployment on a discrete 4GB VRAM GPU has NOT been verified.

## Source
llama.cpp generation-server startup logs, MacBook M2 Pro, context length 2048.
